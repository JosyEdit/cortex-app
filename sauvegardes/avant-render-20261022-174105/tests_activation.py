"""Tests des modules prêts à s'activer (aucun réseau, aucune vraie clé : valeurs factices de test)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import requests

import cortex as c
import demarrage
import google_business
import source_places
import source_web

ok = 0


def check(nom, cond):
    global ok
    print(("OK   " if cond else "ÉCHEC"), nom)
    ok += bool(cond)


class Rep:
    def __init__(self, code, data=None):
        self.status_code, self._d, self.text = code, data or {}, ""

    def json(self):
        return self._d


class TG:
    enabled = True

    def __init__(self):
        self.out = []

    def send(self, t, buttons=None):
        self.out.append(t)
        return 1

    def alert(self, k, m):
        self.out.append(f"alerte {k}: {m}")


store = c.Store(":memory:")
tg = TG()
store.tg = tg
cx = c.Cortex(store, tg)

# 1. contrôle de démarrage
for k in ("GOOGLE_PLACES_KEY", "GBP_CLIENT_ID"):
    os.environ.pop(k, None)
m = {x[0] for x in demarrage.manquantes()}
check("démarrage : GOOGLE_PLACES_KEY et GBP_CLIENT_ID signalées", {"GOOGLE_PLACES_KEY", "GBP_CLIENT_ID"} <= m)
check("démarrage : aucune clé de paiement attendue (zéro abonnement)", not ({"PAYPLUG_KEY", "STRIPE_KEY", "LIVRAISON_SECRET"} & {x[0] for x in demarrage.CLES}))
check("démarrage : rapport sans valeur de clé", "AIza" not in demarrage.rapport() and "GOOGLE_PLACES_KEY" in demarrage.rapport())
demarrage.notifier(c, cx)
demarrage.notifier(c, cx)
check("démarrage : un seul message Telegram par jour", sum("🔑" in t for t in tg.out) == 1)

# 2. Google Places : repli propre
check("places : inactif sans clé", source_places.search("plombier Poitiers") is None and not source_places.actif())
os.environ["GOOGLE_PLACES_KEY"] = "cle-factice-test"
alertes = []
requests.post = lambda *a, **k: Rep(401)
check("places : 401 -> None (repli Serper)", source_places.search("x", lambda k, m: alertes.append((k, m))) is None)
check("places : message clair, désactivé pour la journée", len(alertes) == 1 and not source_places.actif())
source_places._etat["refus"] = None
requests.post = lambda *a, **k: Rep(200, {"places": [{"id": "1", "displayName": {"text": "Dupont"}, "rating": 4.5,
                                                        "userRatingCount": 12, "formattedAddress": "1 rue, 86000 Poitiers"}]})
r = source_places.search("plombier Poitiers")
check("places : 200 -> même format que Serper", r and r[0]["nom"] == "Dupont" and r[0]["avis"] == 12)
os.environ.pop("GOOGLE_PLACES_KEY")

# 3. Google Business : inactif sans accès
try:
    google_business.publier_post("test")
    check("gbp : refus sans accès", False)
except google_business.NonActif as e:
    check("gbp : refus clair listant les variables manquantes", "GBP_CLIENT_ID" in str(e) and "GBP_LOCATION" in str(e))
for k in google_business.REQUIS:
    os.environ[k] = "valeur-factice"
os.environ["GBP_LOCATION"] = "accounts/1/locations/2"
posts = []


def faux_post(url, **kw):
    posts.append(url)
    if "oauth2" in url:
        return Rep(200, {"access_token": "jeton-test"})
    return Rep(200, {"name": "accounts/1/locations/2/localPosts/3"})


requests.post = faux_post
check("gbp : publication simulée après activation", google_business.publier_post("Bonjour") .endswith("/3") and len(posts) == 2)
for k in google_business.REQUIS:
    os.environ.pop(k)

# 4. Recherche web : Serper puis repli
import audit
audit.brave_search = lambda q, n=8: [{"url": "https://exemple.fr", "title": "t", "description": "d"}]
os.environ.pop("SERPER_WEB", None)
check("web : Serper non utilisé sans SERPER_WEB (crédits protégés) -> repli", source_web.recherche("x")[0]["source"] in ("duckduckgo", "brave"))
os.environ["SERPER_WEB"] = "1"
os.environ["SERPER_API_KEY"] = "cle-factice-test"
requests.post = lambda *a, **k: Rep(402)
res = source_web.recherche("x")
check("web : Serper 402 -> suspendu, repli actif", res and res[0]["source"] != "serper" and source_web._suspendu["jour"])
source_web._suspendu["jour"] = None
requests.post = lambda *a, **k: Rep(200, {"organic": [{"link": "https://a.fr", "title": "A", "snippet": "s"}]})
check("web : Serper 200 -> source serper", source_web.recherche("x")[0]["source"] == "serper")
for k in ("SERPER_WEB", "SERPER_API_KEY"):
    os.environ.pop(k, None)

print(f"\n{ok} vérifications réussies")
