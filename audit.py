"""Analyse approfondie d'un prospect, à partir de sources publiques uniquement.

  identité   : annuaire officiel (recherche-entreprises.api.gouv.fr) : nom, adresse, SIREN,
               dirigeant(s) déclarés (nom et qualité, donnée publique du registre)
  site web   : lu directement (HTTPS, version mobile, page contact, formulaire, mentions
               légales, politique de confidentialité, date du copyright)
  manques    : déduits des seuls faits vérifiés
  services   : uniquement ceux du catalogue qui comblent un manque constaté

Avec BRAVE_API_KEY (.env) : site trouvé par recherche, fiche Google (note, avis) quand
Brave la renvoie. Ce qui n'est pas vérifié (fiche Google sans résultat,
téléphone direct, activité des réseaux) n'est jamais cité. Règle : un prospect n'est gardé
que s'il a au moins un manque vérifié ; sinon pas d'email.
"""

import json
import os
import re
import time
from pathlib import Path
from datetime import date
from urllib.parse import urljoin, urlparse

import requests

UA = "JOSY-EI-Cortex/1.0 (+https://josyei.com)"
# Adresse isolée : ni collée à des chiffres avant (téléphone), ni suivie de chiffres après le TLD.
EMAIL_RE = re.compile(r"(?<![\w.])[a-zA-Z][\w.+-]*@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}(?![\w])")
COMPANY_API = "https://recherche-entreprises.api.gouv.fr/search"
SHARED_DOMAINS = re.compile(r"(^|\.)(gmail|googlemail|hotmail|outlook|live|yahoo|orange|wanadoo|"
                            r"free|sfr|neuf|laposte|bbox|aol|icloud|gmx|notaires|cerfrance)\.",
                            re.IGNORECASE)


def _get(url, timeout=15):
    try:
        t0 = time.monotonic()
        r = requests.get(url, timeout=timeout, headers={"User-Agent": UA}, allow_redirects=True)
        return r, time.monotonic() - t0
    except requests.RequestException:
        return None, None


# ----------------------------------------------------------------- Brave Search
# Clé BRAVE_API_KEY dans .env. Sans clé : aucune recherche, l'analyse se limite au site
# déduit de l'email. Quota mensuel suivi dans brave_usage.json (BRAVE_MONTHLY_QUOTA).
BRAVE_API = "https://api.search.brave.com/res/v1/web/search"
BRAVE_USAGE = Path(__file__).resolve().parent / "brave_usage.json"
DIRECTORIES = re.compile(r"pagesjaunes|societe\.com|pappers|verif\.com|infogreffe|manageo|kompass|"
                         r"annuaire|118712|mappy|justacote|wikipedia|indeed|doctrine|"
                         r"^(www\.)?notaires\.fr$|immobilier\.notaires|immonot|^(www\.)?avocat\.fr$|google\.|bing\.|youtube|facebook|instagram|"
                         r"bing\.com|duckduckgo|yelp|tripadvisor|"
                         r"lefigaro|ouest-france|leboncoin|cylex|hoodspot|societeinfo|e-pro\.fr|"
                         r"thefork|lafourchette|ubereats|deliveroo|planity|treatwell|houzz|"
                         r"habitatpresto|travaux\.com|starofservice", re.IGNORECASE)


def brave_key():
    return os.environ.get("BRAVE_API_KEY", "").strip()


def _brave_quota_ok():
    month = date.today().strftime("%Y-%m")
    try:
        usage = json.loads(BRAVE_USAGE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        usage = {}
    limit = int(os.environ.get("BRAVE_MONTHLY_QUOTA", "2000"))
    if usage.get(month, 0) >= limit:
        return False
    usage[month] = usage.get(month, 0) + 1
    BRAVE_USAGE.write_text(json.dumps(usage), encoding="utf-8")
    return True


_DDG_LAST = [0.0]


def ddg_search(query, count=8):
    """DuckDuckGo (paquet ddgs, sans clé). Pause de 2 s entre requêtes ; [] si bloqué."""
    try:
        from ddgs import DDGS
    except ImportError:
        return []
    wait = 2.0 - (time.monotonic() - _DDG_LAST[0])
    if wait > 0:
        time.sleep(wait)
    try:
        hits = list(DDGS().text(query, region="fr-fr", max_results=count))
    except Exception:
        hits = []  # limite atteinte ou blocage : dégradation propre, aucun constat
    _DDG_LAST[0] = time.monotonic()
    return [{"url": h.get("href", ""), "title": h.get("title", ""), "description": h.get("body", "")}
            for h in hits if "bing.com/aclick" not in h.get("href", "")]


def search_available():
    return bool(brave_key()) or ddg_available()


def ddg_available():
    try:
        import ddgs  # noqa: F401
        return True
    except ImportError:
        return False


def brave_search(query, count=8):
    """Recherche web : Brave si BRAVE_API_KEY est présente, sinon DuckDuckGo."""
    if not brave_key():
        return ddg_search(query, count)
    if not _brave_quota_ok():
        return []
    try:
        r = requests.get(BRAVE_API, params={"q": query, "count": count, "country": "fr",
                                            "search_lang": "fr"},
                         headers={"X-Subscription-Token": brave_key(), "Accept": "application/json"},
                         timeout=20)
        if r.status_code == 429:  # limite par seconde du plan gratuit
            time.sleep(1.5)
            return []
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        return []
    time.sleep(1.1)  # plan gratuit : 1 requête par seconde
    out = [{"url": h.get("url", ""), "title": h.get("title", ""), "description": h.get("description", "")}
           for h in (data.get("web") or {}).get("results", [])]
    out += [{"url": loc.get("url") or "", "title": loc.get("title", ""), "local": loc}
            for loc in (data.get("locations") or {}).get("results", [])]
    return out


def _tokens(text):
    stop = {"sas", "sarl", "selarl", "scp", "et", "associes", "associés", "de", "du", "la", "le", "les",
            "des", "cabinet", "office", "notarial", "notaires", "avocats", "selas", "sa"}
    return [t for t in re.findall(r"[a-zà-ÿ0-9]{3,}", (text or "").lower()) if t not in stop]


def find_website(nom, ville):
    """Site officiel par Brave : premier résultat hors annuaires dont la page cite le nom."""
    for hit in brave_search(f"{nom} {ville}"):
        url = hit["url"]
        host = urlparse(url).netloc.lower()
        if not url.startswith("http") or DIRECTORIES.search(host):
            continue
        r, _ = _get(f"{urlparse(url).scheme}://{urlparse(url).netloc}/")
        if r is None or r.status_code >= 400:
            continue
        low = r.text.lower()
        toks = _tokens(nom)
        need = len(toks) if len(toks) <= 2 else -(-2 * len(toks) // 3)  # tous, ou les 2/3
        city = (ville or "").lower().split(" ")[0].replace("-", " ")
        city_ok = not city or city in low.replace("-", " ")  # un site local cite sa commune
        if toks and sum(t in low for t in toks) >= need and city_ok:
            return f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    return None


def google_presence(nom, ville):
    """Fiche d'établissement (note, nombre d'avis) si Brave la renvoie ; sinon non vérifiée."""
    for hit in brave_search(f"{nom} {ville} avis", count=5):
        loc = hit.get("local")
        if loc:
            rating = loc.get("rating") or {}
            return {"trouvee": True, "note": rating.get("ratingValue"),
                    "avis": rating.get("reviewCount"), "source": "Brave Search (fiche locale)"}
    return None  # non vérifié : jamais cité


def page_exists(root, paths):
    for p in paths:
        r, _ = _get(urljoin(root + "/", p), timeout=10)
        if r is not None and r.status_code == 200 and len(r.text) > 500:
            return urljoin(root + "/", p)
    return None


def find_company(nom, ville="", siren=""):
    """Fiche officielle : SIREN, adresse, dirigeants (nom + qualité)."""
    params = {"q": siren or nom, "per_page": 5}
    try:
        res = requests.get(COMPANY_API, params=params, timeout=20).json().get("results", [])
    except (requests.RequestException, ValueError):
        return None
    ville_l = (ville or "").lower()
    if siren:
        pick = next((e for e in res if e.get("siren") == siren), None)
    else:  # sans SIREN, on n'accepte qu'une fiche dans la même commune (pas d'homonyme)
        pick = next((e for e in res if ville_l and ville_l in
                     ((e.get("siege") or {}).get("libelle_commune") or "").lower()), None)
    if not pick or pick.get("statut_diffusion") != "O":
        return None
    siege = pick.get("siege") or {}
    dirigeants = []
    for d in pick.get("dirigeants") or []:
        if d.get("type_dirigeant") == "personne physique":
            nom_d = " ".join(x for x in (d.get("prenoms", "").split(" ")[0].title(),
                                         (d.get("nom") or "").upper()) if x)
            dirigeants.append({"nom": nom_d, "qualite": d.get("qualite") or ""})
        elif d.get("denomination"):
            dirigeants.append({"nom": d["denomination"], "qualite": d.get("qualite") or ""})
    return {"siren": pick["siren"], "nom": pick.get("nom_complet"), "adresse": siege.get("adresse"),
            "naf": pick.get("activite_principale"), "dirigeants": dirigeants[:2],
            "source": f"https://annuaire-entreprises.data.gouv.fr/entreprise/{pick['siren']}"}


def website_from_email(email):
    domain = (email or "").split("@")[-1].lower()
    if not domain or SHARED_DOMAINS.search(domain + "."):
        return None
    return f"https://{domain}"


def analyse_site(url):
    """Faits vérifiés sur le site (chaque fait garde l'URL de la page lue)."""
    facts = {"site": url}
    r, dt = _get(url)
    if r is None and url.startswith("https://"):
        r, dt = _get("http://" + url[8:])
    if r is None or r.status_code >= 400:
        facts["joignable"] = False
        return facts
    if (r.encoding or "").lower() in ("iso-8859-1", "latin-1") and "charset" not in r.headers.get("content-type", "").lower():
        r.encoding = r.apparent_encoding or "utf-8"  # sans charset annoncé, requests lit en latin-1 : « Ã© » au lieu de « é »
    html = r.text
    low = html.lower()
    facts.update({
        "joignable": True,
        "url_finale": r.url,
        "https": r.url.startswith("https://"),
        "temps_reponse_s": round(dt, 1),
        "mobile": bool(re.search(r'<meta[^>]+name=["\']viewport', low)),
        "titre": (re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I) or [None, ""])[1].strip()[:120],
        "meta_description": any(re.search(r'name\s*=\s*["\']description["\']', m) and
                                re.search(r'content\s*=\s*["\'][^"\']{20,}', m)
                                for m in re.findall(r"<meta\b[^>]*>", low)),
        "formulaire": "<form" in low and ("contact" in low or "message" in low),
        "page_contact": bool(re.search(r'href=["\'][^"\']*contact', low)),
        "mentions_legales": bool(re.search(r"mentions[\s-]*l[ée]gales", low)),
        "confidentialite": bool(re.search(r"confidentialit|donn[ée]es personnelles|rgpd|cookies", low)),
        "wordpress": "wp-content" in low,
        "carte_google": "google.com/maps" in low or "maps.googleapis" in low,
    })
    dom = urlparse(r.url).netloc.lower().removeprefix("www.")
    facts["emails_site"] = sorted({m.lower() for m in EMAIL_RE.findall(html)
                                   if m.lower().split("@")[1].removeprefix("www.") == dom
                                   and not NOREPLY.match(m.lower())})
    years = [int(y) for y in re.findall(r"(?:©|&copy;|copyright)\D{0,12}((?:19|20)\d{2})", low)]
    facts["annee_copyright"] = max(years) if years else None
    return facts


METIERS = {  # code NAF -> métier tel qu'un client le cherche
    "43.22A": "plombier", "43.22B": "chauffagiste", "43.21A": "électricien", "43.32A": "menuisier",
    "43.34Z": "peintre en bâtiment", "43.99C": "maçon", "43.31Z": "plaquiste", "43.91B": "couvreur",
    "56.10A": "restaurant", "56.10C": "restauration rapide", "96.02A": "coiffeur",
    "47.71Z": "boutique de vêtements", "47.76Z": "fleuriste", "56.30Z": "bar", "47.24Z": "boulangerie",
    "96.02B": "institut de beauté", "45.20A": "garage automobile",
    "43.21B": "électricien", "43.29A": "isolation", "43.29B": "artisan du bâtiment", "43.33Z": "carreleur",
    "43.39Z": "peintre en bâtiment", "43.91A": "charpentier", "43.99A": "étanchéité", "43.12A": "terrassier",
    "43.13Z": "terrassier", "43.99B": "artisan du bâtiment", "43.99D": "maçon", "43.32B": "menuisier",
    "43.32C": "agencement", "43.34Z": "peintre en bâtiment", "41.20A": "entreprise de construction",
    "41.20B": "entreprise de construction", "10.71C": "boulangerie", "10.71D": "pâtisserie",
    "47.22Z": "boucherie", "47.23Z": "poissonnerie", "10.13B": "charcuterie", "56.10B": "restaurant",
    "55.10Z": "hôtel", "49.32Z": "taxi", "96.01B": "pressing", "96.04Z": "institut de bien-être",
    "74.20Z": "photographe", "69.20Z": "expert-comptable", "68.31Z": "agence immobilière",
    "86.21Z": "médecin généraliste", "86.23Z": "dentiste", "85.53Z": "auto-école", "81.21Z": "entreprise de nettoyage",
    "81.30Z": "paysagiste", "45.20B": "garage automobile", "95.21Z": "réparation électronique",
    "33.12Z": "réparateur", "16.10A": "scierie", "16.23Z": "charpentier", "31.09B": "meubles sur mesure",
    "25.62A": "mécanique de précision", "25.62B": "mécanique de précision",
}
FREE_MAIL = {"gmail.com", "orange.fr", "outlook.fr", "outlook.com", "hotmail.fr", "hotmail.com", "yahoo.fr",
             "yahoo.com", "free.fr", "wanadoo.fr", "sfr.fr", "laposte.net", "live.fr", "icloud.com"}
PLATFORM_EMAIL = re.compile(r"@(pagesjaunes|societe|pappers|facebook|google|bing|duckduckgo|"
                            r"example|sentry|wix|wordpress|domain|yelp|tripadvisor|thefork|"
                            r"verif|infogreffe|kompass|manageo)\.", re.IGNORECASE)
NOREPLY = re.compile(r"^(no-?reply|ne-pas-repondre|postmaster|webmaster|admin|privacy|dpo|rgpd)@",
                     re.IGNORECASE)


def find_public_email(nom, ville):
    """Email publié par l'entreprise, lu dans les extraits des résultats de recherche (fiche
    Google, annuaire, site). Gardé seulement si l'extrait cite aussi le nom.
    Aucune page d'annuaire n'est parcourue : on ne lit que ce que le moteur affiche."""
    toks = _tokens(nom)
    for q in (f'"{nom}" {ville} email', f"{nom} {ville} contact"):
        for hit in brave_search(q, count=10):
            text = f"{hit.get('title', '')} {hit.get('description', '')}"
            low = text.lower()
            if not toks or sum(t in low for t in toks) < max(1, len(toks) // 2):
                continue
            for m in EMAIL_RE.findall(text):
                m = m.lower().rstrip(".")
                if not PLATFORM_EMAIL.search(m) and not NOREPLY.match(m):
                    return m, hit.get("url", "")
    return None, None


# ----------------------------------------------------------------- Serper.dev (résultats Google Maps)
# Clé SERPER_API_KEY dans .env.serper. Un appel par « métier ville », mis en cache 30 jours au plus
# (cortex.db, table serper_cache) : les notes et nombres d'avis ne sont jamais gardés plus longtemps.
SERPER_URL = "https://google.serper.dev/places"
CACHE_DAYS = 30


def places_key():
    return os.environ.get("SERPER_API_KEY", "").strip()


def _cache_db():
    if os.environ.get("DATABASE_URL", "").strip():
        import cortex
        db = cortex.Store(cortex.DB_PATH).db
    else:
        import sqlite3
        db = sqlite3.connect(Path(__file__).resolve().parent / "cortex.db", timeout=30)
    db.execute("CREATE TABLE IF NOT EXISTS serper_cache (query TEXT PRIMARY KEY, date TEXT, resultats TEXT)")
    db.execute("DELETE FROM serper_cache WHERE date<?",
               (date.fromordinal(date.today().toordinal() - CACHE_DAYS).isoformat(),))
    return db


def _notifier_telegram(sorte, message):
    """Message d'erreur au format ⚠️ (envoi seul vers le chat de JOSY ; ne lit rien)."""
    token, chat = os.environ.get("TG_TOKEN"), os.environ.get("TG_CHAT")
    if not (token and chat):
        return
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=15,
                      json={"chat_id": chat, "text": f"⚠️ Erreur {sorte}. Détails : {message}."})
    except requests.RequestException:
        pass


def serper_search(query):
    """Résultats Google Maps pour « métier ville », dans l'ordre affiché : nom, note, nombre d'avis,
    adresse, site. None si la clé manque ou si l'API échoue (rien n'est alors affirmé).
    Google Places est essayé d'abord s'il est actif (GOOGLE_PLACES_KEY valide) ; refusé, il se désactive pour
    la journée avec un message Telegram et Serper prend le relais."""
    try:
        import source_places
        res = source_places.search(query, _notifier_telegram)
        if res:
            return res
    except Exception:
        pass
    if not places_key():
        return None
    db = _cache_db()
    try:
        row = db.execute("SELECT resultats FROM serper_cache WHERE query=?", (query,)).fetchone()
        if row:
            return json.loads(row[0])
        try:
            r = requests.post(SERPER_URL, timeout=30, json={"q": query, "gl": "fr", "hl": "fr"},
                              headers={"X-API-KEY": places_key(), "Content-Type": "application/json"})
            r.raise_for_status()
            places = r.json().get("places") or []
        except (requests.RequestException, ValueError):
            return None
        res = [{"id": str(p.get("cid") or ""), "nom": p.get("title", ""), "note": p.get("rating"),
                "avis": int(p.get("ratingCount") or 0), "adresse": p.get("address", ""),
                "site": p.get("website", ""), "categorie": p.get("category", "")} for p in places]
        db.execute("INSERT INTO serper_cache(query, date, resultats) VALUES(?,?,?) "
                   "ON CONFLICT(query) DO UPDATE SET date=excluded.date, resultats=excluded.resultats",
                   (query, date.today().isoformat(), json.dumps(res, ensure_ascii=False)))
        db.commit()
        return res
    finally:
        db.close()


places_search = serper_search


def _host(url):
    return urlparse(url if "//" in (url or "") else "//" + (url or "")).netloc.lower().removeprefix("www.")


def metier_google(nom, ville):
    """Métier tel que Google Maps le nomme (catégorie de la fiche dont le nom correspond), pour toute
    activité. None si la fiche n'est pas trouvée sans ambiguïté : rien n'est alors affirmé."""
    if not places_key() or not nom or not ville:
        return None
    toks = _tokens(nom)
    for p in (serper_search(f"{nom} {ville}") or [])[:3]:
        hit = sum(t in p["nom"].lower() for t in toks)
        if toks and (hit == len(toks) or (len(toks) > 2 and hit >= 2)) and p.get("categorie"):
            return p["categorie"].lower()
    return None


def google_comparison(metier, ville, nom, site=None):
    """Position et avis du prospect face aux entreprises affichées par Google Maps pour
    « métier ville ». Prudent : une fiche n'est reconnue que par le site web ou par le nom ;
    en cas de doute (nom partiellement ressemblant), rien n'est affirmé."""
    if not metier or not ville:
        return None
    query = f"{metier} {ville}"
    res = serper_search(query)
    if not res:
        return None
    # Homonymes de communes : on ne garde que le département majoritaire (code postal de l'adresse)
    deps = [m.group(1) for p in res for m in [re.search(r"\b(97\d|20[12]|\d{2})\d{2,3}\b", p["adresse"])] if m]
    if deps:
        majo = max(set(deps), key=deps.count)
        res = [p for p in res if not re.search(r"\b\d{5}\b", p["adresse"])
               or re.search(rf"\b{majo}\d{{2,3}}\b", p["adresse"])]
    toks = _tokens(nom)
    host = _host(site) if site else ""
    rank, doubt = None, False
    for i, p in enumerate(res, 1):
        low = p["nom"].lower()
        hit = sum(t in low for t in toks)
        name_match = bool(toks) and (hit == len(toks) or (len(toks) > 2 and hit >= 2))
        if (host and p.get("site") and _host(p["site"]) == host) or name_match:
            rank = i
            break
        if hit:
            doubt = True  # ressemblance partielle : homonyme possible
    if rank is None and doubt:
        return None
    others = [p for i, p in enumerate(res, 1) if i != rank]
    avg = round(sum(p["avis"] for p in others) / len(others)) if others else None
    return {"requete": query, "rang": rank, "total": len(res), "premier": res[0],
            "prospect": res[rank - 1] if rank else None, "moyenne_avis": avg,
            "nb_autres": len(others), "source": "Google Maps (Serper)"}


def local_visibility(metier, ville, nom, site=None):
    """Recherche « métier ville » : l'entreprise apparaît-elle dans les 10 premiers résultats ?"""
    if not metier or not ville:
        return None
    hits = brave_search(f"{metier} {ville}", count=10)
    if not hits:
        return None  # recherche indisponible : non vérifié
    toks = _tokens(nom)
    host = urlparse(site).netloc.lower().removeprefix("www.") if site else ""
    for i, h in enumerate(hits, 1):
        blob = f"{h.get('url', '')} {h.get('title', '')}".lower()
        if (host and host in blob) or (toks and all(t in blob for t in toks[:2])):
            return {"requete": f"{metier} {ville}", "rang": i}
    # Concurrents réellement affichés en tête : sites d'entreprises (pas d'annuaires), dans l'ordre.
    concurrents, seen = [], set()
    for h in hits:
        dom = urlparse(h.get("url", "")).netloc.lower().removeprefix("www.")
        if not dom or DIRECTORIES.search(dom) or dom in seen:
            continue
        name = re.split(r"\s[-|–—:·]\s|\s\|\s", h.get("title", ""))[0].strip()
        # Un vrai nom d'entreprise : pas seulement « métier + ville » (titres de pages SEO génériques).
        generic = {t.rstrip("s") for t in _tokens(f"{metier} {ville}")} | {
            "artisan", "entreprise", "professionnel", "gastronomique", "traditionnel", "pas", "cher",
            "urgence", "depannage", "dépannage", "renovation", "rénovation", "services", "travaux"}
        distinct = [t for t in _tokens(name) if t.rstrip("s") not in generic]
        if (3 <= len(name) <= 50 and distinct and name.lower() not in {c["nom"].lower() for c in concurrents}
                and not re.search(r"\b(top|meilleur|liste|annuaire|devis|avis|\d+)\b", name, re.I)):
            seen.add(dom)
            concurrents.append({"nom": name, "site": dom})
    return {"requete": f"{metier} {ville}", "rang": None, "resultats": len(hits),
            "concurrents": concurrents[:3]}


# Manque constaté -> (phrase factuelle citée dans l'email, service du catalogue)
def gaps_and_services(f):
    gaps = []
    # Règle de JOSY : chaque email porte UN chiffre vérifié qui montre une perte concrète.
    # Option B (Google Places, prioritaire) : chiffres renvoyés par Google Maps.
    g = f.get("google_maps")
    if g and g.get("premier"):
        first, me = g["premier"], g.get("prospect")
        if not me and first["avis"] and g["total"] >= 5:
            gaps.append((f"sur Google Maps, le 1er résultat pour « {g['requete']} » est {first['nom']}, "
                         f"avec {first['avis']} avis, et votre entreprise n'apparaît pas dans les "
                         f"{g['total']} premiers résultats", "concurrents"))
        elif me and g.get("moyenne_avis") and g.get("nb_autres", 0) >= 3 and me["avis"] * 2 <= g["moyenne_avis"]:
            gaps.append((f"votre fiche Google compte {me['avis']} avis, alors que la moyenne locale est de "
                         f"{g['moyenne_avis']} (calculée sur les {g['nb_autres']} autres entreprises affichées "
                         f"pour « {g['requete']} »)", "avis"))
    # Seuls les arguments Google (Serper) sont autorisés (décision de JOSY, 14/10/2026) : le « site daté »
    # est interdit. Sans fait Google vérifié, il n'y a pas d'email.
    services, seen = [], set()
    for _, s in gaps:
        if s not in seen:
            seen.add(s)
            services.append(s)
    return [g for g, _ in gaps], services[:3], [list(x) for x in gaps]
    # (les constats sans chiffre ci-dessous ne sont plus utilisés pour ouvrir un email)
    # « Aucun site » n'est jamais affirmé : deux recherches identiques ont donné des résultats
    # différents lors des tests (site trouvé puis non trouvé).
    # « Pas de site » ou « site injoignable » ne sont jamais affirmés : un site peut exister
    # sous un autre domaine ou bloquer les robots. Sans page lue, aucun constat.
    if f.get("joignable"):
        host = urlparse(f["url_finale"]).netloc
        if not f["mobile"]:
            gaps.append((f"votre site {host} n'a pas de version adaptée au mobile", "site"))
        if not f["https"]:
            gaps.append((f"votre site {host} n'est pas sécurisé (pas de HTTPS)", "site"))
        if f.get("annee_copyright") and f["annee_copyright"] <= date.today().year - 3:
            gaps.append((f"le pied de page de votre site affiche encore {f['annee_copyright']}", "site"))
        # Seuls les constats fiables sont cités (pas de temps de chargement, mesuré depuis le
        # PC de JOSY ; pas de formulaire ou de page contact, souvent chargés en JavaScript).
        if not f["meta_description"]:
            gaps.append((f"la page d'accueil du site {host} n'a pas de description pour les résultats "
                         "Google", "seo"))
        # Absences vérifiées deux fois : lien absent de l'accueil ET adresse usuelle introuvable.
        if not f["mentions_legales"] and not f.get("page_mentions"):
            gaps.append((f"je n'ai pas trouvé de mentions légales sur le site {host}", "diag"))
        elif not f["confidentialite"] and not f.get("page_confidentialite"):
            gaps.append((f"je n'ai pas trouvé de politique de confidentialité (RGPD) sur le site "
                         f"{host}", "diag"))
        if not f["page_contact"] and not f.get("page_contact_url") and not f["formulaire"]:
            gaps.append((f"je n'ai pas trouvé de page contact sur le site {host}", "auto"))
    g = f.get("google")
    if g and g.get("trouvee") and g.get("avis") is not None:
        n = int(g["avis"])
        if n < 10:
            gaps.append((f"votre fiche Google ne compte que {n} avis", "gbp"))
        elif g.get("note") and float(g["note"]) < 4:
            gaps.append((f"votre fiche Google affiche une note de "
                         f"{str(g['note']).replace('.', ',')} sur 5", "gbp"))
    services, seen = [], set()
    for _, s in gaps:
        if s not in seen:
            seen.add(s)
            services.append(s)
    return [g for g, _ in gaps], services[:3], [list(x) for x in gaps]


def audit_prospect(row):
    """row : nom, secteur, ville, email, (siren). Renvoie l'analyse complète."""
    nom, ville = row["nom"], row.get("ville", "")
    ident = find_company(nom, ville, row.get("siren", ""))
    # 1. Site : déduit de l'email, sinon cherché avec Brave (page qui cite le nom).
    site = row.get("site") or website_from_email(row.get("email")) or find_website(nom, ville)
    facts = analyse_site(site) if site else {"site": None}
    if facts.get("joignable"):
        root = f"{urlparse(facts['url_finale']).scheme}://{urlparse(facts['url_finale']).netloc}"
        # 4. Contact et 5. RGPD / mentions : adresses usuelles testées avant d'affirmer une absence.
        if not facts["mentions_legales"]:
            facts["page_mentions"] = page_exists(root, ["mentions-legales", "mentions-legales/",
                                                        "mentions_legales", "legal"])
        if not facts["confidentialite"]:
            facts["page_confidentialite"] = page_exists(root, [
                "politique-de-confidentialite", "politique-de-confidentialite/", "confidentialite",
                "privacy-policy"])
        if not facts["page_contact"]:
            facts["page_contact_url"] = page_exists(root, ["contact", "contact/", "nous-contacter",
                                                           "contactez-nous"])
    facts["site_cherche"] = bool(not site and search_available())
    # Email : celui de la feuille, sinon un email publié trouvé dans les résultats de recherche.
    email, email_source = row.get("email") or None, row.get("source") or None
    if not email and facts.get("emails_site"):
        email, email_source = facts["emails_site"][0], facts.get("url_finale")
    if not email and search_available():
        email, email_source = find_public_email(nom, ville)
        src_host = urlparse(email_source or "").netloc.lower()
        email_dom = (email or "").split("@")[-1].lower().removeprefix("www.")
        if (email_source and src_host and not DIRECTORIES.search(src_host) and not facts.get("joignable")
                and src_host.removeprefix("www.") == email_dom):  # même domaine que l'email : leur site
            # L'email vient d'une page hors annuaire : c'est probablement leur site. On l'analyse
            # et on n'affirme surtout pas « aucun site ».
            facts = analyse_site(f"{urlparse(email_source).scheme}://{urlparse(email_source).netloc}")
            facts["site_cherche"] = False
    # Visibilité locale : l'entreprise sort-elle sur « métier + ville » ?
    metier = METIERS.get(row.get("naf") or (ident or {}).get("naf") or "") or metier_google(nom, ville)
    facts["google_maps"] = google_comparison(
        metier, ville, nom, facts.get("url_finale") or site
        or (f"https://{email.split('@')[-1]}" if email and not PLATFORM_EMAIL.search(email)
            and email.split("@")[-1] not in FREE_MAIL else None)) if places_key() else None
    facts["visibilite"] = local_visibility(metier, ville, nom, facts.get("url_finale")) \
        if search_available() and not facts["google_maps"] else None
    # 2. Fiche Google (si Brave la renvoie).
    facts["google"] = google_presence(nom, ville) if brave_key() else None
    gaps, services, detail = gaps_and_services(facts)
    non_verifie = ["téléphone direct"]
    if not facts["google"]:
        non_verifie[:0] = ["fiche Google Business", "avis Google"]
    if not facts.get("joignable"):
        non_verifie.insert(0, "site internet")
    if not email:  # personne à qui écrire : pas de prospect
        gaps, services, detail = [], [], []
    return {"entreprise": {"nom": nom, "secteur": row.get("secteur", ""), "ville": ville,
                           "email": email or "", "email_source": email_source or "",
                           "metier": metier, "officiel": ident},
            "site": facts, "manques": gaps, "services": services, "manques_detail": detail,
            "non_verifie": non_verifie,
            "recherche": "brave" if brave_key() else ("duckduckgo" if ddg_available() else "aucune"),
            "date": date.today().isoformat()}


# L'email n'est plus un gabarit : il est rédigé par prompts_audit.py à partir du dossier d'audit
# (dossier_audit_manager.py), sans aucun prix, puis contrôlé par regles_absolues.py.

# Pourquoi c'est un problème : 2 phrases fixes par type de manque (aucun chiffre inventé).
WHY = {
    "concurrents": ("Les entreprises affichées en tête sont celles que contactent les clients qui cherchent "
                    "votre métier près de chez eux. Chaque demande qu'elles reçoivent est une demande que vous ne voyez pas."),
    "avis": ("Entre deux professionnels, un client choisit presque toujours celui qui a le plus "
             "d'avis. Chaque avis manquant fait pencher la balance vers un concurrent."),
    "site_date": ("Un client qui arrive aujourd'hui sur un site qui affiche une année ancienne doute "
                  "que l'entreprise soit toujours active. Beaucoup passent au concurrent suivant."),
    "gbp": ("Quand un client cherche un professionnel près de chez lui, il contacte en général "
            "ceux qu'il voit en premier. Ne pas y figurer, c'est laisser ces demandes à d'autres."),
    "seo": ("Cette description est le texte que les moteurs de recherche affichent sous votre nom. "
            "Sans elle, ils en choisissent un au hasard, souvent peu engageant."),
    "site": ("Un site qui paraît daté ou mal adapté au téléphone fait douter les visiteurs. "
             "Beaucoup repartent avant même de vous écrire."),
    "diag": ("Ces informations sont obligatoires pour un site professionnel en France. Leur absence "
             "expose à une sanction et inquiète les clients attentifs à leurs données."),
    "auto": ("Sans moyen simple de vous écrire depuis votre site, une partie des visiteurs abandonne. "
             "Ces demandes se perdent sans que vous le sachiez."),
}
