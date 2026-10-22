"""Google Places (API New) comme source facultative, avec repli propre sur Serper.

Inactif tant que GOOGLE_PLACES_KEY est absente. Si Google refuse la clé (401, 403) ou signale un quota
dépassé (429), le module se désactive pour la journée, envoie UN message Telegram clair et rend la main :
audit.py continue avec Serper, sans aucune erreur. Données (notes, avis) conservées 30 jours au plus, comme
le cache existant. Aucune valeur de clé n'est écrite dans les messages ni les journaux.
"""

import os
from datetime import date

import requests

URL = "https://places.googleapis.com/v1/places:searchText"
CHAMPS = "places.id,places.displayName,places.rating,places.userRatingCount,places.formattedAddress,places.websiteUri"
_etat = {"refus": None}   # jour du dernier refus : pas de nouvel essai avant demain


def cle():
    return os.environ.get("GOOGLE_PLACES_KEY", "").strip()


def actif():
    return bool(cle()) and _etat["refus"] != date.today().isoformat()


def search(query, notifier=None):
    """Mêmes champs que audit.serper_search : id, nom, note, avis, adresse, site. None = utiliser Serper."""
    if not actif():
        return None
    try:
        r = requests.post(URL, timeout=20, json={"textQuery": query, "languageCode": "fr", "regionCode": "FR"},
                          headers={"X-Goog-Api-Key": cle(), "X-Goog-FieldMask": CHAMPS})
    except requests.RequestException:
        return None
    if r.status_code in (401, 403, 429):
        _etat["refus"] = date.today().isoformat()
        if notifier:
            motif = {401: "clé non acceptée (API Places (New) exige une clé classique)",
                     403: "accès refusé (API non activée ou facturation absente)",
                     429: "quota dépassé"}[r.status_code]
            notifier("google_places", f"{motif}. Repli automatique sur Serper")
        return None
    if r.status_code != 200:
        return None
    try:
        places = r.json().get("places") or []
    except ValueError:
        return None
    return [{"id": p.get("id", ""), "nom": (p.get("displayName") or {}).get("text", ""),
             "note": p.get("rating"), "avis": int(p.get("userRatingCount") or 0),
             "adresse": p.get("formattedAddress", ""), "site": p.get("websiteUri", "")} for p in places] or None
