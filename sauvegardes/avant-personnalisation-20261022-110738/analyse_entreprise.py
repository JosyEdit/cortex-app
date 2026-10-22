"""Analyse Entreprise (onglet Discuter : « Analyse la société X », avec ou sans lien vers son site).

1. Registre public : API de l'État recherche-entreprises.api.gouv.fr (SIREN, activité, effectif
   déclaré, création, dirigeants, chiffre d'affaires publié s'il existe).
2. Site de l'entreprise (si un lien est donné) : ouvert par Playwright dans le Chrome installé,
   JavaScript exécuté, bannière de cookies REFUSÉE quand un bouton « Refuser » existe.
3. Synthèse en tableau, chaque ligne avec sa source. Rien n'est inventé (I1).

Limites voulues : données publiques seulement ; aucune protection anti-robot ni page de connexion
n'est contournée ; LinkedIn, Facebook, Instagram, X et TikTok ne sont pas lus (leurs conditions
interdisent l'extraction automatisée). Les noms de dirigeants viennent du registre public, ne
servent qu'à la fiche affichée et ne sont pas enregistrés.
"""

import re
import urllib.parse

import requests

API = "https://recherche-entreprises.api.gouv.fr/search"
RESEAUX = re.compile(r"(^|\.)(linkedin|facebook|instagram|x|twitter|tiktok|youtube|pinterest)\.com$", re.I)
DEMANDE_RE = re.compile(r"^\s*(?:peux-tu\s+|pouvez-vous\s+)?analyse[rz]?\s+(?:la\s+soci[ée]t[ée]|"
                        r"l['’]\s?entreprise|la\s+bo[iî]te|le\s+cabinet|la\s+structure)\s+(.+)$", re.I | re.S)
TRANCHES = {"NN": "non employeuse", "00": "0 salarié", "01": "1 à 2", "02": "3 à 5", "03": "6 à 9",
            "11": "10 à 19", "12": "20 à 49", "21": "50 à 99", "22": "100 à 199", "31": "200 à 249",
            "32": "250 à 499", "41": "500 à 999", "42": "1 000 à 1 999", "51": "2 000 à 4 999",
            "52": "5 000 à 9 999", "53": "10 000 et plus"}
REFUS_COOKIES = ("Tout refuser", "Refuser tout", "Refuser", "Continuer sans accepter",
                 "Je refuse", "Reject all", "Decline")


def demande(texte):
    """(nom ou SIREN, URL du site ou None) si le message demande une analyse, sinon None."""
    m = DEMANDE_RE.match(texte or "")
    if not m:
        return None
    reste = m.group(1).strip()
    url = (re.search(r"https?://\S+", reste) or [None])[0]
    nom = re.sub(r"https?://\S+", "", reste)
    nom = re.sub(r"\b(son site|site|sur|avec|:)\s*$", "", nom.strip(), flags=re.I).strip(" ,.;:?!«»\"'")
    return (nom or None), (url.rstrip(".,;:!?") if url else None)


def registre(nom):
    """Première correspondance du registre public, ou None."""
    r = requests.get(API, params={"q": nom, "per_page": 3, "page": 1}, timeout=20,
                     headers={"User-Agent": "JOSY-EI-Cortex/1.0 (+https://josyei.com)"})
    r.raise_for_status()
    res = r.json().get("results") or []
    return res[0] if res else None, len(res)


def _dirigeants(e):
    lignes = []
    for d in (e.get("dirigeants") or [])[:4]:
        if d.get("type_dirigeant") == "personne morale":
            lignes.append(f"{d.get('denomination', '?')} ({d.get('qualite') or 'dirigeant'})")
        else:
            nom = " ".join(x for x in (d.get("prenoms", "").split(" ")[0], d.get("nom", "")) if x).title()
            lignes.append(f"{nom} ({d.get('qualite') or 'dirigeant'})")
    return " · ".join(lignes) or "non publié"


def _finances(e):
    fin = e.get("finances") or {}
    if not fin:
        return "non publié"
    annee = max(fin)
    ca, rn = fin[annee].get("ca"), fin[annee].get("resultat_net")
    morceaux = []
    if ca is not None:
        morceaux.append(f"CA {ca:,.0f} €".replace(",", " "))
    if rn is not None:
        morceaux.append(f"résultat net {rn:,.0f} €".replace(",", " "))
    return f"{' · '.join(morceaux) or 'non publié'} ({annee})"


def lire_site(url):
    """Rend la page avec Playwright (Chrome installé). Renvoie (titre, description, texte)."""
    from playwright.sync_api import sync_playwright
    hote = urllib.parse.urlparse(url).hostname or ""
    if RESEAUX.search(hote):
        raise ValueError("réseau social : extraction automatisée interdite par ses conditions")
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome", headless=True)
        try:
            page = nav.new_page(locale="fr-FR", user_agent=None)
            page.goto(url, timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            for libelle in REFUS_COOKIES:  # choix le plus respectueux de la vie privée
                bouton = page.get_by_role("button", name=libelle, exact=False)
                if bouton.count():
                    try:
                        bouton.first.click(timeout=2000)
                        page.wait_for_timeout(800)
                        break
                    except Exception:
                        pass
            titre = page.title()
            desc = page.evaluate("() => (document.querySelector('meta[name=description]')||{}).content||''")
            texte = page.inner_text("body", timeout=5000)
        finally:
            nav.close()
    if re.search(r"captcha|are you a robot|access denied|vérifiez que vous êtes humain", texte[:3000], re.I):
        raise ValueError("le site affiche une protection anti-robot : non contournée")
    return titre, desc, re.sub(r"\n\s*\n+", "\n", texte)


def indices_site(texte):
    """Indices factuels repérés tels quels dans le texte du site (aucune déduction)."""
    effectif = re.search(r"(\d[\d\s]{0,6})\s*(salariés|collaborateurs|employés|personnes|experts)", texte, re.I)
    actus = [l.strip() for l in texte.splitlines()
             if re.search(r"\b(actualit|news|blog|nouveau|nouvelle|ouverture|lancement)", l, re.I)
             and 15 < len(l.strip()) < 140][:3]
    return (effectif.group(0).strip() if effectif else None), actus


def analyser(nom, url, store, appeler_llm=None):
    """Fiche texte (tableau « champ : valeur — source ») et liste des sources lues."""
    lignes, sources = [], []
    e, n = (None, 0)
    if nom:
        try:
            e, n = registre(nom)
        except Exception as exc:
            lignes.append(f"Registre public : indisponible ({type(exc).__name__})")
    if e:
        siege = e.get("siege") or {}
        src = "registre public (recherche-entreprises.api.gouv.fr)"
        sources.append(src)
        tranche = e.get("tranche_effectif_salarie") or siege.get("tranche_effectif_salarie")
        lignes += [
            f"Nom : {e.get('nom_complet', '?')}",
            f"SIREN : {e.get('siren', '?')}",
            f"État : {'active' if e.get('etat_administratif') == 'A' else 'fermée'}",
            f"Activité (NAF) : {e.get('activite_principale', '?')}",
            f"Siège : {siege.get('code_postal', '')} {siege.get('libelle_commune', '')}".rstrip(),
            f"Création : {e.get('date_creation') or '?'}",
            f"Effectif déclaré : {TRANCHES.get(tranche, 'non publié')}"
            + (f" ({e.get('annee_tranche_effectif_salarie')})" if tranche and e.get('annee_tranche_effectif_salarie') else ""),
            f"Finances : {_finances(e)}",
            f"Dirigeants : {_dirigeants(e)}",
        ]
        lignes = [f"{l} — source : registre public" if not l.startswith("Registre") else l for l in lignes]
        if n > 1:
            lignes.append(f"(À vérifier : {n} résultats pour « {nom} », j'ai pris le premier.)")
        store.log("EXECUTIF", "analyse_entreprise", details={"siren": e.get("siren"), "site": bool(url)})
    elif nom:
        lignes.append(f"Registre public : aucune entreprise trouvée pour « {nom} ».")
    synthese = ""
    if url:
        try:
            titre, desc, texte = lire_site(url)
            sources.append(url)
            effectif, actus = indices_site(texte)
            lignes.append(f"Site : {titre or url} — source : {url}")
            if desc:
                lignes.append(f"Présentation : {desc[:200]} — source : {url}")
            lignes.append(f"Effectif cité sur le site : {effectif or 'aucun'} — source : {url}")
            if actus:
                lignes.append(f"Actualités repérées : {' | '.join(actus)} — source : {url}")
            if appeler_llm:
                synthese = appeler_llm(texte[:4500]) or ""
        except Exception as exc:
            raison = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            lignes.append(f"Site : non lu ({raison}) — {url}")
    elif e:
        lignes.append("Site : aucun lien donné (ajoute-le à ta demande pour que je le lise).")
    titre = f"Analyse : {(e or {}).get('nom_complet') or nom or url}"
    fiche = titre + "\n" + "\n".join(f"• {l}" for l in lignes)
    if synthese:
        fiche += "\n\nCe que dit le site (synthèse) :\n" + synthese.strip()
    fiche += ("\n\nNon lus : LinkedIn et les réseaux sociaux (extraction automatisée interdite par leurs "
              "conditions).")
    return fiche, sources
