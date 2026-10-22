"""Publie (ou met à jour) les pages de josyei.com via l'API REST WordPress :
l'accueil, /mentions-legales et /politique-de-confidentialite (/diagnostic renvoie vers l'accueil).
Identifiants : WP_URL, WP_USER, WP_APP_PASSWORD dans .env (mot de passe d'application)."""

import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")
URL = os.environ.get("WP_URL", "https://josyei.com").rstrip("/")
AUTH = (os.environ.get("WP_USER", "Mrjosyvalery"), os.environ["WP_APP_PASSWORD"])

MENTIONS = """<div class="jei"><div class="w"><section class="stack">

<p><b>Éditeur du site</b> : JOSY EI, entrepreneur individuel. SIREN 914 113 543. TVA intracommunautaire FR00914113543. Siège : 86500 Montmorillon, France. Contact : contact@josyei.com.</p>
<p><b>Directeur de la publication</b> : l'entrepreneur individuel exploitant JOSY EI.</p>
<p><b>Hébergeur</b> : Hostinger International Ltd, 61 Lordou Vironos Street, 6023 Larnaca, Chypre.</p>
<p><b>Propriété intellectuelle</b> : les textes et éléments graphiques de ce site sont la propriété de JOSY EI, sauf mention contraire. Toute reproduction sans autorisation est interdite.</p>
<p><b>Données personnelles</b> : voir la <a href="/politique-de-confidentialite/">politique de confidentialité</a>.</p>
<p>Découvrez notre <a href="/">présentation du Cortex</a>.</p>
</section></div></div>"""

CONFIDENTIALITE = """<div class="jei"><div class="w"><section class="stack">

<p><b>Responsable du traitement</b> : JOSY EI, SIREN 914 113 543, contact@josyei.com.</p>
<p><b>Données collectées</b> : celles que vous nous envoyez par email (nom, prénom, email professionnel, téléphone, site web, objectif de votre demande), ainsi que les informations professionnelles publiques sur votre entreprise (annuaire officiel des entreprises, site internet, résultats de recherche).</p>
<p><b>Finalités et bases légales</b> : répondre à votre demande et préparer notre offre (mesures précontractuelles à votre demande) ; prospection commerciale par email auprès de professionnels, sur des sujets liés à leur activité (intérêt légitime, article 6.1.f du RGPD).</p>
<p><b>Durée de conservation</b> : 3 ans à compter du dernier échange, puis suppression. Les adresses des personnes qui s'opposent à la prospection sont conservées sous forme chiffrée, uniquement pour ne plus les contacter.</p>
<p><b>Destinataires</b> : JOSY EI uniquement. Les emails transitent par notre hébergeur de messagerie (Hostinger). Certains textes peuvent être traités par un service d'intelligence artificielle pour préparer une réponse ; aucune donnée n'est vendue ni cédée.</p>
<p><b>Météo et heure de la page d'accueil</b> : si, et seulement si, vous acceptez la géolocalisation proposée par votre navigateur, votre position approximative (coordonnées arrondies à 2 décimales) est envoyée par votre navigateur à Open-Meteo (température) et à OpenStreetMap Nominatim (nom de la ville). JOSY EI ne reçoit ni ne conserve cette position : aucun cookie, aucun stockage. Sans votre accord, aucun appel n'est fait et la page affiche « Montmorillon (86) ».</p>
<p><b>Vos droits</b> : accès, rectification, effacement, opposition, limitation et portabilité. Pour ne plus recevoir de message, répondez STOP à n'importe quel email ou écrivez à contact@josyei.com. Vous pouvez aussi saisir la CNIL (www.cnil.fr).</p>
<p>Voir aussi les <a href="/mentions-legales/">mentions légales</a> et la <a href="/">présentation du Cortex</a>.</p>
</section></div></div>"""


SEO = {  # titre SEO et meta description (155 caractères au plus) par page
    "accueil": ("Le Cortex, employé IA pour site, Google et boutique | JOSY EI",
                "Le Cortex gère votre site web, votre fiche Google Business et votre boutique en ligne, "
                "24h/24. Formules de 0 à 19,99 € HT par mois, essai gratuit de 3 jours sur Pro."),
    "mentions-legales": ("Mentions légales | JOSY EI",
                         "Mentions légales du site josyei.com : éditeur JOSY EI, entrepreneur individuel "
                         "(SIREN 914 113 543), hébergeur et propriété intellectuelle."),
    "politique-de-confidentialite": ("Politique de confidentialité | JOSY EI",
                                     "Comment JOSY EI collecte et protège vos données : finalités, "
                                     "bases légales, durée de conservation et exercice de vos droits RGPD."),
}

REDIRECTION = """<meta http-equiv="refresh" content="0;url=/">
<link rel="canonical" href="https://josyei.com/">
<p>Cette page a déménagé : <a href="/">retour à l'accueil</a>.</p>
<script>location.replace("/");</script>"""


def style():
    return (BASE / "page-style.css.html").read_text(encoding="utf-8")


def publish(slug, title, html, with_style=True):
    content = f"<!-- wp:html -->\n{style() if with_style else ''}\n{html}\n<!-- /wp:html -->"
    api = f"{URL}/wp-json/wp/v2/pages"
    found = requests.get(api, params={"slug": slug, "status": "publish,draft,private"}, auth=AUTH, timeout=30)
    found.raise_for_status()
    data = {"title": title, "slug": slug, "status": "publish", "content": content}
    if slug in SEO:  # pris en compte seulement si l'extension SEO expose ces champs à l'API
        data["meta"] = {"rank_math_title": SEO[slug][0], "rank_math_description": SEO[slug][1]}
        data["excerpt"] = SEO[slug][1]  # l'extrait sert souvent de meta description
    target = f"{api}/{found.json()[0]['id']}" if found.json() else api
    for attempt in range(3):  # connexion parfois coupée (pare-feu ou antivirus) : on réessaie
        try:
            r = requests.post(target, json=data, auth=AUTH, timeout=60)
            break
        except requests.exceptions.SSLError:
            if attempt == 2:
                raise
            time.sleep(5)
    if r.status_code not in (200, 201):
        print("ÉCHEC", slug, r.status_code, r.text[:200])
        return False
    print("publiée :", r.json().get("link"))
    return True


def main():
    body = (BASE / "page-accueil.html").read_text(encoding="utf-8")
    ok = publish("accueil", "Le Cortex, votre employé IA pour votre présence en ligne", body, with_style=False)
    ok &= publish("mentions-legales", "Mentions légales", MENTIONS)
    ok &= publish("politique-de-confidentialite", "Politique de confidentialité", CONFIDENTIALITE)
    ok &= remplacer_diagnostic()
    if not ok:
        return 1
    api = f"{URL}/wp-json/wp/v2"
    home = requests.get(f"{api}/pages", params={"slug": "accueil"}, auth=AUTH, timeout=30).json()[0]["id"]
    requests.post(f"{api}/settings", json={"show_on_front": "page", "page_on_front": home}, auth=AUTH, timeout=30)
    return 0


def remplacer_diagnostic():
    """Supprime définitivement les anciennes pages /diagnostic (corbeille comprise), puis
    publie une page de renvoi vers l'accueil."""
    api = f"{URL}/wp-json/wp/v2"
    for p in requests.get(f"{api}/pages", params={"slug": "diagnostic", "status": "publish,draft,private,trash"},
                          auth=AUTH, timeout=30).json():
        r = requests.delete(f"{api}/pages/{p['id']}", params={"force": "true"}, auth=AUTH, timeout=30)
        print("ancienne page /diagnostic supprimée définitivement :", p["id"], r.status_code)
    return publish("diagnostic", "Diagnostic", REDIRECTION, with_style=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
