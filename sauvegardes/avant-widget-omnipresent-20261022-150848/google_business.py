"""Google Business Profile : publication de posts et réponses aux avis, SUR VALIDATION de JOSY.

Inactif tant que GBP_CLIENT_ID, GBP_CLIENT_SECRET, GBP_REFRESH_TOKEN et GBP_LOCATION ne sont pas tous présents
(accès à faire approuver côté Google). Ce module ne décide rien : il est appelé seulement après un /valider
explicite (action google_post ou reponse_avis). Sans clés, `publier_post` et `repondre_avis` lèvent NonActif et
le message de refus dit exactement ce qui manque. Aucune valeur de clé n'est écrite dans un journal.
"""

import os

import requests

REQUIS = ("GBP_CLIENT_ID", "GBP_CLIENT_SECRET", "GBP_REFRESH_TOKEN", "GBP_LOCATION")
TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://mybusiness.googleapis.com/v4"


class NonActif(Exception):
    """Module inactif : message sans secret, prêt à être envoyé sur Telegram."""


def manquantes():
    return [k for k in REQUIS if not os.environ.get(k, "").strip()]


def actif():
    return not manquantes()


def _jeton():
    r = requests.post(TOKEN_URL, timeout=30, data={
        "client_id": os.environ["GBP_CLIENT_ID"], "client_secret": os.environ["GBP_CLIENT_SECRET"],
        "refresh_token": os.environ["GBP_REFRESH_TOKEN"], "grant_type": "refresh_token"})
    if r.status_code != 200:
        raise NonActif(f"autorisation Google refusée (code {r.status_code}) : à renouveler côté Google")
    return r.json()["access_token"]


def _verifier():
    if not actif():
        raise NonActif("Google Business inactif : variables manquantes : " + ", ".join(manquantes()))


def publier_post(texte, lien=None):
    """Publie une actualité sur la fiche (localPosts.create). Appelé uniquement après /valider."""
    _verifier()
    corps = {"languageCode": "fr", "summary": texte[:1500], "topicType": "STANDARD"}
    if lien:
        corps["callToAction"] = {"actionType": "LEARN_MORE", "url": lien}
    r = requests.post(f"{API}/{os.environ['GBP_LOCATION']}/localPosts", timeout=30,
                      headers={"Authorization": f"Bearer {_jeton()}"}, json=corps)
    if r.status_code not in (200, 201):
        raise NonActif(f"publication refusée par Google (code {r.status_code})")
    return r.json().get("name", "")


def lister_avis(n=20):
    _verifier()
    r = requests.get(f"{API}/{os.environ['GBP_LOCATION']}/reviews", timeout=30, params={"pageSize": n},
                     headers={"Authorization": f"Bearer {_jeton()}"})
    if r.status_code != 200:
        raise NonActif(f"lecture des avis refusée par Google (code {r.status_code})")
    return [{"nom": a.get("name"), "note": a.get("starRating"), "texte": (a.get("comment") or "")[:500],
             "repondu": bool(a.get("reviewReply"))} for a in r.json().get("reviews", [])]


def repondre_avis(nom_avis, texte):
    """Répond à un avis (reviews.updateReply). Appelé uniquement après /valider."""
    _verifier()
    r = requests.put(f"{API}/{nom_avis}/reply", timeout=30,
                     headers={"Authorization": f"Bearer {_jeton()}"}, json={"comment": texte[:4000]})
    if r.status_code not in (200, 201):
        raise NonActif(f"réponse refusée par Google (code {r.status_code})")
    return True
