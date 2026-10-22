"""Rôles et identités : savoir qui parle au Cortex (identites.json, décision de JOSY du 21/10/2026).

  - fondateur        : JOSY (adresse Gmail personnelle) ;
  - admin_entreprise : contact@josyei.com, la boîte publique de JOSY EI ;
  - exterieur        : toute autre adresse (prospect si on lui a écrit, sinon inconnu).

Sécurité : l'adresse « From » d'un email se falsifie en une ligne. Un email n'est donc traité comme
venant du fondateur que si le serveur de réception a validé son authentification (DMARC, ou DKIM du
domaine de l'expéditeur) dans l'en-tête Authentication-Results. Sinon il est traité en extérieur et
JOSY est alerté d'une possible usurpation. Même authentifié, un email ne déclenche jamais l'envoi
de données internes par email : le Cortex prévient JOSY sur Telegram et l'interface locale.
"""

import json
import re
from email.utils import parseaddr
from pathlib import Path

FICHIER = Path(__file__).resolve().parent / "identites.json"
ROLES_CONNUS = ("fondateur", "admin_entreprise")


def roles():
    try:
        donnees = json.loads(FICHIER.read_text(encoding="utf-8"))
        return {k.strip().lower(): v for k, v in (donnees.get("roles") or {}).items()
                if v in ROLES_CONNUS}
    except (OSError, ValueError):
        return {}  # fichier absent ou illisible : personne n'est reconnu (défaut sûr)


def role_de(adresse):
    """Rôle déclaré d'une adresse : « fondateur », « admin_entreprise » ou « exterieur »."""
    return roles().get(parseaddr(adresse or "")[1].strip().lower(), "exterieur")


def authentifie(msg, adresse):
    """Vrai si le serveur de réception a validé l'expéditeur (DMARC pass, ou DKIM pass signé par
    le domaine de l'adresse). Seuls les en-têtes Authentication-Results sont lus."""
    domaine = parseaddr(adresse or "")[1].rpartition("@")[2].lower()
    if not domaine:
        return False
    for entete in msg.get_all("Authentication-Results") or []:
        texte = str(entete).lower()
        if re.search(r"\bdmarc=pass\b", texte) and f"header.from={domaine}" in texte:
            return True
        if re.search(rf"\bdkim=pass\b[^;]*header\.(?:d|i)=@?{re.escape(domaine)}\b", texte):
            return True
    return False


def identifier(msg):
    """(adresse, rôle effectif, rôle déclaré) d'un email reçu. Le rôle effectif d'un fondateur non
    authentifié est « exterieur »."""
    adresse = parseaddr(msg.get("From", ""))[1].strip().lower()
    declare = role_de(adresse)
    if declare == "fondateur" and not authentifie(msg, adresse):
        return adresse, "exterieur", declare
    return adresse, declare, declare
