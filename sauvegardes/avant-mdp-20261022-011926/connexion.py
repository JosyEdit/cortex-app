"""Connexion à l'interface locale : comptes (table utilisateurs, bcrypt) et sessions.

Deux verrous se cumulent : le laissez-passer dans l'adresse (?t=…, inchangé) et une session
ouverte par email + mot de passe. Sessions en mémoire (un redémarrage de l'interface déconnecte),
cookie HttpOnly + SameSite=Strict (+ Secure derrière HTTPS / Tailscale), 12 h au plus.
Tentatives limitées : 5 échecs en 15 minutes bloquent la connexion 15 minutes.
"""

import secrets
import threading
import time

import bcrypt

SCHEMA = """CREATE TABLE IF NOT EXISTS utilisateurs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, mot_de_passe TEXT NOT NULL,
  role TEXT NOT NULL, cree_le TEXT, maj_le TEXT)"""
COOKIE = "cortex_session"
DUREE_S = 12 * 3600
ECHECS_MAX, FENETRE_S = 5, 15 * 60
MDP_MIN = 12

_sessions = {}   # jeton -> (email, role, expire_a)
_echecs = []     # horodatages des échecs récents
_verrou = threading.Lock()


def preparer(store):
    store.db.execute(SCHEMA)
    store.db.commit()


def hacher(mdp):
    return bcrypt.hashpw(mdp.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")


def creer_compte(store, c, email, role, mdp=None):
    """Crée un compte s'il n'existe pas. Renvoie le mot de passe généré (None si le compte existait)."""
    preparer(store)
    email = email.strip().lower()
    if store.db.execute("SELECT 1 FROM utilisateurs WHERE email=?", (email,)).fetchone():
        return None
    mdp = mdp or secrets.token_urlsafe(15)
    store.db.execute("INSERT INTO utilisateurs(email, mot_de_passe, role, cree_le) VALUES(?,?,?,?)",
                     (email, hacher(mdp), role, c.iso(c.now())))
    store.db.commit()
    store.log("HUMAIN", "compte_cree", details={"role": role})  # sans l'adresse (I4)
    return mdp


def bloque():
    with _verrou:
        maintenant = time.time()
        _echecs[:] = [t for t in _echecs if maintenant - t < FENETRE_S]
        return len(_echecs) >= ECHECS_MAX


def connecter(store, email, mdp):
    """Renvoie (jeton de session, rôle) ou (None, raison)."""
    if bloque():
        return None, "Trop d'essais : connexion bloquée 15 minutes."
    preparer(store)
    row = store.db.execute("SELECT * FROM utilisateurs WHERE email=?",
                           ((email or "").strip().lower(),)).fetchone()
    ok = bool(row) and bcrypt.checkpw((mdp or "").encode("utf-8"), row["mot_de_passe"].encode("ascii"))
    if not ok:
        with _verrou:
            _echecs.append(time.time())
        store.log("JUDICIAIRE", "connexion_refusee", details={"echecs_recents": len(_echecs)})
        return None, "Email ou mot de passe incorrect."
    jeton = secrets.token_urlsafe(32)
    with _verrou:
        _sessions[jeton] = (row["email"], row["role"], time.time() + DUREE_S)
    store.log("HUMAIN", "connexion", details={"role": row["role"]})
    return jeton, row["role"]


def session(jeton):
    """(email, rôle) de la session, ou None si absente ou expirée."""
    with _verrou:
        s = _sessions.get(jeton or "")
        if not s:
            return None
        if s[2] < time.time():
            _sessions.pop(jeton, None)
            return None
        return s[0], s[1]


def deconnecter(jeton):
    with _verrou:
        _sessions.pop(jeton or "", None)


def changer_mdp(store, c, email, ancien, nouveau):
    """Renvoie (réussi, message)."""
    if len(nouveau or "") < MDP_MIN:
        return False, f"Le nouveau mot de passe doit faire au moins {MDP_MIN} caractères."
    row = store.db.execute("SELECT * FROM utilisateurs WHERE email=?", (email,)).fetchone()
    if not row or not bcrypt.checkpw((ancien or "").encode("utf-8"), row["mot_de_passe"].encode("ascii")):
        return False, "Mot de passe actuel incorrect."
    store.db.execute("UPDATE utilisateurs SET mot_de_passe=?, maj_le=? WHERE email=?",
                     (hacher(nouveau), c.iso(c.now()), email))
    store.db.commit()
    store.log("HUMAIN", "mot_de_passe_change", details={"role": row["role"]})
    return True, "Mot de passe changé."
