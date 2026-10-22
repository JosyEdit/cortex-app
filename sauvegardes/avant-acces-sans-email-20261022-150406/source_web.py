"""Recherche web avec repli automatique : Serper, puis Brave (si clé), puis DuckDuckGo (sans clé).

Résultat normalisé : [{"url", "title", "description", "source"}], ou [] si tout échoue (rien n'est inventé).
Serper n'est utilisé ici que si SERPER_WEB=1 : ses crédits gratuits (2 500) servent d'abord aux arguments
Google Maps. Quand Serper répond 402 (crédits épuisés) ou 429, il est suspendu pour la journée et le repli prend
le relais sans erreur. La dernière source utilisée est lisible dans `derniere_source`.
"""

import os
import time
from datetime import date

import requests

SERPER_SEARCH = "https://google.serper.dev/search"
derniere_source = None
_suspendu = {"jour": None}


def _serper(query, count):
    cle = os.environ.get("SERPER_API_KEY", "").strip()
    if not cle or os.environ.get("SERPER_WEB") != "1" or _suspendu["jour"] == date.today().isoformat():
        return None
    try:
        r = requests.post(SERPER_SEARCH, timeout=30, headers={"X-API-KEY": cle, "Content-Type": "application/json"},
                          json={"q": query, "gl": "fr", "hl": "fr", "num": count})
    except requests.RequestException:
        return None
    if r.status_code in (402, 429):
        _suspendu["jour"] = date.today().isoformat()
        return None
    if r.status_code != 200:
        return None
    try:
        return [{"url": o.get("link", ""), "title": o.get("title", ""), "description": o.get("snippet", ""),
                 "source": "serper"} for o in r.json().get("organic", [])[:count]]
    except ValueError:
        return None


def recherche(query, count=8):
    global derniere_source
    hits = _serper(query, count)
    if hits:
        derniere_source = "serper"
        return hits
    import audit  # Brave si BRAVE_API_KEY, sinon DuckDuckGo (même code que le reste du Cortex)
    res = audit.brave_search(query, count) or []
    derniere_source = "brave" if audit.brave_key() else "duckduckgo"
    return [dict(h, source=derniere_source) for h in res if h.get("url")]
