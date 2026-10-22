"""Livraison après paiement : création du compte client dans cortex.db (table `abonnements`).

Le scénario Make (tarifs/scenario-livraison.md) envoie un email signé « [CORTEX-COMPTE] <ref> » à
contact@josyei.com après un paiement vérifié chez Stripe ou PayPlug. Le Cortex le lit dans la boîte (IMAP) et appelle
`traiter_email()`. Rien n'est créé si la signature est fausse, et un même paiement ne crée jamais deux comptes.

Inactif tant que LIVRAISON_SECRET est absente : aucun email n'est alors interprété (le Cortex le dit sur Telegram
dès qu'un email [CORTEX-COMPTE] arrive). Ce module N'ENVOIE AUCUN EMAIL : l'email de bienvenue et la notification
Telegram sont faits par Make. Aucun secret ni code d'accès n'est écrit dans le journal.
"""

import hashlib
import hmac
from datetime import datetime, timezone

MARQUE = "[CORTEX-COMPTE]"
FORMULES = {"gratuit", "decouverte", "starter", "pro"}
SCHEMA = """CREATE TABLE IF NOT EXISTS abonnements (
  client_id TEXT PRIMARY KEY, source TEXT, ref TEXT UNIQUE, email TEXT, entreprise TEXT, formule TEXT,
  essai_fin TEXT, test INTEGER, statut TEXT DEFAULT 'actif', cree_le TEXT)"""


def _hmac(secret, texte):
    return hmac.new(secret.encode(), texte.encode(), hashlib.sha256).hexdigest()


def client_id(ref):
    """Identique au scénario Make : CX- + 8 premiers caractères de sha256(ref), en majuscules."""
    return "CX-" + hashlib.sha256(ref.encode()).hexdigest()[:8].upper()


def code_acces(ref, secret):
    """Identique au scénario Make : 10 premiers caractères de HMAC-SHA256(ref), en majuscules."""
    return _hmac(secret, ref)[:10].upper()


def _champs(corps):
    out = {}
    for ligne in corps.splitlines():
        if "=" in ligne:
            k, v = ligne.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def signature_valide(champs, secret):
    a_signer = "|".join(champs.get(k, "") for k in ("source", "ref", "email", "formule", "essai_fin"))
    return hmac.compare_digest(_hmac(secret, a_signer), champs.get("sig", ""))


def traiter_email(con, sujet, corps, secret, store=None):
    """Renvoie None si ce n'est pas un transfert de paiement. Sinon un dict {statut, client_id}.
    statut : cree | deja_traite | signature_invalide | invalide | inactif."""
    if not (sujet or "").strip().startswith(MARQUE):
        return None
    if not secret:
        return {"statut": "inactif", "motif": "LIVRAISON_SECRET absente"}
    champs = _champs(corps)
    if not signature_valide(champs, secret):
        if store:
            store.log("JUDICIAIRE", "paiement_signature_invalide")
        return {"statut": "signature_invalide"}
    if champs.get("formule") not in FORMULES or not champs.get("ref") or "@" not in champs.get("email", ""):
        return {"statut": "invalide"}
    con.execute(SCHEMA)
    cid = client_id(champs["ref"])
    if con.execute("SELECT 1 FROM abonnements WHERE ref=?", (champs["ref"],)).fetchone():
        return {"statut": "deja_traite", "client_id": cid}
    con.execute("INSERT INTO abonnements(client_id, source, ref, email, entreprise, formule, essai_fin, test, cree_le) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (cid, champs.get("source", ""), champs["ref"], champs["email"].lower(), champs.get("entreprise", ""),
                 champs["formule"], champs.get("essai_fin", ""), int(champs.get("test", "0") == "1"),
                 datetime.now(timezone.utc).isoformat(timespec="seconds")))
    con.commit()
    if store:  # journal chaîné : identifiant et formule seulement, ni email ni code
        store.log("EXECUTIF", "abonnement_cree", details={"client_id": cid, "formule": champs["formule"],
                                                           "test": champs.get("test") == "1"})
    return {"statut": "cree", "client_id": cid}
