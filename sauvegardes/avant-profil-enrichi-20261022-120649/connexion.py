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
    colonnes = {r[1] for r in store.db.execute("PRAGMA table_info(utilisateurs)")}
    for nom, type_ in (("mdp_temp", "TEXT"), ("mdp_temp_expire", "REAL"), ("doit_changer", "INTEGER DEFAULT 0")):
        if nom not in colonnes:  # mot de passe oublié (22/10/2026)
            store.db.execute(f"ALTER TABLE utilisateurs ADD COLUMN {nom} {type_}")
    store.db.commit()


# --- Mot de passe oublié ---------------------------------------------------------------
# Le mot de passe temporaire s'AJOUTE à l'actuel pendant 30 minutes (il ne le remplace pas) :
# quelqu'un qui demanderait une réinitialisation à ta place ne peut pas te bloquer dehors.
TEMP_DUREE_S = 30 * 60
RESET_INTERVALLE_S = 10 * 60
_derniere_demande = [0.0]


def demander_reinitialisation(store, c, email, envoyer):
    """Si l'email est un compte fondateur : mot de passe temporaire envoyé par `envoyer(dest, mdp)`.
    Renvoie toujours le même message (ne révèle pas quels comptes existent)."""
    neutre = ("Si cette adresse correspond au compte fondateur, un mot de passe temporaire vient d'y "
              "être envoyé (valable 30 minutes).")
    preparer(store)
    email = (email or "").strip().lower()
    row = store.db.execute("SELECT * FROM utilisateurs WHERE email=? AND role='fondateur'", (email,)).fetchone()
    if not row:
        store.log("JUDICIAIRE", "reinitialisation_refusee", details={"raison": "compte_inconnu"})
        return neutre
    with _verrou:
        if time.time() - _derniere_demande[0] < RESET_INTERVALLE_S:
            return "Une demande vient d'être faite : regarde ta boîte Gmail (et les spams), ou réessaie dans 10 minutes."
        _derniere_demande[0] = time.time()
    temp = secrets.token_urlsafe(9)
    store.db.execute("UPDATE utilisateurs SET mdp_temp=?, mdp_temp_expire=? WHERE email=?",
                     (hacher(temp), time.time() + TEMP_DUREE_S, email))
    store.db.commit()
    try:
        envoyer(email, temp)
    except Exception as exc:
        store.db.execute("UPDATE utilisateurs SET mdp_temp=NULL, mdp_temp_expire=NULL WHERE email=?", (email,))
        store.db.commit()
        store.log("EXECUTIF", "reinitialisation_echec_envoi", details={"erreur": type(exc).__name__})
        return "L'email n'a pas pu partir (serveur d'envoi injoignable). Rien n'a changé : réessaie plus tard."
    store.log("EXECUTIF", "reinitialisation_envoyee", details={"role": "fondateur"})  # sans l'adresse (I4)
    return neutre


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
    temporaire = False
    if row and not ok and row["mdp_temp"] and (row["mdp_temp_expire"] or 0) > time.time():
        temporaire = ok = bcrypt.checkpw((mdp or "").encode("utf-8"), row["mdp_temp"].encode("ascii"))
    if temporaire:  # usage unique : il faudra choisir un nouveau mot de passe
        store.db.execute("UPDATE utilisateurs SET mdp_temp=NULL, mdp_temp_expire=NULL, doit_changer=1 "
                         "WHERE email=?", (row["email"],))
        store.db.commit()
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


def doit_changer(store, email):
    preparer(store)
    row = store.db.execute("SELECT doit_changer FROM utilisateurs WHERE email=?", (email,)).fetchone()
    return bool(row and row[0])


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
    if not row:
        return False, "Compte introuvable."
    # Après une connexion par mot de passe temporaire (doit_changer), l'ancien n'est pas redemandé.
    if not row["doit_changer"] and not bcrypt.checkpw((ancien or "").encode("utf-8"),
                                                      row["mot_de_passe"].encode("ascii")):
        return False, "Mot de passe actuel incorrect."
    store.db.execute("UPDATE utilisateurs SET mot_de_passe=?, maj_le=?, doit_changer=0, mdp_temp=NULL, "
                     "mdp_temp_expire=NULL WHERE email=?", (hacher(nouveau), c.iso(c.now()), email))
    store.db.commit()
    store.log("HUMAIN", "mot_de_passe_change", details={"role": row["role"]})
    return True, "Mot de passe changé."
