"""Récupération d'accès SANS email (22/10/2026) : l'administrateur (JOSY) valide chaque demande.

Parcours :
  1. le client clique « Mot de passe oublié » et donne son email → une demande est enregistrée
     (réponse identique que le compte existe ou non : on ne révèle pas quels comptes existent) ;
  2. JOSY la voit dans Mon Agent › « Demandes d'accès en attente », vérifie l'identité avec les
     informations de l'entreprise, clique « Générer un code » : un code à 6 chiffres s'affiche UNE fois ;
  3. JOSY le donne au client (téléphone, SMS) ; le client saisit email + code + nouveau mot de passe.

Garde-fous : code tiré par `secrets`, seul son hachage bcrypt est en base, usage unique, valable
30 minutes, 5 essais au plus puis annulé, 3 demandes par compte et par jour, tout est journalisé
(sans l'adresse ni le code). Le compte fondateur ne passe pas par ici : depuis le PC,
`python acces.py --reinitialiser <email>` (accès physique = administrateur).
"""

import secrets
import sys
import threading
import time

import bcrypt

SCHEMA = """CREATE TABLE IF NOT EXISTS demandes_acces (
  id INTEGER PRIMARY KEY AUTOINCREMENT, utilisateur_id INTEGER, cree_le REAL, statut TEXT DEFAULT 'en_attente',
  code_hash TEXT, code_emis_le REAL, code_expire REAL, essais INTEGER DEFAULT 0, ip TEXT, traite_le REAL)"""
CODE_DUREE_S = 30 * 60
ESSAIS_MAX = 5
DEMANDES_JOUR_MAX = 3
MESSAGE_NEUTRE = ("Votre demande a été enregistrée. Un administrateur va valider votre accès. "
                  "Votre code vous sera communiqué.")


def preparer(store):
    store.db.execute(SCHEMA)
    store.db.execute("CREATE TABLE IF NOT EXISTS comptes_entreprise (utilisateur_id INTEGER)")
    if "telephone" not in {r[1] for r in store.db.execute("PRAGMA table_info(comptes_entreprise)")}:
        # téléphone de l'entreprise : sert à JOSY pour vérifier l'identité et donner le code
        store.db.execute("ALTER TABLE comptes_entreprise ADD COLUMN telephone TEXT")
    store.db.commit()


def _expirer(store):
    """Codes périmés ou demandes de plus de 7 jours : clôturés (jamais réutilisables)."""
    t = time.time()
    store.db.execute("UPDATE demandes_acces SET statut='expiree', code_hash=NULL, traite_le=? "
                     "WHERE statut='code_emis' AND code_expire < ?", (t, t))
    store.db.execute("UPDATE demandes_acces SET statut='expiree', traite_le=? "
                     "WHERE statut='en_attente' AND cree_le < ?", (t, t - 7 * 86400))
    store.db.commit()


def demander(store, email, ip=None, notifier=None):
    """Enregistre une demande d'accès. Renvoie toujours MESSAGE_NEUTRE."""
    preparer(store)
    email = (email or "").strip().lower()[:200]
    row = store.db.execute("SELECT id, role FROM utilisateurs WHERE email=?", (email,)).fetchone()
    if not row or row["role"] == "fondateur":
        store.log("JUDICIAIRE", "demande_acces_ignoree",
                  details={"raison": "fondateur" if row else "compte_inconnu"})
        return MESSAGE_NEUTRE
    uid = row["id"]
    n = store.db.execute("SELECT COUNT(*) FROM demandes_acces WHERE utilisateur_id=? AND cree_le > ?",
                         (uid, time.time() - 86400)).fetchone()[0]
    if n >= DEMANDES_JOUR_MAX:
        store.log("JUDICIAIRE", "demande_acces_limitee", details={"utilisateur_id": uid})
        return MESSAGE_NEUTRE
    # une seule demande ouverte par compte : la nouvelle remplace l'ancienne (et annule un code émis)
    store.db.execute("UPDATE demandes_acces SET statut='remplacee', code_hash=NULL, traite_le=? "
                     "WHERE utilisateur_id=? AND statut IN ('en_attente','code_emis')", (time.time(), uid))
    store.db.execute("INSERT INTO demandes_acces(utilisateur_id, cree_le, ip) VALUES(?,?,?)",
                     (uid, time.time(), (ip or "")[:45]))
    store.db.commit()
    store.log("HUMAIN", "demande_acces_recue", details={"utilisateur_id": uid})
    if notifier:
        nom = store.db.execute("SELECT nom FROM comptes_entreprise WHERE utilisateur_id=?", (uid,)).fetchone()
        threading.Thread(target=notifier, args=(f"🔑 Demande d'accès : {nom[0] if nom else 'un client'} a oublié son "
                                                "mot de passe. Vérifiez son identité puis générez le code dans "
                                                "Mon Agent › Demandes d'accès en attente.",), daemon=True).start()
    return MESSAGE_NEUTRE


def en_attente(store):
    """Demandes ouvertes, avec ce qu'il faut pour vérifier l'identité (registre + profil)."""
    preparer(store)
    _expirer(store)
    return store.db.execute(
        "SELECT d.id, d.cree_le, d.statut, d.code_expire, d.essais, u.email, u.cree_le AS inscrit_le, "
        "u.derniere_connexion, c.nom, c.siren, c.commune, c.secteur, c.adresse, c.site_web, c.telephone "
        "FROM demandes_acces d JOIN utilisateurs u ON u.id=d.utilisateur_id "
        "LEFT JOIN comptes_entreprise c ON c.utilisateur_id=d.utilisateur_id "
        "WHERE d.statut IN ('en_attente','code_emis') ORDER BY d.id DESC").fetchall()


def generer_code(store, did):
    """Émet le code à 6 chiffres d'une demande. Renvoie le code EN CLAIR (affiché une seule fois) ou None."""
    preparer(store)
    _expirer(store)
    row = store.db.execute("SELECT utilisateur_id, statut FROM demandes_acces WHERE id=?", (did,)).fetchone()
    if not row or row["statut"] not in ("en_attente", "code_emis"):
        return None
    code = f"{secrets.randbelow(10**6):06d}"
    t = time.time()
    store.db.execute("UPDATE demandes_acces SET statut='code_emis', code_hash=?, code_emis_le=?, code_expire=?, "
                     "essais=0 WHERE id=?", (bcrypt.hashpw(code.encode(), bcrypt.gensalt(rounds=10)).decode(),
                                            t, t + CODE_DUREE_S, did))
    store.db.commit()
    store.log("HUMAIN", "code_acces_emis", details={"demande": did, "utilisateur_id": row["utilisateur_id"],
                                                     "valable_min": CODE_DUREE_S // 60})
    return code


def refuser(store, did):
    preparer(store)
    store.db.execute("UPDATE demandes_acces SET statut='refusee', code_hash=NULL, traite_le=? WHERE id=? "
                     "AND statut IN ('en_attente','code_emis')", (time.time(), did))
    store.db.commit()
    store.log("HUMAIN", "demande_acces_refusee", details={"demande": did})


def utiliser_code(store, c, email, code, nouveau, confirmation, hacher, mdp_min):
    """Le client saisit son code. Renvoie (réussi, message). Message d'échec identique dans tous les cas."""
    preparer(store)
    _expirer(store)
    echec = "Code invalide ou expiré. Vérifiez-le, ou refaites une demande d'accès."
    if len(nouveau or "") < mdp_min:
        return False, f"Le nouveau mot de passe doit faire au moins {mdp_min} caractères."
    if nouveau != confirmation:
        return False, "Les deux mots de passe ne sont pas identiques."
    code = "".join(ch for ch in (code or "") if ch.isdigit())
    row = store.db.execute(
        "SELECT d.id, d.code_hash, d.essais, u.id AS uid FROM demandes_acces d JOIN utilisateurs u ON u.id=d.utilisateur_id "
        "WHERE u.email=? AND u.role<>'fondateur' AND d.statut='code_emis' ORDER BY d.id DESC LIMIT 1",
        ((email or "").strip().lower(),)).fetchone()
    if not row or len(code) != 6:
        store.log("JUDICIAIRE", "code_acces_refuse", details={"raison": "pas_de_code" if not row else "format"})
        return False, echec
    if not bcrypt.checkpw(code.encode(), row["code_hash"].encode()):
        essais = row["essais"] + 1
        statut = "bloquee" if essais >= ESSAIS_MAX else "code_emis"
        store.db.execute("UPDATE demandes_acces SET essais=?, statut=?, code_hash=CASE WHEN ?='bloquee' THEN NULL "
                         "ELSE code_hash END WHERE id=?", (essais, statut, statut, row["id"]))
        store.db.commit()
        store.log("JUDICIAIRE", "code_acces_refuse", details={"demande": row["id"], "essais": essais,
                                                               "bloquee": statut == "bloquee"})
        return False, echec
    store.db.execute("UPDATE utilisateurs SET mot_de_passe=?, maj_le=?, doit_changer=0, mdp_temp=NULL, "
                     "mdp_temp_expire=NULL WHERE id=?", (hacher(nouveau), c.iso(c.now()), row["uid"]))
    store.db.execute("UPDATE demandes_acces SET statut='utilisee', code_hash=NULL, traite_le=? WHERE id=?",
                     (time.time(), row["id"]))
    store.db.commit()
    store.log("HUMAIN", "acces_retabli", details={"demande": row["id"], "utilisateur_id": row["uid"]})
    return True, "Mot de passe changé. Vous pouvez vous connecter."


if __name__ == "__main__":  # secours du fondateur, sur le PC uniquement
    import getpass
    import cortex as C
    import connexion
    if len(sys.argv) != 3 or sys.argv[1] != "--reinitialiser":
        sys.exit("Usage : python acces.py --reinitialiser <email>")
    store = C.Store(C.DB_PATH)
    connexion.preparer(store)
    email = sys.argv[2].strip().lower()
    if not store.db.execute("SELECT 1 FROM utilisateurs WHERE email=?", (email,)).fetchone():
        sys.exit("Aucun compte avec cette adresse.")
    mdp = getpass.getpass("Nouveau mot de passe (12 caractères au moins) : ")
    if len(mdp) < connexion.MDP_MIN or mdp != getpass.getpass("Confirmez : "):
        sys.exit("Trop court ou différent : rien n'a changé.")
    store.db.execute("UPDATE utilisateurs SET mot_de_passe=?, maj_le=?, doit_changer=0 WHERE email=?",
                     (connexion.hacher(mdp), C.iso(C.now()), email))
    store.db.commit()
    store.log("HUMAIN", "mot_de_passe_reinitialise_local", details={"source": "console du PC"})
    print("Mot de passe changé.")
