"""Module OSINT du Cortex : données publiques et professionnelles d'une entreprise, pour enrichir un audit.

Vetos du judiciaire (JOSY, 19/10/2026), appliqués dans le code :
  - aucun scan de vulnérabilités (ni Nuclei ni autre scanner) : seule la détection de technologies ;
  - aucun email personnel : seules les adresses génériques du domaine du site (contact@, info@, accueil@,
    direction@, bonjour@, hello@, admin@), jamais prenom.nom@ ni une adresse contenant un chiffre ;
  - aucune recherche sur une personne physique : Sherlock ne reçoit qu'un nom d'entreprise ou de marque ;
  - robots.txt lu avant tout crawl ; s'il interdit, rien n'est lu ;
  - Google Maps : exclu de ce module (aucun scraping). Position et avis Google Maps viennent de Serper (audit.py) ;
  - chaque appel est consigné dans audit.db (table audit_log, lignes chaînées par sha256) ;
  - les dépendances facultatives (python-wappalyzer, sherlock-project, beautifulsoup4) ne sont jamais installées
    par le Cortex : install_osint.bat les installe après accord de JOSY. Absentes, la fonction concernée renvoie
    une erreur ou se replie sur la bibliothèque standard, et l'audit continue.

Aucune fonction ne lève d'exception : en cas d'erreur, {"status": "erreur", "detail": ...}.
"""

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests

BASE_DIR = Path(__file__).resolve().parent
AUDIT_DB = Path(os.environ.get("CORTEX_AUDIT_DB", "").strip() or BASE_DIR / "audit.db")
UA = "JOSY-EI-AuditBot/1.0 (contact@josyei.com)"
TIMEOUT = 30
COMPANY_API = "https://recherche-entreprises.api.gouv.fr/search"

GENERIQUES = ("contact", "info", "accueil", "direction", "bonjour", "hello", "admin")
EMAIL_RE = re.compile(r"(?<![\w.+-])[a-zA-Z][\w.+-]*@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}(?![\w])")
PAGES_EMAILS = ("", "contact", "nous-contacter", "mentions-legales", "a-propos")
MAX_PAGES = 5
DELAI_PAGES_S = 1.0
SHERLOCK_TIMEOUT_S = 120

# Mots qui signalent une entreprise ou une marque, et prénoms courants (refus d'un « Prénom Nom »).
MOTS_ENTREPRISE = {
    "sarl", "sas", "sasu", "eurl", "sa", "sci", "scp", "selarl", "snc", "ei", "earl", "gaec", "ets", "groupe",
    "le", "la", "les", "l", "au", "aux", "du", "de", "des", "et", "chez", "atelier", "agence", "cabinet", "garage",
    "restaurant", "boulangerie", "patisserie", "boucherie", "cafe", "bar", "hotel", "salon", "institut",
    "pharmacie", "plomberie", "electricite", "menuiserie", "maconnerie", "transports", "studio", "boutique",
    "maison", "domaine", "ferme", "auto", "services", "conseil", "immobilier", "fleurs", "bistrot", "pizzeria",
    "taxi", "ambulances", "batiment", "renovation", "construction", "nettoyage", "coiffure", "beaute", "optique",
    "test", "demo", "exemple",
}
PRENOMS = {
    "jean", "pierre", "marie", "michel", "philippe", "alain", "nicolas", "christophe", "patrick", "laurent",
    "david", "eric", "frederic", "stephane", "sebastien", "julien", "thomas", "olivier", "francois", "daniel",
    "nathalie", "isabelle", "sylvie", "catherine", "sophie", "christine", "valerie", "sandrine", "julie", "anne",
    "paul", "jacques", "louis", "lucas", "hugo", "emma", "lea", "chloe", "camille", "manon", "sarah", "laura",
}


def _now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _plat(texte):
    t = unicodedata.normalize("NFKD", str(texte or ""))
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def journal(fonction, cible, statut, detail=None, db_path=None):
    """Trace de chaque collecte (I7) : fonction, cible (entreprise ou domaine), statut. Aucun email collecté."""
    try:
        db = sqlite3.connect(db_path or AUDIT_DB, timeout=30)
        db.execute("CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, "
                   "fonction TEXT, cible TEXT, statut TEXT, detail TEXT, prev_hash TEXT, hash TEXT)")
        row = db.execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
        prev, ts = (row[0] if row else "GENESIS"), _now()
        det = json.dumps(detail or {}, ensure_ascii=False, sort_keys=True)[:1000]
        digest = hashlib.sha256(f"{prev}|{ts}|{fonction}|{cible}|{statut}|{det}".encode()).hexdigest()
        db.execute("INSERT INTO audit_log(ts, fonction, cible, statut, detail, prev_hash, hash) VALUES(?,?,?,?,?,?,?)",
                   (ts, fonction, str(cible)[:200], statut, det, prev, digest))
        db.commit()
        db.close()
    except sqlite3.Error:
        pass


def _erreur(fonction, cible, exc):
    detail = f"{type(exc).__name__}: {exc}"[:300] if isinstance(exc, Exception) else str(exc)[:300]
    journal(fonction, cible, "erreur", {"detail": detail})
    return {"status": "erreur", "detail": detail}


# ----------------------------------------------------------------- 1. données légales (annuaire officiel)
def get_legal_data(siren_or_name: str) -> dict:
    """Fiche publique de l'annuaire officiel (recherche-entreprises.api.gouv.fr, sans clé)."""
    try:
        q = str(siren_or_name or "").strip()
        if not q:
            return {"status": "erreur", "detail": "nom ou SIREN vide"}
        r = requests.get(COMPANY_API, params={"q": q, "per_page": 5}, timeout=TIMEOUT, headers={"User-Agent": UA})
        r.raise_for_status()
        res = r.json().get("results") or []
        if not res:
            journal("get_legal_data", q, "aucun_resultat")
            return {"status": "aucun_resultat"}
        e = res[0]
        siege = e.get("siege") or {}
        dirigeants = [{"nom": " ".join(x for x in ((d.get("prenoms") or "").split(" ")[0].title(),
                                                     (d.get("nom") or "").upper()) if x) or d.get("denomination", ""),
                       "qualite": d.get("qualite") or ""}
                      for d in (e.get("dirigeants") or [])[:3]]
        out = {"status": "ok", "raison_sociale": e.get("nom_complet") or e.get("nom_raison_sociale"),
               "siren": e.get("siren"), "siren_siege": siege.get("siret"), "activite": e.get("activite_principale"),
               "adresse": siege.get("adresse"), "dirigeants": dirigeants, "date_creation": e.get("date_creation"),
               "effectifs": e.get("tranche_effectif_salarie"),
               "source": f"https://annuaire-entreprises.data.gouv.fr/entreprise/{e.get('siren')}"}
        journal("get_legal_data", q, "ok", {"siren": e.get("siren"), "alternatives": [x.get("siren") for x in res[1:]]})
        return out
    except Exception as exc:  # noqa: BLE001
        return _erreur("get_legal_data", siren_or_name, exc)


# ----------------------------------------------------------------- 2. technologies du site (aucun scan)
def scan_technologies(url: str) -> dict:
    """Technologies visibles (CMS, frameworks, analytics) par python-wappalyzer. Aucune sonde de vulnérabilité."""
    try:
        if not url:
            return {"status": "erreur", "detail": "aucun site"}
        try:
            from Wappalyzer import Wappalyzer, WebPage
        except ImportError:
            journal("scan_technologies", urlparse(url).netloc, "dependance_absente")
            return {"status": "erreur", "detail": "python-wappalyzer non installé (install_osint.bat)"}
        page = WebPage.new_from_url(url, timeout=TIMEOUT)
        techs = Wappalyzer.latest().analyze_with_versions_and_categories(page)
        liste = [{"nom": nom, "categories": v.get("categories", []), "versions": v.get("versions", [])}
                 for nom, v in sorted(techs.items())]
        journal("scan_technologies", urlparse(url).netloc, "ok", {"nb": len(liste)})
        return {"status": "ok", "technologies": liste, "https": url.startswith("https://")}
    except Exception as exc:  # noqa: BLE001
        return _erreur("scan_technologies", url, exc)


# ----------------------------------------------------------------- 3. Google Maps : exclu (Serper)
def google_maps_exclu(query: str = "") -> dict:
    """Aucun scraping de Google Maps : la position et les avis viennent de Serper (audit.google_comparison)."""
    return {"status": "exclu", "detail": "Google Maps non scrapé ; données fournies par Serper"}


# ----------------------------------------------------------------- 4. réseaux sociaux de la marque
def ressemble_a_une_personne(nom):
    """True si le nom ressemble à « Prénom Nom » (ou contient un prénom courant sans mot d'entreprise)."""
    mots = re.findall(r"[a-z]+", _plat(nom))
    if not mots or any(m in MOTS_ENTREPRISE for m in mots):
        return False
    if mots[0] in PRENOMS:
        return True
    brut = str(nom or "").split()
    return 2 <= len(brut) <= 3 and all(w[:1].isupper() and w[1:].islower() and w.isalpha() for w in brut)


def identifiant_marque(nom):
    return re.sub(r"[^a-z0-9]", "", _plat(nom))[:30]


def find_social_profiles(brand_name: str, runner=None) -> dict:
    """Plateformes où l'identifiant de la marque existe (Sherlock). Jamais un nom de personne physique."""
    try:
        if ressemble_a_une_personne(brand_name):
            journal("find_social_profiles", "refuse", "personne_physique")
            return {"status": "refuse", "detail": "nom de personne physique : recherche interdite"}
        handle = identifiant_marque(brand_name)
        if len(handle) < 3:
            return {"status": "erreur", "detail": "nom de marque trop court"}
        if runner is None:
            exe = shutil.which("sherlock")
            cmd = [exe] if exe else [sys.executable, "-m", "sherlock_project"]
            if not exe:
                import importlib.util
                if not importlib.util.find_spec("sherlock_project"):
                    journal("find_social_profiles", handle, "dependance_absente")
                    return {"status": "erreur", "detail": "sherlock-project non installé (install_osint.bat)"}
            runner = lambda args: subprocess.run(cmd + args, capture_output=True, text=True,  # noqa: E731
                                                 timeout=SHERLOCK_TIMEOUT_S)
        proc = runner([handle, "--print-found", "--no-txt", "--timeout", "10"])
        plateformes = [{"plateforme": m.group(1).strip(), "url": m.group(2).strip()}
                       for m in re.finditer(r"^\[\+\]\s*([^:]+):\s*(\S+)", proc.stdout or "", re.M)]
        journal("find_social_profiles", handle, "ok", {"nb": len(plateformes)})
        return {"status": "ok", "identifiant": handle, "plateformes": plateformes}
    except subprocess.TimeoutExpired as exc:
        return _erreur("find_social_profiles", brand_name, exc)
    except Exception as exc:  # noqa: BLE001
        return _erreur("find_social_profiles", brand_name, exc)


# ----------------------------------------------------------------- 5. emails génériques du site
class _Liens(HTMLParser):
    def __init__(self):
        super().__init__()
        self.mailtos, self.texte = [], []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k == "href" and v and v.lower().startswith("mailto:"):
                self.mailtos.append(v[7:].split("?")[0])

    def handle_data(self, data):
        self.texte.append(data)


def _extraire(html_texte):
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_texte, "html.parser")
        mailtos = [a["href"][7:].split("?")[0] for a in soup.find_all("a", href=True)
                   if a["href"].lower().startswith("mailto:")]
        return mailtos + EMAIL_RE.findall(soup.get_text(" "))
    except ImportError:
        p = _Liens()
        p.feed(html_texte)
        return p.mailtos + EMAIL_RE.findall(" ".join(p.texte))


def email_generique(adresse, domaine=None):
    """contact@ / info@ / ... du domaine du site ; jamais prenom.nom@ ni une adresse avec un chiffre."""
    a = str(adresse or "").strip().lower().rstrip(".")
    if not EMAIL_RE.fullmatch(a) or re.search(r"\d", a):
        return False
    local, dom = a.split("@", 1)
    if local not in GENERIQUES:
        return False
    return not domaine or dom.removeprefix("www.") == domaine.removeprefix("www.")


def scrape_website_emails(url: str, getter=None, pause=time.sleep) -> dict:
    """Emails génériques publiés sur le site (5 pages au plus, 1 s entre deux pages), après robots.txt."""
    try:
        if not url:
            return {"status": "erreur", "detail": "aucun site"}
        racine = f"{urlparse(url).scheme or 'https'}://{urlparse(url).netloc or urlparse('//' + url).netloc}"
        domaine = urlparse(racine).netloc.lower()
        get = getter or (lambda u: requests.get(u, timeout=TIMEOUT, headers={"User-Agent": UA}))
        rp = robotparser.RobotFileParser()
        try:
            r = get(racine + "/robots.txt")
            rp.parse((r.text if getattr(r, "status_code", 404) == 200 else "").splitlines())
        except Exception:  # noqa: BLE001  robots.txt illisible : règle standard, crawl permis
            rp.parse([])
        if not rp.can_fetch(UA, racine + "/"):
            journal("scrape_website_emails", domaine, "robots_txt_interdit")
            return {"status": "robots_txt_interdit"}
        trouves, lues, rejetees = [], 0, 0
        for i, chemin in enumerate(PAGES_EMAILS[:MAX_PAGES]):
            page_url = urljoin(racine + "/", chemin)
            if not rp.can_fetch(UA, page_url):
                continue
            if i:
                pause(DELAI_PAGES_S)
            try:
                r = get(page_url)
            except Exception:  # noqa: BLE001
                continue
            if getattr(r, "status_code", 0) != 200:
                continue
            lues += 1
            for a in _extraire(r.text):
                a = a.strip().lower().rstrip(".")
                if email_generique(a, domaine):
                    if a not in trouves:
                        trouves.append(a)
                else:
                    rejetees += 1  # adresse nominative, d'un autre domaine ou avec chiffre : jamais gardée
        journal("scrape_website_emails", domaine, "ok", {"pages": lues, "generiques": len(trouves),
                                                         "ecartees": rejetees})
        return {"status": "ok", "emails": trouves, "pages_lues": lues}
    except Exception as exc:  # noqa: BLE001
        return _erreur("scrape_website_emails", url, exc)


# ----------------------------------------------------------------- 6. orchestration
def run_full_osint_audit(company_name: str, website_url: str, siren: str = "", outils=None) -> dict:
    """Les fonctions ci-dessus dans l'ordre ; une erreur n'arrête pas les suivantes. `outils` : simulations (tests)."""
    o = {"legal": get_legal_data, "technologies": scan_technologies, "social": find_social_profiles,
         "emails": scrape_website_emails, **(outils or {})}
    res = {"legal_data": {}, "technologies": {}, "google_maps": google_maps_exclu(),
           "social_profiles": {}, "emails_pro": [], "erreurs": [], "timestamp": _now()}
    for cle, appel in (("legal_data", lambda: o["legal"](siren or company_name)),
                       ("technologies", lambda: o["technologies"](website_url)),
                       ("social_profiles", lambda: o["social"](company_name)),
                       ("emails", lambda: o["emails"](website_url))):
        try:
            r = appel()
        except Exception as exc:  # noqa: BLE001
            r = {"status": "erreur", "detail": f"{type(exc).__name__}: {exc}"[:300]}
        if r.get("status") not in ("ok", "aucun_resultat"):
            res["erreurs"].append({"etape": cle, "status": r.get("status"), "detail": r.get("detail", "")})
        if cle == "emails":
            res["emails_pro"] = r.get("emails", [])
        else:
            res[cle] = r
    journal("run_full_osint_audit", company_name, "ok", {"erreurs": len(res["erreurs"])})
    return res
