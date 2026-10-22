#!/usr/bin/env python3
"""Le Cortex — agent autonome supervisé de JOSY EI.

Une exécution = un cycle (lancé toutes les 15 min par GitHub Actions) :
  1. lit les réponses Telegram (/valider, /refuser, /stop, /reprise, /etat...)
  2. applique les timeouts (R2 = 2 h, R3 = 24 h -> refus automatique)
  3. lit les flux RSS, analyse les nouveautés avec le modèle choisi (LLM_PROVIDER)
  4. fait contrôler chaque proposition par le pouvoir judiciaire
  5. soumet les actions R2/R3 à JOSY sur Telegram, notifie les R1

Séparation des pouvoirs (I12) :
  - LÉGISLATIF : AGENTS.md + constantes ci-dessous (modifiables seulement par commit)
  - EXÉCUTIF   : Telegram, llm_chat, fonctions fetch/dispatch/execute
  - JUDICIAIRE : classe Judiciaire (contrôle déterministe, dernier mot)

Secrets : uniquement via variables d'environnement (TG_TOKEN, TG_CHAT, clé du modèle si hébergé),
chargées depuis le fichier .env local s'il existe (python-dotenv).
"""

import csv
import hashlib
import html
import json
import os
import re
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests

# Connexion persistante : sur ce PC, chaque nouvelle connexion HTTPS coûte 5 à 11 s (mesuré le 15/10/2026),
# alors qu'un appel sur une connexion déjà ouverte répond en 0,15 à 0,8 s. Un seul objet Session réutilise
# les connexions de Groq et de Telegram.
HTTP = requests.Session()

BASE_DIR = Path(__file__).resolve().parent

try:  # en local, les secrets viennent du fichier .env à côté du script
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
    load_dotenv(BASE_DIR / ".env.serper")  # clé Serper.dev, hors du dépôt
except ImportError:
    pass

try:
    from zoneinfo import ZoneInfo
    PARIS = ZoneInfo("Europe/Paris")
except Exception:  # tzdata absent : on reste en UTC
    PARIS = timezone.utc

# --------------------------------------------------------------------------
# Configuration (secrets : environnement uniquement, jamais dans le code)
# --------------------------------------------------------------------------
TG_TOKEN = os.environ.get("TG_TOKEN", "").strip()
TG_CHAT = os.environ.get("TG_CHAT", "").strip()
DB_PATH = os.environ.get("CORTEX_DB", "").strip() or str(BASE_DIR / "cortex.db")
AGENTS_PATH = BASE_DIR / "AGENTS.md"

# Mémoire du Cortex (bibliothèque validée par JOSY) : index FTS5 en lecture seule.
MEMOIRE_DB = BASE_DIR / "memoire" / "memoire.db"
sys.path.insert(0, str(MEMOIRE_DB.parent / "outils"))
try:
    from memoire import Memoire, build as build_memoire
except ImportError:
    Memoire = build_memoire = None
MEMOIRE_MAX_CHARS = 6000


def open_memoire():
    try:
        return Memoire(MEMOIRE_DB) if Memoire and MEMOIRE_DB.exists() else None
    except Exception:
        return None


def email_hash(email):
    return hashlib.sha256((email or "").strip().lower().encode()).hexdigest()

# --------------------------------------------------------------------------
# LÉGISLATIF — règles fixées par JOSY (I13 : modifiées uniquement par commit)
# --------------------------------------------------------------------------
FEEDS = {
    "Frandroid": "https://www.frandroid.com/feed",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    # L'ancien flux Usine Digitale IA renvoie 403 ; remplacé par Le Monde Informatique IA.
    "Le Monde Informatique IA": "https://www.lemondeinformatique.fr/flux-rss/thematique/intelligence-artificielle/rss.xml",
    # Google Actualités (flux RSS publics, pas de lecture des pages de résultats Google)
    "Google Actualités IA PME": "https://news.google.com/rss/search?q=intelligence+artificielle+PME&hl=fr&gl=FR&ceid=FR:fr",
    "Google Actualités RGPD cyber": "https://news.google.com/rss/search?q=RGPD+OR+cybers%C3%A9curit%C3%A9+entreprises&hl=fr&gl=FR&ceid=FR:fr",
    # Sources officielles
    "CNIL": "https://www.cnil.fr/fr/rss.xml",
    "CERT-FR (ANSSI)": "https://www.cert.ssi.gouv.fr/feed/",
}
# Fournisseur du modèle de langage, choisi dans .env (LLM_PROVIDER).
# ollama : local, gratuit, open source, données sur le PC ; les autres sont hébergés.
LLM_PROVIDERS = {
    "ollama": {"url": "http://localhost:11434/api/chat", "model": "qwen2.5:3b",
               "key_env": None, "timeout": 1500, "articles": 6},
    "groq": {"url": "https://api.groq.com/openai/v1/chat/completions",
             "model": "openai/gpt-oss-120b", "key_env": "GROQ_API_KEY",
             "timeout": 90, "articles": 15},
    "mistral": {"url": "https://api.mistral.ai/v1/chat/completions",
                "model": "mistral-small-latest", "key_env": "MISTRAL_API_KEY",
                "timeout": 90, "articles": 15},
}


def _provider(name, primary=False):
    name = (name or "").strip().lower()
    if name not in LLM_PROVIDERS:
        return None
    cfg = dict(LLM_PROVIDERS[name], name=name)
    if primary:  # LLM_URL / LLM_MODEL ne surchargent que le fournisseur principal
        cfg["url"] = os.environ.get("LLM_URL", "").strip() or cfg["url"]
        cfg["model"] = os.environ.get("LLM_MODEL", "").strip() or cfg["model"]
    cfg["key"] = os.environ.get(cfg["key_env"], "").strip() if cfg["key_env"] else ""
    if cfg["key_env"] and not cfg["key"]:
        return None  # fournisseur hébergé sans clé : inutilisable
    return cfg


# Principal, puis repli automatique (LLM_FALLBACK) si le principal échoue.
LLM_CHAIN = [p for p in (_provider(os.environ.get("LLM_PROVIDER", "ollama"), primary=True),
                         _provider(os.environ.get("LLM_FALLBACK", ""))) if p]
# Repli automatique entre modèles Groq : gpt-oss-120b, puis gpt-oss-20b, puis qwen3.8-27b (décision de JOSY,
# 14/10/2026), avant le repli local éventuel ; si tous échouent, alerte Telegram sans rien inventer.
_groq = next((p for p in LLM_CHAIN if p["name"] == "groq"), None)
if _groq:
    _pos = LLM_CHAIN.index(_groq) + 1
    for _model in ("openai/gpt-oss-20b", "qwen/qwen3.8-27b"):
        LLM_CHAIN.insert(_pos, dict(_groq, model=_model))
        _pos += 1
_llm = LLM_CHAIN[0] if LLM_CHAIN else dict(LLM_PROVIDERS["ollama"], name="aucun", key="")
LLM_PROVIDER = _llm["name"]
LLM_MODEL = _llm["model"]

MISSIONS = {"M1_Prospection", "M2_Visibilite", "M3_Relation_Client",
            "M4_Monetisation", "M5_Veille"}
RISK_ORDER = ["R0", "R1", "R2", "R3"]
RISK_BY_ACTION = {  # I7 : niveau minimal imposé ; tout type inconnu = R3
    "analyse": "R0", "note_veille": "R0",
    "google_post": "R1", "article_blog": "R1", "publication": "R1",
    "cold_email": "R2", "premier_contact": "R2", "relance": "R2",
    "amelioration_regle": "R2",
    "devis": "R3", "proposition_commerciale": "R3", "contrat": "R3",
    "paiement": "R3",
    "proposition_rdv": "R2",
    "diagnostic": "R2",
    "reponse": "R2",
}
SENDABLE_ACTIONS = {"cold_email", "relance", "proposition_rdv", "diagnostic", "reponse"}  # vente.py
TIMEOUT_HOURS = {"R0": 0, "R1": 0, "R2": 2, "R3": 24}
EMAIL_ACTIONS = {"cold_email", "premier_contact", "relance"}

# Prospection (M1) : cibles réelles uniquement, tirées de la feuille « Cortex - Suivi cabinets »
# exportée dans prospects.csv. Le texte vient des gabarits ci-dessous (vente/emails-lot-1.md),
# jamais du modèle : aucune offre, aucun prix, aucune promesse inventés.
PROSPECTS_PATH = BASE_DIR / "prospects.csv"
# Réservation sans outil tiers : le prospect répond à l'email (ou écrit depuis la page de
# vente avec l'objet « Demande de diagnostic ») ; le Cortex détecte la demande et alerte JOSY.
BOOKING_URL = os.environ.get("BOOKING_URL", "").strip()  # lien d'agenda facultatif
BOOKING_LINE = "Si vous souhaitez en savoir plus, répondez à cet email."
REQUEST_SUBJECT = "Demande JOSY EI"  # objet des demandes envoyées depuis le site
SKIP_STATUS_RE = re.compile(r"envoy|refus|stop|r(é|e)pondu|client|perdu", re.IGNORECASE)
# Identification minimale de l'émetteur (LCEN) : ni prénom, ni adresse postale, ni téléphone.
SENDER_EMAIL = os.environ.get("HOSTINGER_EMAIL", "").strip() or "contact@josyei.com"  # émetteur unique
SIGNATURE = ("LE CORTEX par JOSY EI, SIREN 914 113 543, Montmorillon (86), France.\n"
             "Vos coordonnées professionnelles proviennent de sources publiques (intérêt légitime, "
             "art. 6.1.f du RGPD). Pour ne plus recevoir de message : "
             f"mailto:{SENDER_EMAIL}?subject=STOP (ou répondez STOP).")
# Données personnelles de JOSY interdites dans tout contenu sortant (rejet par le judiciaire).
PERSONAL_RE = re.compile(r"\bval[eé]ry\b|gambetta|86500|07\s*52\s*94\s*14\s*60|"
                         r"contactbullebebe|mrjosyvalery", re.IGNORECASE)
ALLOWED_PRICES = {"0", "999", "1499", "1999"}  # Gratuit 0 €, Découverte 9,99, Starter 14,99, Pro 19,99 € HT
PRICE_RE = re.compile(r"(\d[\d\s.,]*)\s*(?:€|euros?)", re.IGNORECASE)


PROSPECT_FIELDS = ["nom", "secteur", "ville", "email", "statut", "source", "siren"]


def load_prospects():
    if not PROSPECTS_PATH.exists():
        return []
    with open(PROSPECTS_PATH, encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in row.items() if k}
                for row in csv.DictReader(f, delimiter=";")
                if (row.get("email") or "").strip() and (row.get("nom") or "").strip()]


def append_prospects(rows):
    """Ajoute des prospects trouvés par la recherche à prospects.csv (colonnes complétées)."""
    existing = load_prospects()
    with open(PROSPECTS_PATH, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PROSPECT_FIELDS, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for r in existing + rows:
            w.writerow({k: r.get(k, "") for k in PROSPECT_FIELDS})


# Recherche de prospects (M1) : de vraies entreprises, des emails lus, jamais devinés.
#  1. entreprises actives de 6 à 49 salariés, par code NAF, via l'API officielle
#     recherche-entreprises.api.gouv.fr (gratuite, sans clé) ;
#  2. site officiel trouvé par un moteur de recherche (Brave Search, clé BRAVE_API_KEY) ;
#  3. email lu sur une page de ce site (domaine identique), URL de la page conservée.
COMPANY_API = "https://recherche-entreprises.api.gouv.fr/search"
SEARCH_API = "https://api.search.brave.com/res/v1/web/search"
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "").strip()
# Secteurs et codes NAF ciblés : secteurs.json (modifiable sans toucher au code).
# Zone : France uniquement (métropole et DOM-TOM), cible francophone. Nouvelle-Aquitaine plus souvent
# (86, 79, 87, 16, 17) ; les requêtes nationales n'ont pas de filtre de département.
SECTEURS_PATH = BASE_DIR / "secteurs.json"
SMALL = "01,02,03,11,12"  # 1 à 49 salariés
DEPARTEMENTS = ("86", "79", "87", "16", "17")


def load_targets():
    try:
        cfg = json.loads(SECTEURS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    zone = cfg.get("priorite_geographique", [list(DEPARTEMENTS), "france"])
    deps = ",".join(zone[0])
    eff = cfg.get("effectif_api", SMALL)
    locale, nationale = [], []
    for name, s in cfg.get("secteurs", {}).items():
        if not s.get("actif", True):
            continue
        codes = s.get("codes_naf", [])
        for i in range(0, len(codes), 20):  # l'API accepte des listes de codes
            base = {"activite_principale": ",".join(codes[i:i + 20]), "tranche_effectif_salarie": eff}
            locale.append((dict(base, departement=deps), name))
            nationale.append((base, name))
    return locale * 3 + nationale  # Nouvelle-Aquitaine trois fois plus souvent


RESEARCH_TARGETS = load_targets() or [({"section_activite_principale": "F"}, "bâtiment")]
EXCLUDED_NAF = re.compile(r"^84\.")  # administration publique
RESEARCH_HEADCOUNT = "03,11,12"     # 6-9, 10-19, 20-49 salariés
ENRICH_PER_RUN = 8                  # entreprises dont on cherche l'email par passage
DIRECTORY_DOMAINS = re.compile(r"pagesjaunes|societe\.com|pappers|linkedin|facebook|instagram|"
                               r"annuaire|verif\.com|infogreffe|manageo|kompass|google|"
                               r"wikipedia|youtube|doctrine|indeed|welcome", re.IGNORECASE)
GENERIC_LOCAL = re.compile(r"^(contact|accueil|info|infos|office|secretariat|cabinet|bonjour|"
                           r"agence|hello|courrier|direction|etude)", re.IGNORECASE)
RAMP_PER_DAY = [5, 10, 15, 20]      # emails proposés par jour, semaines 1 à 4 puis 20


def ramp_cap(start_iso):
    week = (now() - parse_iso(start_iso)).days // 7 if start_iso else 0
    return RAMP_PER_DAY[min(week, len(RAMP_PER_DAY) - 1)]


MAX_ARTICLE_AGE_H = 72          # articles plus vieux : ignorés
ARTICLES_PER_ANALYSIS = _llm["articles"]  # moins d'articles pour un petit modèle local
# Rotation : une mission analysée toutes les 30 min, à tour de rôle.
MISSION_ORDER = ["M5_Veille", "M1_Prospection", "M2_Visibilite",
                 "M3_Relation_Client", "M4_Monetisation"]
MISSION_INTERVAL_MIN = 30
MAX_LLM_CALLS_PER_DAY = 20      # quota Groq gratuit : le chat doit garder des jetons (15/10/2026)
MISSION_TOPICS = {  # mots-clés ajoutés à la recherche dans la mémoire
    "M5_Veille": "tendances IA cybersécurité obligations",
    "M2_Visibilite": "visibilité fiche Google Business publications site web",
    "M3_Relation_Client": "objections réponses profils dirigeants relance",
    "M4_Monetisation": "prix concurrents offre aides financements",
}
# Niveau 2 : ces missions analysent puis recommandent (options, avantages, risques).
LEVEL2_MISSIONS = {"M2_Visibilite", "M3_Relation_Client", "M4_Monetisation"}
LEVEL2_INSTRUCTIONS = (
    "\n\nNIVEAU 2 : avant les propositions, ajoute au JSON trois champs : "
    "\"analyse\" (3 phrases : situation, ce que disent les sources et la mémoire), "
    "\"options\" (2 ou 3 objets {\"option\", \"avantages\", \"risques\"}), "
    "\"recommandation\" (UNE seule phrase : l'option choisie et pourquoi, en tenant compte des "
    "décisions passées de JOSY ci-dessous). Tu tranches : une seule recommandation, jamais une liste de choix. "
    "Périmètre strict : uniquement le site web, la fiche Google Business ou la boutique en ligne ; tout autre "
    "sujet est interdit. Les propositions restent soumises à validation.")
MAX_CHAT_REPLIES_PER_RUN = 3    # discussion libre : réponses par cycle
AUDITS_PER_RUN = 5              # prospects analysés au plus par passage de la prospection
MAX_PROPOSALS_PER_RUN = 3
MAX_PROPOSALS_PER_DAY = 30     # dont 20 emails max (montée en charge RAMP_PER_DAY)
MAX_PENDING = 25                # au-delà, on n'ajoute rien (pas de saturation)
MIN_SOURCES = 2                 # I5
PENDING = "en_attente_humain"

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+33|0)\s*[1-9](?:[\s.-]*\d{2}){4}")
IBAN_RE = re.compile(r"\bFR\d{2}(?:\s?\d{4}){5}\s?\d{3}\b|\b(?:\d{4}[\s-]?){3}\d{4}\b")


# --------------------------------------------------------------------------
# Utilitaires
# --------------------------------------------------------------------------
def now():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def parse_iso(s):
    return datetime.fromisoformat(s)


def paris(dt):
    return dt.astimezone(PARIS).strftime("%d/%m %H:%M")


def norm_url(u):
    return (u or "").strip().rstrip("/")


def strip_html(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def safe_error(exc):
    """Nom de l'exception sans son message (qui peut contenir l'URL et donc le token)."""
    return type(exc).__name__


# --------------------------------------------------------------------------
# Mémoire (SQLite) et journal chaîné (I1)
# --------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS articles (
    url TEXT PRIMARY KEY, feed TEXT, title TEXT, summary TEXT,
    published TEXT, fetched_at TEXT, analyzed INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS entreprises(
  siren TEXT PRIMARY KEY, denomination TEXT, naf TEXT, tranche_effectif TEXT,
  departement TEXT, commune TEXT, date_creation TEXT, categorie_juridique TEXT,
  statut_diffusion TEXT, est_ei INTEGER DEFAULT 0,
  secteur_memoire TEXT, segment TEXT, dirigeant_fonction TEXT,
  site_web TEXT, https INTEGER, cms TEXT, mentions_legales INTEGER,
  politique_confidentialite INTEGER, fiche_google INTEGER, avis_google INTEGER,
  email_contact TEXT, email_origine TEXT, email_collecte_le TEXT,
  statut TEXT DEFAULT 'a_qualifier', dernier_contact TEXT, prochaine_relance TEXT,
  reponse_resume TEXT, score INTEGER DEFAULT 0, prochaine_action TEXT,
  cree_le TEXT, maj_le TEXT, purge_le TEXT);
CREATE TABLE IF NOT EXISTS signaux(
  id INTEGER PRIMARY KEY AUTOINCREMENT, siren TEXT REFERENCES entreprises(siren),
  type TEXT, description TEXT, url TEXT, date TEXT, poids INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS liste_opposition(
  siren TEXT, email_hash TEXT, date_opposition TEXT, PRIMARY KEY(siren, email_hash));
CREATE TABLE IF NOT EXISTS candidates (
    siren TEXT PRIMARY KEY, nom TEXT, secteur TEXT, ville TEXT, source TEXT,
    website TEXT, email TEXT, email_source TEXT, status TEXT, checked_at TEXT);
CREATE TABLE IF NOT EXISTS article_missions (
    url TEXT, mission TEXT, PRIMARY KEY (url, mission));
CREATE TABLE IF NOT EXISTS proposals (
    action_id TEXT PRIMARY KEY, created_at TEXT, risk_level TEXT, mission TEXT,
    action_type TEXT, status TEXT, expires_at TEXT, decided_at TEXT,
    decision_source TEXT, tg_message_id INTEGER, payload TEXT);
CREATE TABLE IF NOT EXISTS journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, power TEXT, event TEXT,
    action_id TEXT, details TEXT, prev_hash TEXT, hash TEXT);
"""


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=30)  # base partagée avec chat_daemon.py
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    def get(self, key, default=None):
        row = self.db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set(self, key, value):
        self.db.execute("INSERT INTO kv(key, value) VALUES(?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (key, str(value)))
        self.db.commit()

    def log(self, power, event, action_id=None, details=None):
        """Journal append-only ; chaque ligne est chaînée à la précédente (sha256)."""
        ts = iso(now())
        row = self.db.execute("SELECT hash FROM journal ORDER BY id DESC LIMIT 1").fetchone()
        prev = row["hash"] if row else "GENESIS"
        det = json.dumps(details or {}, ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha256(
            f"{prev}|{ts}|{power}|{event}|{action_id or ''}|{det}".encode()).hexdigest()
        self.db.execute("INSERT INTO journal(ts, power, event, action_id, details, prev_hash, hash) "
                        "VALUES(?,?,?,?,?,?,?)", (ts, power, event, action_id, det, prev, digest))
        self.db.commit()
        # Trace secondaire dans les logs Actions : sans contenu (les logs d'un repo public sont publics).
        print(json.dumps({"ts": ts, "pouvoir": power, "evenement": event, "id": action_id},
                         ensure_ascii=False))

    def verify_journal(self):
        prev = "GENESIS"
        for r in self.db.execute("SELECT * FROM journal ORDER BY id"):
            digest = hashlib.sha256(
                f"{prev}|{r['ts']}|{r['power']}|{r['event']}|{r['action_id'] or ''}|{r['details']}"
                .encode()).hexdigest()
            if r["prev_hash"] != prev or r["hash"] != digest:
                return False, r["id"]
            prev = r["hash"]
        return True, None

    def count_today(self, sql, *args):
        start = iso(now().astimezone(PARIS).replace(hour=0, minute=0, second=0, microsecond=0))
        return self.db.execute(sql, (start, *args)).fetchone()[0]


# --------------------------------------------------------------------------
# EXÉCUTIF — Telegram
# --------------------------------------------------------------------------
class Telegram:
    def __init__(self, token, chat, store):
        self.token, self.chat, self.store = token, chat, store
        self.enabled = bool(token and chat)
        store.tg = self

    def call(self, method, **params):
        if not self.enabled:
            return {"ok": False, "description": "telegram_non_configure"}
        # Une erreur SSL passagère ne doit pas faire perdre un message : sans nouvel
        # essai, JOSY ne reçoit jamais la réponse et croit que le Cortex est muet.
        for tentative in range(3):
            try:
                r = HTTP.post(f"https://api.telegram.org/bot{self.token}/{method}",
                                  json=params, timeout=30)
                return r.json()
            except (requests.RequestException, ValueError) as exc:
                if tentative == 2:
                    self.store.log("EXECUTIF", "telegram_erreur_reseau",
                                   details={"methode": method, "erreur": safe_error(exc),
                                            "tentatives": 3})
                    return {"ok": False, "description": safe_error(exc)}
                time.sleep(1.5 * (tentative + 1))
        return {"ok": False, "description": "telegram_injoignable"}

    def send(self, text, buttons=None):
        if not self.enabled:
            print("[telegram désactivé] " + strip_html(text)[:300])
            return None
        params = {"chat_id": self.chat, "text": text[:4096], "parse_mode": "HTML",
                  "disable_web_page_preview": True}
        if buttons:
            params["reply_markup"] = {"inline_keyboard": [buttons]}
        res = self.call("sendMessage", **params)
        if not res.get("ok"):
            self.store.log("EXECUTIF", "telegram_envoi_echec",
                           details={"raison": str(res.get("description", ""))[:200]})
            return None
        return res["result"]["message_id"]

    def alert(self, kind, message):
        """Format F. Une alerte par type et par 3 heures au plus (le journal garde tout)."""
        key = f"alerte_{kind}"
        last = self.store.get(key)
        if last and now() - parse_iso(last) < timedelta(hours=3):
            return
        self.store.set(key, iso(now()))
        self.send(f"⚠️ Erreur {html.escape(kind)}. Détails : {html.escape(str(message)[:300])}.")

    def clear_buttons(self, message_id):
        if message_id:
            self.call("editMessageReplyMarkup", chat_id=self.chat, message_id=message_id,
                      reply_markup={"inline_keyboard": []})


# --------------------------------------------------------------------------
# EXÉCUTIF — modèle de langage (Ollama local, Groq, Mistral...)
# --------------------------------------------------------------------------
def llm_configured():
    return bool(LLM_CHAIN)


def alert(store, kind, message):
    tg = getattr(store, "tg", None)
    if tg:
        tg.alert(kind, message)


LAST_LLM = None


def llm_chat(system, user, store, json_mode=True, max_tokens=2000, prefer=None):
    """Renvoie un objet JSON (json_mode) ou du texte libre (discussion Telegram).
    Essaie le fournisseur principal, puis le repli si le principal échoue.
    `prefer` : modèle à essayer en premier (la discussion préfère le plus rapide)."""
    global LAST_LLM
    chaine = sorted(LLM_CHAIN, key=lambda p: p["model"] != prefer) if prefer else LLM_CHAIN
    for cfg in chaine:
        result = _llm_call(cfg, system, user, store, json_mode, max_tokens)
        if result is not None:
            LAST_LLM = f"{cfg['name']}:{cfg['model']}"  # modèle qui a réellement répondu (journalisé)
            return result
    if LLM_CHAIN:
        alert(store, "llm", "aucun modèle n'a répondu (principal et repli)")
    return None


def _llm_call(cfg, system, user, store, json_mode, max_tokens):
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    name = cfg["name"]
    if name == "ollama":
        # API native : permet d'agrandir le contexte (sinon le prompt serait tronqué).
        headers = {"Content-Type": "application/json"}
        body = {"model": cfg["model"], "messages": messages, "stream": False,
                "options": {"temperature": 0.2 if json_mode else 0.5,
                            "num_ctx": 8192 if json_mode else 4096, "num_predict": max_tokens}}
        if json_mode:
            body["format"] = "json"
    else:  # API compatible OpenAI
        headers = {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"}
        body = {"model": cfg["model"], "temperature": 0.2 if json_mode else 0.5,
                "max_tokens": max_tokens, "messages": messages}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        elif "gpt-oss" in cfg["model"]:
            body["reasoning_effort"] = "low"  # discussion : peu de raisonnement, réponse en environ une seconde
    for attempt in range(3):
        try:
            r = HTTP.post(cfg["url"], headers=headers, json=body, timeout=cfg["timeout"])
        except requests.RequestException as exc:
            if attempt < 2:  # incident réseau passager : on réessaie avant d'abandonner
                time.sleep(1.5 * (attempt + 1))
                continue
            store.log("EXECUTIF", "llm_erreur_reseau", details={"fournisseur": name,
                                                               "erreur": safe_error(exc),
                                                               "tentatives": attempt + 1})
            return None
        if r.status_code == 429:
            # Quota atteint (souvent journalier) : attendre ne sert à rien et gèle la
            # conversation. On passe immédiatement au modèle suivant de la chaîne.
            store.log("EXECUTIF", "llm_quota_atteint",
                      details={"fournisseur": name, "modele": cfg["model"]})
            return None
        if r.status_code == 400 and json_mode and "response_format" in body and "json" in r.text.lower():
            body.pop("response_format")  # le modèle a produit un JSON invalide : nouvel essai libre
            body["messages"][0]["content"] += "\nRéponds uniquement par un objet JSON valide."
            continue
        if r.status_code != 200:
            store.log("EXECUTIF", "llm_erreur_http", details={"fournisseur": name,
                                                              "statut": r.status_code,
                                                              "message": r.text[:200]})
            return None
        try:
            data = r.json()
            content = (data["message"]["content"] if name == "ollama"
                       else data["choices"][0]["message"]["content"])
            if not json_mode:
                return str(content).strip()
            m = re.search(r"\{.*\}", str(content), re.S)
            return json.loads(m.group(0) if m else content)
        except (ValueError, KeyError, IndexError, TypeError):
            store.log("EXECUTIF", "llm_reponse_invalide", details={"fournisseur": name})  # I6
            return None
    return None


# --------------------------------------------------------------------------
# JUDICIAIRE — contrôle déterministe des propositions
# --------------------------------------------------------------------------
class Judiciaire:
    """Vérifie chaque proposition de l'exécutif. Peut relever le risque, jamais le baisser."""

    def __init__(self, known_sources, expected_mission=None, articles=None, memoire=None):
        # url normalisée -> (url d'origine, date de publication) : seules sources admises (I6)
        self.known = known_sources
        self.expected_mission = expected_mission  # rotation : seule la mission du créneau
        self.articles = articles   # URL des articles du cycle : au moins une source d'actualité
        self.memoire = memoire     # pour vérifier les citations « memoire:fiche#section »

    def citation_exists(self, cit):
        m = re.fullmatch(r"memoire:([\w.-]+)#([\w.-]+)", cit or "")
        if not m or not self.memoire:
            return False
        return self.memoire.db.execute("SELECT 1 FROM sections WHERE fiche_id=? AND ancre=?",
                                       (m.group(1), m.group(2))).fetchone() is not None

    def review(self, raw):
        reasons, notes = [], []
        if not isinstance(raw, dict):
            return None, ["format: objet JSON attendu"]

        mission = str(raw.get("mission", "")).strip()
        if mission not in MISSIONS:
            reasons.append(f"mission inconnue: {mission!r}")
        elif self.expected_mission and mission != self.expected_mission:
            reasons.append(f"mission {mission} hors du créneau {self.expected_mission}")

        action_type = str(raw.get("action_type", "")).strip().lower()
        if not action_type:
            reasons.append("action_type manquant")
        floor = RISK_BY_ACTION.get(action_type, "R3")
        claimed = str(raw.get("risk_level", "")).strip().upper()
        risk = max([floor] + ([claimed] if claimed in RISK_ORDER else []), key=RISK_ORDER.index)
        if claimed != risk:
            notes.append(f"risque relevé de {claimed or '?'} à {risk} (I7)")

        target = raw.get("target") if isinstance(raw.get("target"), dict) else {}
        company = str(target.get("company", "")).strip()
        contact = str(target.get("contact", "")).strip()
        if not company:
            reasons.append("cible: company manquante")
        if EMAIL_RE.search(contact) or PHONE_RE.search(contact):  # I4 minimisation
            contact = "à identifier par JOSY"
            notes.append("coordonnées personnelles retirées de la cible (I4)")

        content = raw.get("content") if isinstance(raw.get("content"), dict) else {}
        subject = str(content.get("subject", "")).strip()[:200]
        body = str(content.get("body", "")).strip()[:2500]
        if not body:
            reasons.append("contenu vide")
        if EMAIL_RE.search(body) or PHONE_RE.search(body):
            reasons.append("le contenu contient des coordonnées personnelles (I4)")
        if PERSONAL_RE.search(body + " " + subject):
            reasons.append("prénom, adresse ou téléphone personnel de JOSY dans le contenu (I4)")
        if IBAN_RE.search(body):
            reasons.append("le contenu contient des coordonnées bancaires (I10)")
        if action_type in EMAIL_ACTIONS:
            # Un email n'est jamais rédigé par le modèle : seuls les gabarits validés,
            # adressés à un prospect réel de prospects.csv, passent (voir review_email).
            reasons.append("email rédigé par le modèle : interdit, seuls les gabarits validés passent")
        for amount in PRICE_RE.findall(body + " " + subject):
            if re.sub(r"\D", "", amount) not in ALLOWED_PRICES:
                reasons.append(f"prix non autorisé dans le contenu : {amount.strip()} € (I6)")
        # Offre unique (décision de JOSY, 14/10/2026) : site web, fiche Google Business, boutique en ligne.
        scope = " ".join([body, subject, str(raw.get("justification", "")),
                          str((raw.get("target") or {}).get("company", ""))])
        if not re.search(r"\b(sites?|google|boutique|e-?commerce|woocommerce|fiche|r[ée]f[ée]rencement|seo)\b",
                         scope, re.IGNORECASE):
            reasons.append("hors offre : seuls le site web, la fiche Google Business et la boutique en ligne "
                           "sont autorisés")

        sources, seen = [], set()
        for s in raw.get("sources") or []:
            url = norm_url(s.get("url") if isinstance(s, dict) else s)
            if not url or url in seen:
                continue
            seen.add(url)
            if url not in self.known:
                reasons.append(f"source hors de la liste fournie (I6): {url[:120]}")
                continue
            original, published = self.known[url]
            sources.append({"url": original, "date": published})  # date réelle, pas celle du modèle
        if len(sources) < MIN_SOURCES:
            reasons.append(f"{len(sources)} source(s) vérifiée(s), {MIN_SOURCES} minimum (I5)")
        if self.articles is not None and not any(norm_url(s["url"]) in self.articles for s in sources):
            reasons.append("aucune source d'actualité du cycle (I5)")
        citations = [str(c) for c in raw.get("memoire") or []][:6]
        for cit in citations:
            if not self.citation_exists(cit):
                reasons.append(f"citation de mémoire inexistante : {cit[:80]} (I6)")

        justification = str(raw.get("justification", "")).strip()[:800]
        reversibility = str(raw.get("reversibility", "")).strip()[:400]
        if not justification:
            reasons.append("justification manquante (I3)")
        if not reversibility:
            reasons.append("réversibilité non décrite (I8)")

        if reasons:
            return None, reasons
        return {
            "action_id": str(uuid.uuid4()),
            "timestamp": iso(now()),
            "risk_level": risk,
            "mission": mission,
            "action_type": action_type,
            "target": {"company": company[:200], "contact": contact[:120]},
            "content": {"subject": subject, "body": body},
            "sources": sources,
            "justification": justification,
            "reversibility": reversibility,
            "memoire": citations,
            "timeout_hours": TIMEOUT_HOURS[risk],
        }, notes

    @staticmethod
    def review_email(p, prospects, opposed=None):
        """Email de prospection : destinataire réel (prospects.csv) et texte identique au gabarit."""
        reasons = []
        to = p["target"].get("email", "").lower()
        match = [r for r in prospects if r["email"].lower() == to]
        if not to or not match:
            reasons.append("destinataire absent de la feuille de suivi (prospects.csv)")
        else:
            row = match[0]
            if p["target"].get("company") != row["nom"]:
                reasons.append("nom du cabinet différent de la feuille de suivi")
            if p.get("audit"):  # email fondé sur l'analyse : texte recalculé à partir des faits
                import audit
                subject, body = audit.render_audit_email(p["audit"], sys.modules[__name__]) or ("", "")
                if not p["audit"].get("manques"):
                    reasons.append("aucun fait vérifié sur l'entreprise")
            else:
                reasons.append("email sans analyse vérifiée de l'entreprise")
                subject, body = "", ""
            if p["content"].get("subject") != subject or p["content"].get("body") != body:
                reasons.append("texte différent du gabarit validé (offre, prix ou promesse modifiés)")
            if SKIP_STATUS_RE.search(row.get("statut", "")):
                reasons.append(f"prospect au statut « {row['statut']} » : ne pas recontacter")
        if PERSONAL_RE.search(p["content"].get("subject", "") + " " + p["content"].get("body", "")):
            reasons.append("prénom, adresse ou téléphone personnel de JOSY dans l'email (I4)")
        if opposed is not None and email_hash(to) in opposed:
            reasons.append("adresse sur la liste d'opposition")
        if p["risk_level"] != "R2" or p["action_type"] != "cold_email":
            reasons.append("un email de prospection est toujours R2 / cold_email")
        return reasons


# --------------------------------------------------------------------------
# Le Cortex
# --------------------------------------------------------------------------
class Cortex:
    def __init__(self, store, tg):
        self.s, self.tg = store, tg

    # ---------- 1. Commandes Telegram ----------
    def poll_telegram(self):
        if not self.tg.enabled:
            self.s.log("SYSTEME", "telegram_non_configure")
            return
        beat = self.s.get("chat_daemon_heartbeat")
        if beat and now() - parse_iso(beat) < timedelta(seconds=90):
            return  # chat_daemon.py lit Telegram en continu : un seul lecteur getUpdates
        info = self.tg.call("getWebhookInfo")
        if info.get("ok") and info["result"].get("url"):
            # getUpdates est impossible tant qu'un webhook existe : on prévient, on ne supprime rien.
            self.s.log("SYSTEME", "webhook_actif_polling_impossible")
            today = now().astimezone(PARIS).date().isoformat()
            if self.s.get("webhook_alert_day") != today:
                self.tg.send("⚠️ Un webhook est configuré sur le bot : le Cortex ne peut pas lire "
                             "/valider et /refuser. Supprime-le (deleteWebhook) pour activer la "
                             "validation. En attendant, les actions R2/R3 expireront (refus auto).")
                self.s.set("webhook_alert_day", today)
            return

        offset = int(self.s.get("tg_offset", "0"))
        res = self.tg.call("getUpdates", offset=offset, timeout=0, limit=100,
                           allowed_updates=["message", "callback_query"])
        if not res.get("ok"):
            # 409 = un autre programme lit les mises à jour du même bot (ex. Apps Script).
            self.s.log("SYSTEME", "telegram_getupdates_echec",
                       details={"code": res.get("error_code"),
                                "raison": str(res.get("description", ""))[:200]})
            return
        for upd in res.get("result", []):
            try:
                self.handle_update(upd)
            except Exception as exc:  # une mise à jour défectueuse ne bloque pas les suivantes
                self.s.log("SYSTEME", "commande_erreur", details={"erreur": safe_error(exc)})
            self.s.set("tg_offset", upd["update_id"] + 1)

    def handle_update(self, upd):
        if "callback_query" in upd:
            cq = upd["callback_query"]
            chat_id = str(((cq.get("message") or {}).get("chat") or {}).get("id", ""))
            self.tg.call("answerCallbackQuery", callback_query_id=cq["id"])
            if chat_id != self.tg.chat:
                self.s.log("SYSTEME", "commande_chat_non_autorise", details={"chat": chat_id})
                return
            verb, _, short = (cq.get("data") or "").partition(":")
            if verb in ("v", "r"):
                self.decide(short, "valide" if verb == "v" else "refuse", now(), "bouton")
            return

        msg = upd.get("message") or {}
        chat_id = str((msg.get("chat") or {}).get("id", ""))
        text = (msg.get("text") or "").strip()
        if not text:
            return
        if chat_id != self.tg.chat:  # seul JOSY commande le Cortex
            self.s.log("SYSTEME", "commande_chat_non_autorise", details={"chat": chat_id})
            return
        if not text.startswith("/"):
            self.converse(text)
            return
        parts = text.split()
        cmd = parts[0].split("@")[0].lower()
        args = parts[1:]
        sent_at = datetime.fromtimestamp(msg.get("date", time.time()), timezone.utc)
        self.s.log("HUMAIN", "commande_recue", details={"commande": cmd, "args": args[:3]})

        if cmd == "/valider":
            self.decide(args[0] if args else "", "valide", sent_at, "commande")
        elif cmd == "/refuser":
            self.decide(args[0] if args else "", "refuse", sent_at, "commande",
                        motif=" ".join(args[1:])[:300])
        elif cmd == "/stop":
            self.s.set("system_status", "arrete")
            self.s.log("HUMAIN", "arret_demande")
            self.tg.send("🛑 Cortex arrêté (I9). Plus aucune analyse ni proposition. "
                         "Les actions en attente expireront. /reprise pour relancer.")
        elif cmd == "/reprise":
            self.s.set("system_status", "actif")
            self.s.log("HUMAIN", "reprise_demandee")
            self.tg.send("▶️ Cortex relancé.")
        elif cmd in ("/1", "/2", "/3", "/r"):  # choix de la réponse à envoyer à un prospect
            import vente
            vente.setup(self.s)
            vente.answer_reply(sys.modules[__name__], self, cmd[1:], " ".join(text.split()[1:]))
        elif cmd == "/opposition":  # ne plus jamais contacter cette adresse (STOP reçu)
            if not args or not EMAIL_RE.fullmatch(args[0]):
                self.tg.send("Usage : /opposition adresse@exemple.fr")
            else:
                self.s.db.execute("INSERT OR IGNORE INTO liste_opposition(siren, email_hash, "
                                  "date_opposition) VALUES('', ?, ?)", (email_hash(args[0]), iso(now())))
                self.s.db.commit()
                self.s.log("HUMAIN", "opposition_ajoutee")  # ni l'adresse ni son hash dans le journal
                self.tg.send("✅ Adresse ajoutée à la liste d'opposition : plus jamais contactée.")
        elif cmd in ("/jour", "/ajuste", "/fait", "/reporte", "/profil", "/vie", "/bilan"):
            import fondateur
            fondateur.commande(sys.modules[__name__], self, cmd, args, text)
        elif cmd in ("/etat", "/status", "/état"):
            self.tg.send(self.status_text())
        elif cmd == "/attente":
            self.tg.send(self.pending_text())
        elif cmd == "/cles":  # clés et accès manquants (noms seulement, jamais de valeur)
            import demarrage
            self.tg.send(html.escape(demarrage.rapport()))
        elif cmd in ("/oui", "/non"):  # réponse à la dernière recommandation (rien n'est exécuté seul)
            self.s.log("HUMAIN", "recommandation_acceptee" if cmd == "/oui" else "recommandation_refusee")
            self.tg.send("✅ Noté." if cmd == "/oui" else "❌ Noté, rien ne sera fait.")
        elif cmd == "/historique":
            import honnetete
            self.tg.send(html.escape(honnetete.historique(self.s)))
        elif cmd == "/log":
            import honnetete
            self.tg.send(html.escape(honnetete.log_resume(self.s)))
        elif cmd == "/lancer_prospection":
            import honnetete
            honnetete.lancer_prospection(sys.modules[__name__], self)
        else:
            self.tg.send(HELP)

    def converse(self, text):
        """Discussion libre avec JOSY. Ne déclenche jamais d'action : la conversation
        ne passe ni par le judiciaire ni par dispatch, elle produit seulement du texte."""
        self.chat_count = getattr(self, "chat_count", 0) + 1
        if self.chat_count > MAX_CHAT_REPLIES_PER_RUN:
            if self.chat_count == MAX_CHAT_REPLIES_PER_RUN + 1:
                self.tg.send("Plusieurs messages reçus : je réponds aux premiers, renvoie la suite "
                             "dans quelques minutes.")
            return
        if not llm_configured():
            self.tg.send("Aucun modèle de langage configuré : je ne peux pas discuter. " + HELP)
            return
        t0 = time.monotonic()
        try:  # réponse libre à la question du jour : une donnée de vie (I14), chemin rapide sans modèle
            import fondateur
            if fondateur.capturer(sys.modules[__name__], self, text):
                self.s.log("EXECUTIF", "reponse_rapide_question", details={"ms": int((time.monotonic() - t0) * 1000)})
                return  # compris et enregistré : pas d'appel au modèle, pas de seconde réponse
        except Exception as exc:
            self.s.log("EXECUTIF", "fondateur_capture_echec", details={"erreur": safe_error(exc)})
        self.s.log("HUMAIN", "message_libre_recu", details={"longueur": len(text)})
        if FACTUAL_RE.search(text) or len(text) < 4:
            # Capacités / état : réponse construite à partir des vraies données, sans modèle.
            pending = self.s.db.execute("SELECT COUNT(*) FROM proposals WHERE status=?",
                                        (PENDING,)).fetchone()[0]
            nxt = MISSION_ORDER[int(self.s.get("mission_index", "0")) % len(MISSION_ORDER)]
            self.tg.send(f"🧠 {self.s.get('system_status', 'actif').capitalize()} · {pending} en attente "
                         f"· prochaine mission {nxt.split('_', 1)[1]}.\n"
                         "Je gère d'abord votre journée (plan, créneaux, charge), puis votre veille, la "
                         "prospection par email, vos publications Google Business, le site et la boutique "
                         "en ligne. /etat pour le détail.")
            self.s.log("EXECUTIF", "reponse_factuelle_envoyee")
            return
        self.s.db.execute("CREATE TABLE IF NOT EXISTS chat_historique (id INTEGER PRIMARY KEY "
                          "AUTOINCREMENT, ts TEXT, role TEXT, texte TEXT)")
        if MISSION_RE.search(text):
            # Mode mission : la demande est notée ; le Cortex n'exécute que ses missions prévues.
            self.s.db.execute("CREATE TABLE IF NOT EXISTS missions_demandees (id INTEGER PRIMARY KEY "
                              "AUTOINCREMENT, ts TEXT, texte TEXT, statut TEXT DEFAULT 'notee')")
            self.s.db.execute("INSERT INTO missions_demandees(ts, texte) VALUES(?, ?)", (iso(now()), text[:1000]))
            self.s.db.commit()
            self.s.log("HUMAIN", "mission_demandee")
            self.tg.send("📌 Mode mission : demande notée. J'exécute seulement mes missions prévues "
                         "(veille, prospection, réponses, diagnostics) ; le reste est traité par "
                         "l'équipe Claude, qui la retrouve dans mon journal.")
            return
        # Mode conversation : mémoire validée + 6 derniers échanges.
        mem = open_memoire()
        # Conversation : un prompt court répond vite. Mesuré sur le modèle local :
        # 3 371 caractères -> 40 s ; 2 500 caractères -> 10 s. Et au-delà d'environ
        # 8 000 caractères, les petits modèles hébergés refusent (« Request too large »).
        # Prompt court par défaut (réponse rapide) ; mémoire, articles et capacités seulement si le message
        # parle de veille, d'actualité, de marché ou de ce que fait le Cortex.
        detail = re.search(r"actu|article|veille|nouveaut|march[ée]|concurren|prix|rgpd|cnil|fiche|m[ée]moire|"
                           r"capacit|que fais|que sais", text, re.IGNORECASE)
        contexte = mem.contexte_pour_prompt(text, k=2, max_chars=1200) if (mem and detail) else ""
        histo = self.s.db.execute("SELECT role, texte FROM chat_historique ORDER BY id DESC LIMIT 4").fetchall()
        echanges = "\n".join(f"{'JOSY' if r['role'] == 'josy' else 'Cortex'} : {r['texte']}"
                             for r in reversed(histo))
        news = self.s.db.execute("SELECT feed, title, url FROM articles ORDER BY published DESC LIMIT 3").fetchall()
        actus = "\n".join(f"- {n['title']} ({n['feed']}, {n['url']})" for n in news)
        import honnetete
        system = (CHAT_PROMPT + "\n" + honnetete.CONSIGNES_HONNETE + "\n" + honnetete.contexte_reel(self.s)
                  + ("\n\nPour parler d'actualité, n'utilise QUE les articles listés ci-dessous, "
                     "en citant la source ; sinon dis que tu n'as rien lu là-dessus."
                     + "\n\n" + strip_html(CAPABILITIES) + "\n\nÉtat actuel du Cortex :\n"
                     + strip_html(self.status_text()) if detail else "")
                  + ("\n\nARTICLES RÉCEMMENT LUS :\n" + actus if actus and detail else "")
                  + ("\n\nMÉMOIRE (fiches validées) :\n" + contexte if contexte else "")
                  + ("\n\nDERNIERS ÉCHANGES :\n" + echanges if echanges else ""))
        try:  # la question que le Cortex vient de poser à JOSY : sans elle, sa réponse n'a pas de sens
            import fondateur
            cle_q = fondateur.question_en_attente(sys.modules[__name__], self.s)
            if cle_q:
                system += (f"\n\nQUESTION POSÉE À JOSY, SANS RÉPONSE ENREGISTRÉE : « {fondateur.CHAMPS_DICT[cle_q][0]} ». "
                           "S'il y répond, accuse réception en une phrase.")
        except Exception:
            pass
        system += ("\n\nCOHÉRENCE : réponds uniquement à ce que JOSY vient de dire, en tenant compte des derniers "
                   "échanges. Si son message est ambigu, pose UNE question de clarification. Ne parle jamais de "
                   "« délai », de « temps de réponse » ni de ce que tu feras « pendant que » il fait autre chose.")
        self.tg.call("sendChatAction", chat_id=self.tg.chat, action="typing")  # accusé immédiat : « écrit… »
        answer = llm_chat(system, text[:2000], self.s, json_mode=False, max_tokens=400,
                          prefer="openai/gpt-oss-20b")  # le plus rapide d'abord ; repli : 120b, qwen, local
        if not answer:
            self.tg.send("Je n'ai pas pu formuler de réponse cette fois. Réessaie au prochain cycle.")
            return
        self.s.db.executemany("INSERT INTO chat_historique(ts, role, texte) VALUES(?,?,?)",
                              [(iso(now()), "josy", text[:1000]), (iso(now()), "cortex", answer[:1500])])
        self.s.db.execute("DELETE FROM chat_historique WHERE id NOT IN "
                          "(SELECT id FROM chat_historique ORDER BY id DESC LIMIT 40)")
        self.s.db.commit()
        self.tg.send(html.escape(answer[:3500]))
        self.s.log("EXECUTIF", "reponse_libre_envoyee", details={"longueur": len(answer), "modele": LAST_LLM,
                                                                          "ms": int((time.monotonic() - t0) * 1000)})

    def decide(self, short, decision, decided_at, source, motif=""):
        short = short.strip().lower()
        if len(short) < 6:
            self.tg.send("Indique l'identifiant (8 premiers caractères suffisent). /attente pour la liste.")
            return
        rows = self.s.db.execute("SELECT * FROM proposals WHERE action_id LIKE ?",
                                 (short + "%",)).fetchall()
        if len(rows) != 1:
            self.tg.send(f"Identifiant {html.escape(short)} : {len(rows)} correspondance(s). /attente pour la liste.")
            return
        p = rows[0]
        aid = p["action_id"]
        if p["status"] != PENDING:
            self.tg.send(f"<code>{aid[:8]}</code> est déjà au statut « {p['status']} ».")
            return
        if decided_at > parse_iso(p["expires_at"]):  # décision arrivée après le délai
            self.close(p, "refuse_timeout", "timeout")
            self.tg.send(f"⌛ <code>{aid[:8]}</code> avait expiré : refus automatique maintenu.")
            return
        self.s.db.execute("UPDATE proposals SET status=?, decided_at=?, decision_source=? "
                          "WHERE action_id=?", (decision, iso(decided_at), source, aid))
        self.s.db.commit()
        self.s.log("HUMAIN", f"decision_{decision}", aid, {"source": source, "motif": motif})
        self.tg.clear_buttons(p["tg_message_id"])
        if decision == "valide":
            self.execute(json.loads(p["payload"]))
        else:
            self.tg.send(f"❌ <code>{aid[:8]}</code> refusé. Rien ne sera fait.")

    def close(self, p, status, source):
        self.s.db.execute("UPDATE proposals SET status=?, decided_at=?, decision_source=? "
                          "WHERE action_id=?", (status, iso(now()), source, p["action_id"]))
        self.s.db.commit()
        self.s.log("JUDICIAIRE", status, p["action_id"])
        self.tg.clear_buttons(p["tg_message_id"])

    # ---------- EXÉCUTIF : exécution d'une action validée ----------
    def execute(self, p):
        """I10 : après validation de JOSY, les emails partent par contact@josyei.com (vente.py) ;
        tout autre contenu (publication Google Business, site, boutique) est remis à JOSY."""
        if p["action_type"] in SENDABLE_ACTIONS:  # validé par JOSY : envoi par la boîte josyei.com
            import vente
            vente.setup(self.s)
            vente.queue_from_proposal(sys.modules[__name__], self, p)
            return
        c = p["content"]
        text = (f"✅ <b>Validé</b> <code>{p['action_id'][:8]}</code> · {p['action_type']}\n"
                f"Cible : {html.escape(p['target']['company'])} ({html.escape(p['target']['contact'])})\n"
                + (f"<b>À :</b> {html.escape(p['target']['email'])}\n" if p["target"].get("email") else "")
                + "\n"
                + (f"<b>Objet :</b> {html.escape(c['subject'])}\n\n" if c.get("subject") else "")
                + f"<pre>{html.escape(c['body'][:3200])}</pre>\n"
                f"À envoyer par toi depuis {SENDER_EMAIL} (aucun envoi automatique configuré).")
        self.tg.send(text)
        self.s.db.execute("UPDATE proposals SET status='execute_remis' WHERE action_id=?",
                          (p["action_id"],))
        self.s.db.commit()
        self.s.log("EXECUTIF", "contenu_remis_a_josy", p["action_id"])

    # ---------- 2. Timeouts ----------
    def expire_timeouts(self):
        for p in self.s.db.execute("SELECT * FROM proposals WHERE status=? AND expires_at<?",
                                   (PENDING, iso(now()))).fetchall():
            self.close(p, "refuse_timeout", "timeout")
            self.tg.send(f"⌛ Refus automatique (sans réponse en {TIMEOUT_HOURS[p['risk_level']]} h) : "
                         f"<code>{p['action_id'][:8]}</code> {p['action_type']}.")

    # ---------- 3. Veille RSS ----------
    def fetch_feeds(self):
        cutoff = now() - timedelta(hours=MAX_ARTICLE_AGE_H)
        for name, url in FEEDS.items():
            feed = None
            for essai in range(3):  # erreurs réseau passagères (SSL, coupure) : 3 essais
                try:
                    r = requests.get(url, timeout=20, headers={"User-Agent": "JOSY-EI-Cortex/1.0 (+https://josyei.com)"})
                    r.raise_for_status()
                    feed = feedparser.parse(r.content)
                    break
                except Exception as exc:
                    if essai == 2:
                        self.s.log("EXECUTIF", "flux_erreur", details={"flux": name, "erreur": safe_error(exc)})
                    else:
                        time.sleep(2)
            if feed is None:
                continue
            added = 0
            for e in feed.entries:
                link = norm_url(e.get("link"))
                if not link.startswith("http"):
                    continue
                t = e.get("published_parsed") or e.get("updated_parsed")
                pub = datetime(*t[:6], tzinfo=timezone.utc) if t else now()
                cur = self.s.db.execute(
                    "INSERT OR IGNORE INTO articles(url, feed, title, summary, published, fetched_at, analyzed) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (link, name, strip_html(e.get("title"))[:300], strip_html(e.get("summary"))[:600],
                     iso(pub), iso(now()), 0 if pub >= cutoff else 2))
                added += cur.rowcount
            self.s.db.commit()
            self.s.log("EXECUTIF", "flux_lu", details={"flux": name, "articles": len(feed.entries),
                                                       "nouveaux": added})

    # ---------- 4. Analyse + contrôle judiciaire ----------
    def analyze(self):
        if not llm_configured():
            self.s.log("SYSTEME", "llm_non_configure", details={"fournisseur": LLM_PROVIDER})
            return []
        # Rotation : une seule mission par créneau de MISSION_INTERVAL_MIN minutes.
        last = self.s.get("last_analysis")
        if last and now() - parse_iso(last) < timedelta(minutes=MISSION_INTERVAL_MIN):
            return []
        calls = self.s.count_today("SELECT COUNT(*) FROM journal WHERE ts>=? AND event='analyse_llm'")
        if calls >= MAX_LLM_CALLS_PER_DAY:
            self.s.log("SYSTEME", "quota_llm_journalier_atteint")
            return []
        idx = int(self.s.get("mission_index", "0")) % len(MISSION_ORDER)
        mission = MISSION_ORDER[idx]
        # Le créneau est consommé même en cas d'échec : une mission ne bloque pas les autres.
        self.s.set("mission_index", idx + 1)
        self.s.set("last_analysis", iso(now()))
        if mission == "M1_Prospection":
            self.research()        # nouvelles entreprises réelles + emails publics sourcés
            return self.prospect()  # sans modèle : prospect réel + gabarit fixe

        # Articles récents que cette mission n'a pas encore étudiés.
        new = self.s.db.execute(
            "SELECT * FROM articles WHERE analyzed!=2 AND url NOT IN "
            "(SELECT url FROM article_missions WHERE mission=?) "
            "ORDER BY published DESC LIMIT ?", (mission, ARTICLES_PER_ANALYSIS)).fetchall()
        if len(new) < MIN_SOURCES:
            self.s.log("SYSTEME", "mission_sans_nouveaux_articles", details={"mission": mission})
            return []

        articles = [{"url": a["url"], "source": a["feed"], "date": a["published"][:10],
                     "titre": a["title"], "resume": a["summary"][:300]} for a in new]
        # Mémoire validée (lecture seule) : passages pertinents, à citer.
        mem = open_memoire()
        query = MISSION_TOPICS.get(mission, "") + " " + " ".join(a["title"] for a in new)
        passages = mem.search(query, k=4) if mem else []
        contexte = mem.contexte_pour_prompt(query, k=4, max_chars=MEMOIRE_MAX_CHARS) if mem else ""
        if passages:
            self.s.log("EXECUTIF", "memoire_consultee",
                       details={"citations": [p["citation"] for p in passages]})
        level2 = mission in LEVEL2_MISSIONS
        user = (f"Mission de ce cycle : {mission}. Ne propose QUE des actions de cette mission "
                f"(champ \"mission\" = \"{mission}\").\n"
                "Voici les articles (au moins une source par proposition doit en venir). "
                "Détecte les opportunités business pour JOSY EI selon tes règles et réponds en JSON.\n"
                + json.dumps(articles, ensure_ascii=False)
                + ("\n\nMÉMOIRE DU CORTEX (connaissances validées par JOSY, à citer dans le champ "
                   "\"memoire\" avec l'identifiant exact memoire:fiche#section ; ce qui est marqué "
                   "estimation ou non vérifié ne va jamais dans un contenu destiné à un prospect) :\n"
                   + contexte if contexte else "")
                + (LEVEL2_INSTRUCTIONS + self.decision_history() if level2 else ""))
        self.s.log("EXECUTIF", "analyse_llm", details={"mission": mission, "articles": len(new),
                                                      "fournisseur": LLM_PROVIDER, "modele": LLM_MODEL,
                                                      "memoire_caracteres": len(contexte)})
        started = time.monotonic()
        result = llm_chat(AGENTS_PATH.read_text(encoding="utf-8"), user, self.s)
        self.s.log("EXECUTIF", "analyse_llm_fin", details={"mission": mission,
                                                          "secondes": round(time.monotonic() - started),
                                                          "ok": result is not None})
        if result is None:
            return []  # les articles restent à étudier au prochain passage de la mission
        self.s.db.executemany("INSERT OR IGNORE INTO article_missions(url, mission) VALUES(?, ?)",
                              [(a["url"], mission) for a in new])
        self.s.db.executemany("UPDATE articles SET analyzed=1 WHERE url=?", [(a["url"],) for a in new])
        self.s.db.commit()

        known = {norm_url(a["url"]): (a["url"], a["published"][:10]) for a in new}
        if mem:  # sources citées par les fiches de mémoire : vérifiables, comme les articles
            known.update({norm_url(u): v for u, v in mem.sources_connues(passages).items()})
        judge = Judiciaire(known, expected_mission=mission,
                           articles={norm_url(a["url"]) for a in new}, memoire=mem)
        if level2 and isinstance(result, dict):
            self.send_recommendation(mission, result)
        raw_list = result.get("propositions") if isinstance(result, dict) else None
        if not isinstance(raw_list, list):
            self.s.log("JUDICIAIRE", "reponse_hors_format")
            return []
        accepted = []
        for raw in raw_list[:MAX_PROPOSALS_PER_RUN]:
            proposal, notes = judge.review(raw)
            if proposal is None:
                self.s.log("JUDICIAIRE", "proposition_rejetee", details={
                    "motifs": notes, "action_type": str((raw or {}).get("action_type", ""))[:40]
                    if isinstance(raw, dict) else ""})
                continue
            self.s.log("JUDICIAIRE", "proposition_admise", proposal["action_id"],
                       {"risque": proposal["risk_level"], "notes": notes})
            accepted.append(proposal)
        if not raw_list:
            self.s.log("EXECUTIF", "aucune_opportunite")
        return accepted

    def refresh_memoire(self):
        """Reconstruit l'index si une fiche .md est plus récente (écriture atomique côté memoire.py)."""
        if not build_memoire:
            return
        src = MEMOIRE_DB.parent
        newest = max((p.stat().st_mtime for p in src.rglob("*.md")), default=0)
        if newest and (not MEMOIRE_DB.exists() or newest > MEMOIRE_DB.stat().st_mtime):
            try:
                rejets = build_memoire(src, MEMOIRE_DB, verbose=False) or []
            except Exception as exc:
                self.s.log("SYSTEME", "memoire_erreur", details={"erreur": safe_error(exc)})
                return
            self.s.log("SYSTEME", "memoire_reindexee", details={"rejets": len(rejets)})
            if rejets:
                self.tg.send(f"⚠️ Mémoire : {len(rejets)} fiche(s) rejetée(s) (motif interdit). "
                             "Voir le journal.")

    # ---------- Niveau 2 : analyse puis recommandation ----------
    def decision_history(self):
        """Ce que JOSY a validé ou refusé (30 jours) : le modèle en tient compte."""
        since = iso(now() - timedelta(days=30))
        rows = self.s.db.execute("SELECT action_type, status, COUNT(*) n FROM proposals "
                                 "WHERE created_at>=? GROUP BY action_type, status", (since,)).fetchall()
        motifs = [json.loads(r["details"]).get("motif") for r in self.s.db.execute(
            "SELECT details FROM journal WHERE event='decision_refuse' AND ts>=? "
            "ORDER BY id DESC LIMIT 5", (since,))]
        lines = [f"- {r['action_type']} : {r['status']} × {r['n']}" for r in rows]
        lines += [f"- motif de refus : {m}" for m in motifs if m]
        return "\n\nDÉCISIONS DE JOSY (30 derniers jours) :\n" + ("\n".join(lines) or "- aucune")

    def send_recommendation(self, mission, result):
        """R0 : analyse journalisée en entier, résumé de 3 lignes sur Telegram."""
        reco = str(result.get("recommandation", "")).strip()
        options = [o for o in result.get("options") or [] if isinstance(o, dict)][:3]
        if not reco:
            return
        if PERSONAL_RE.search(reco) or any(PERSONAL_RE.search(json.dumps(o, ensure_ascii=False))
                                           for o in options):
            self.s.log("JUDICIAIRE", "recommandation_rejetee", details={"motif": "données personnelles"})
            return
        if not re.search(r"\b(sites?|google|boutique|e-?commerce|woocommerce|fiche|r[ée]f[ée]rencement|seo)\b",
                         reco, re.IGNORECASE):  # offre unique : site web, Google Business, boutique en ligne
            self.s.log("JUDICIAIRE", "recommandation_hors_offre", details={"mission": mission})
            return
        self.s.log("EXECUTIF", "recommandation", details={
            "mission": mission, "analyse": str(result.get("analyse", ""))[:800],
            "options": options, "recommandation": reco[:500]})
        # Une seule recommandation, jamais une liste d'options (les options restent dans le journal).
        self.tg.send(f"💡 Recommandation : {html.escape(re.split(r'(?<=[.!?])\s', reco)[0][:220].rstrip('.'))}. "
                     "/oui /non")

    # ---------- 4 bis. Recherche de prospects (sources vérifiables) ----------
    def research(self):
        """Ajoute de vraies entreprises (API officielle), puis cherche leur email public."""
        self.collect_companies()
        import audit
        if not audit.search_available():
            self.s.log("SYSTEME", "recherche_email_inactive", details={"raison": "aucun moteur de recherche"})
            return
        known = {r["email"].lower() for r in load_prospects()}
        found = []
        for c in self.s.db.execute("SELECT * FROM candidates WHERE status='nouveau' "
                                   "ORDER BY rowid LIMIT ?", (ENRICH_PER_RUN,)).fetchall():
            email, page, site = self.find_public_email(c)
            status = "email_trouve" if email and email.lower() not in known else "sans_email"
            self.s.db.execute("UPDATE candidates SET website=?, email=?, email_source=?, status=?, "
                              "checked_at=? WHERE siren=?",
                              (site, email, page, status, iso(now()), c["siren"]))
            self.s.db.execute("UPDATE entreprises SET site_web=?, email_contact=?, email_origine=?, "
                              "email_collecte_le=?, statut=?, maj_le=? WHERE siren=?",
                              (site, email, page, iso(now()) if email else None,
                               "a_contacter" if status == "email_trouve" else "a_qualifier",
                               iso(now()), c["siren"]))
            self.s.db.commit()  # ne jamais garder la base verrouillée pendant les recherches web
            if status == "email_trouve":
                known.add(email.lower())
                found.append({"nom": c["nom"], "secteur": c["secteur"], "ville": c["ville"],
                              "email": email, "statut": "trouvé (recherche)",
                              "source": page, "siren": c["siren"]})
        self.s.db.commit()
        if found:
            append_prospects(found)
        self.s.log("EXECUTIF", "recherche_prospects", details={"emails_trouves": len(found)})

    def collect_companies(self):
        """Source : annuaire officiel des entreprises (Sirene), une page par passage, secteurs de
        secteurs.json en rotation."""
        pending = self.s.db.execute("SELECT COUNT(*) FROM candidates WHERE status='nouveau'").fetchone()[0]
        if pending >= ENRICH_PER_RUN * 3:
            return
        idx = int(self.s.get("research_index", "0"))
        query, secteur = RESEARCH_TARGETS[idx % len(RESEARCH_TARGETS)]
        self.s.set("research_index", idx + 1)
        page_key = "research_page_" + "_".join(f"{k}={v}" for k, v in query.items())
        page = int(self.s.get(page_key, "0")) % 400 + 1  # l'API plafonne à 10 000 résultats
        self.s.set(page_key, page)
        naf = query.get("activite_principale", "")
        try:
            r = requests.get(COMPANY_API, timeout=30, params=dict(
                {"tranche_effectif_salarie": RESEARCH_HEADCOUNT}, **query,
                etat_administratif="A", per_page=25, page=page))
            r.raise_for_status()
            results = r.json().get("results", [])
        except (requests.RequestException, ValueError) as exc:
            self.s.log("EXECUTIF", "recherche_api_erreur", details={"erreur": safe_error(exc)})
            return
        added = 0
        for e in results:
            comp = e.get("complements") or {}
            if e.get("statut_diffusion") != "O":
                continue  # diffusion restreinte : on ne prospecte pas
            if query.get("departement") and (e.get("siege") or {}).get("departement") not in query["departement"].split(","):
                continue  # le filtre de l'API porte sur les établissements : on veut le siège dans le 86
            if (comp.get("est_association") or comp.get("est_administration")
                    or comp.get("est_service_public") or EXCLUDED_NAF.match(e.get("activite_principale") or "")):
                continue
            nom = (e.get("nom_complet") or "").strip()
            sect = secteur
            siege = e.get("siege") or {}
            self.s.db.execute(  # fiche entreprise (schéma 60-fiches-entreprise)
                "INSERT OR IGNORE INTO entreprises(siren, denomination, naf, tranche_effectif, "
                "departement, commune, date_creation, categorie_juridique, statut_diffusion, "
                "secteur_memoire, statut, cree_le, maj_le) VALUES(?,?,?,?,?,?,?,?,?,?,'a_qualifier',?,?)",
                (e["siren"], nom[:200], e.get("activite_principale"), e.get("tranche_effectif_salarie"),
                 siege.get("departement"), siege.get("libelle_commune"), e.get("date_creation"),
                 e.get("nature_juridique"), e.get("statut_diffusion"), sect, iso(now()), iso(now())))
            cur = self.s.db.execute(
                "INSERT OR IGNORE INTO candidates(siren, nom, secteur, ville, source, status) "
                "VALUES(?,?,?,?,?,'nouveau')",
                (e["siren"], nom[:200], sect, (siege.get("libelle_commune") or "").title(),
                 f"https://annuaire-entreprises.data.gouv.fr/entreprise/{e['siren']}"))
            added += cur.rowcount
        self.s.db.commit()
        self.s.log("EXECUTIF", "recherche_entreprises", details={"filtre": query, "page": page,
                                                                 "ajoutees": added})

    def find_public_email(self, c):
        """Site officiel (recherche web : DuckDuckGo, ou Brave si clé ; la page doit citer le
        nom), puis email lu sur une page de ce site (même domaine)."""
        from urllib.parse import urlparse, urljoin
        from urllib import robotparser
        import audit
        site = audit.find_website(c["nom"], c["ville"])
        if not site:  # sans site : email publié, lu dans les extraits des résultats de recherche
            email, source = audit.find_public_email(c["nom"], c["ville"])
            return email, source, None
        root = f"{urlparse(site).scheme}://{urlparse(site).netloc}"
        domain = urlparse(site).netloc.lower().removeprefix("www.")
        robots = robotparser.RobotFileParser(root + "/robots.txt")
        try:
            robots.read()
        except Exception:
            robots = None
        ua = "JOSY-EI-Cortex/1.0 (+https://josyei.com)"
        for path in ("", "/contact", "/contact/", "/nous-contacter", "/mentions-legales"):
            url = urljoin(root + "/", path.lstrip("/"))
            if robots and not robots.can_fetch(ua, url):
                continue
            try:
                page = requests.get(url, timeout=15, headers={"User-Agent": ua})
                if page.status_code != 200:
                    continue
            except requests.RequestException:
                continue
            emails = {m.lower().rstrip(".") for m in EMAIL_RE.findall(html.unescape(page.text))}
            same = [m for m in emails if m.split("@")[1].removeprefix("www.") == domain]
            if same:  # adresse générique d'abord (contact@, accueil@...)
                same.sort(key=lambda m: (not GENERIC_LOCAL.match(m), m))
                return same[0], url, root
            time.sleep(1)
        return None, None, root

    # ---------- 4 ter. Prospection : prospect réel + gabarit fixe ----------
    def prospect(self):
        prospects = load_prospects()
        done = set()
        for (payload,) in self.s.db.execute("SELECT payload FROM proposals WHERE action_type='cold_email' "
                                            "AND status NOT IN ('retire_gabarit')"):
            try:
                done.add(json.loads(payload)["target"].get("email", "").lower())
            except (ValueError, KeyError, TypeError):
                continue
        opposed = {h for (h,) in self.s.db.execute("SELECT email_hash FROM liste_opposition")}
        todo = [r for r in prospects
                if r["email"].lower() not in done and not SKIP_STATUS_RE.search(r.get("statut", ""))
                and email_hash(r["email"]) not in opposed]
        # Priorité JOSY : artisans et commerces d'abord, cabinets (notaires, avocats, comptables) en dernier.
        def rank(r):
            s = r.get("secteur", "").lower()
            if any(w in s for w in ("bâtiment", "batiment", "restaurant", "coiffure", "commerce")):
                return 0
            return 2 if any(w in s for w in ("notai", "avocat", "expert", "compta", "juridique")) else 1
        todo.sort(key=rank)
        if not todo:
            self.s.log("EXECUTIF", "prospection_liste_epuisee", details={"prospects": len(prospects)})
            return []
        # Analyse approfondie : on cherche, dans l'ordre de la feuille, le premier prospect dont
        # l'analyse publique révèle au moins un manque vérifié. Sans fait vérifié : pas d'email.
        import audit
        self.s.db.execute("CREATE TABLE IF NOT EXISTS audits (email TEXT PRIMARY KEY, date TEXT, "
                          "manques INTEGER, analyse TEXT)")
        recent = {r[0] for r in self.s.db.execute(
            "SELECT email FROM audits WHERE date>=?", (iso(now() - timedelta(days=30)),))}
        # Conditions Google Places : données (notes, avis) conservées 30 jours au plus.
        self.s.db.execute("DELETE FROM audits WHERE date<?", (iso(now() - timedelta(days=30)),))
        self.s.db.commit()
        qualified = []  # jusqu'à MAX_PROPOSALS_PER_RUN prospects qualifiés par passage
        for cand in [r for r in todo if r["email"].lower() not in recent][:AUDITS_PER_RUN]:
            a = audit.audit_prospect(cand)
            self.s.db.execute("INSERT OR REPLACE INTO audits VALUES(?,?,?,?)",
                              (cand["email"].lower(), iso(now()), len(a["manques"]),
                               json.dumps(a, ensure_ascii=False)))
            self.s.db.commit()
            self.s.log("EXECUTIF", "prospect_analyse", details={"manques": len(a["manques"]),
                                                               "services": a["services"]})
            if a["manques"]:
                qualified.append((cand, a))
                if len(qualified) >= MAX_PROPOSALS_PER_RUN:
                    break
        return [p for p in (self.audit_proposal(r, a, prospects, opposed) for r, a in qualified) if p]

    def audit_proposal(self, row, analysis, prospects, opposed):
        import audit
        subject, body = audit.render_audit_email(analysis, sys.modules[__name__])
        p = {
            "audit": analysis,
            "action_id": str(uuid.uuid4()),
            "timestamp": iso(now()),
            "risk_level": "R2",
            "mission": "M1_Prospection",
            "action_type": "cold_email",
            "target": {"company": row["nom"], "contact": f"{row['secteur']}, {row['ville']}",
                       "email": row["email"]},
            "content": {"subject": subject, "body": body},
            "sources": [{"url": analysis["site"].get("url_finale") or "", "date": analysis["date"]}]
            + ([{"url": analysis["entreprise"]["officiel"]["source"], "date": analysis["date"]}]
               if analysis["entreprise"].get("officiel") else []),
            "justification": "Manques constatés : " + " ; ".join(analysis["manques"][:3]) + ".",
            "reversibility": "Rien n'est envoyé sans toi. Après envoi, le prospect peut répondre STOP.",
            "timeout_hours": TIMEOUT_HOURS["R2"],
        }
        reasons = Judiciaire.review_email(p, prospects, opposed)
        if reasons:
            self.s.log("JUDICIAIRE", "proposition_rejetee", details={"motifs": reasons,
                                                                     "action_type": "cold_email"})
            return None
        self.s.log("JUDICIAIRE", "proposition_admise", p["action_id"],
                   {"risque": "R2", "notes": ["analyse vérifiée"]})
        return p

    # ---------- 5. Soumission ----------
    def dispatch(self, p, header=None, text=None):
        aid, risk = p["action_id"], p["risk_level"]
        created = parse_iso(p["timestamp"])
        expires = created + timedelta(hours=p["timeout_hours"])
        if risk in ("R2", "R3"):
            pending = self.s.db.execute("SELECT COUNT(*) FROM proposals WHERE status=?",
                                        (PENDING,)).fetchone()[0]
            today = self.s.count_today("SELECT COUNT(*) FROM proposals WHERE created_at>=?")
            if pending >= MAX_PENDING or today >= MAX_PROPOSALS_PER_DAY:
                self.s.log("JUDICIAIRE", "proposition_differee_quota", aid,
                           {"en_attente": pending, "aujourdhui": today})
                return
        status = {"R0": "execute_auto", "R1": "notifie", "R2": PENDING, "R3": PENDING}[risk]
        cold = p["action_type"] == "cold_email"
        if cold and self.s.db.execute("SELECT 1 FROM proposals WHERE status=? AND action_type="
                                        "'cold_email'", (PENDING,)).fetchone():
            self.s.log("SYSTEME", "email_en_reserve", aid)  # une seule validation à la fois
            return
        self.s.db.execute(
            "INSERT INTO proposals(action_id, created_at, risk_level, mission, action_type, status, "
            "expires_at, payload) VALUES(?,?,?,?,?,?,?,?)",
            (aid, p["timestamp"], risk, p["mission"], p["action_type"], status, iso(expires),
             json.dumps(p, ensure_ascii=False)))
        self.s.db.commit()
        self.s.log("EXECUTIF", f"proposition_{status}", aid, {"risque": risk})

        if risk == "R0":
            return  # analyse interne : journalisée, rien à envoyer
        if risk == "R1":
            self.tg.send(proposal_text(p, None, "ℹ️ <b>R1 préparé</b> (aucune publication automatique "
                                                "configurée : à publier par toi si pertinent)"))
            return
        if text is None and cold and not header:  # format A
            paras = p["content"]["body"].split("\n\n")
            fact = paras[1] if len(paras) > 1 else ""
            import formats_telegram  # format « EMAIL PRÊT » (décision de JOSY du 13/10/2026)
            text = formats_telegram.email_pret(p["target"].get("email", ""), p["content"].get("subject", ""),
                                               fact, aid)
        if text is None:
            text = (f"{header}\n⏳ {paris(expires)} · /valider {aid[:8]} · /refuser {aid[:8]}"
                    if header else proposal_text(p, expires))
        msg_id = self.tg.send(text,
                              buttons=[{"text": "✅ Valider", "callback_data": f"v:{aid[:8]}"},
                                       {"text": "❌ Refuser", "callback_data": f"r:{aid[:8]}"}])
        if msg_id is None:
            # I2 : sans soumission à JOSY, l'action est refusée d'office.
            self.close(self.s.db.execute("SELECT * FROM proposals WHERE action_id=?", (aid,)).fetchone(),
                       "refuse_non_soumis", "systeme")
            return
        self.s.db.execute("UPDATE proposals SET tg_message_id=? WHERE action_id=?", (msg_id, aid))
        self.s.db.commit()

    # ---------- Rapports ----------
    def status_text(self):
        q = self.s.db.execute
        pending = q("SELECT COUNT(*) FROM proposals WHERE status=?", (PENDING,)).fetchone()[0]
        today = self.s.count_today("SELECT COUNT(*) FROM proposals WHERE created_at>=?")
        calls = self.s.count_today("SELECT COUNT(*) FROM journal WHERE ts>=? AND event='analyse_llm'")
        arts = q("SELECT COUNT(*) FROM articles").fetchone()[0]
        ok, bad = self.s.verify_journal()
        last = self.s.get("last_run")
        return (f"🧠 <b>Cortex</b> : {self.s.get('system_status', 'actif')}\n"
                f"En attente de toi : {pending}\nPropositions aujourd'hui : {today}\n"
                f"Analyses IA ({LLM_PROVIDER}) aujourd'hui : {calls}/{MAX_LLM_CALLS_PER_DAY}\n"
                f"Prochaine mission : {MISSION_ORDER[int(self.s.get('mission_index', '0')) % len(MISSION_ORDER)]}\n"
                f"Articles en mémoire : {arts}\n"
                f"Dernier cycle : {paris(parse_iso(last)) if last else '—'}\n"
                f"Journal : {'intègre' if ok else f'ALTÉRÉ à la ligne {bad}'}")

    def activity_text(self):
        """Résumé des dernières 24 h, tiré du journal."""
        since = iso(now() - timedelta(hours=24))
        rows = self.s.db.execute("SELECT event, details FROM journal WHERE ts>=? AND event IN "
                                 "('analyse_llm_fin','proposition_admise','proposition_rejetee')",
                                 (since,)).fetchall()
        runs = [json.loads(r["details"]) for r in rows if r["event"] == "analyse_llm_fin"]
        missions = ", ".join(dict.fromkeys(d.get("mission", "?") for d in runs)) or "aucune"
        admitted = sum(r["event"] == "proposition_admise" for r in rows)
        rejected = sum(r["event"] == "proposition_rejetee" for r in rows)
        last = runs[-1] if runs else None
        return ("📋 <b>Dernières 24 h</b>\n"
                f"Analyses : {len(runs)} (missions : {html.escape(missions)})\n"
                + (f"Durée de la dernière : {last.get('secondes', '?')} s\n" if last else "")
                + f"Propositions admises : {admitted} · rejetées par le judiciaire : {rejected}")

    def pending_text(self):
        rows = self.s.db.execute("SELECT * FROM proposals WHERE status=? ORDER BY created_at",
                                 (PENDING,)).fetchall()
        if not rows:
            return "Aucune action en attente."
        return "\n".join(f"<code>{r['action_id'][:8]}</code> {r['risk_level']} {r['action_type']} "
                         f"· expire {paris(parse_iso(r['expires_at']))}" for r in rows)

    # ---------- Cycle ----------
    def run(self):
        self.s.log("SYSTEME", "debut_cycle")
        self.refresh_memoire()
        self.poll_telegram()
        self.expire_timeouts()
        if self.s.get("system_status", "actif") == "arrete":
            self.s.log("SYSTEME", "arret_actif_aucune_action")  # I9
        else:
            self.fetch_feeds()
            for p in self.analyze():
                self.dispatch(p)
            try:  # vente : file d'envoi (après clic), réponses, relances, leads chauds
                import vente
                vente.cycle(sys.modules[__name__], self)
            except Exception as exc:
                self.s.log("EXECUTIF", "vente_erreur", details={"erreur": safe_error(exc)})
                alert(self.s, "vente", safe_error(exc))
            try:  # contrôle de démarrage : une fois par jour, liste les clés manquantes (noms seulement)
                import demarrage
                demarrage.notifier(sys.modules[__name__], self)
            except Exception as exc:
                self.s.log("EXECUTIF", "demarrage_erreur", details={"erreur": safe_error(exc)})
            try:  # vie du fondateur : plan du jour, recadrage, questions (I14)
                import fondateur
                fondateur.cycle(sys.modules[__name__], self)
            except Exception as exc:
                self.s.log("EXECUTIF", "fondateur_erreur", details={"erreur": safe_error(exc)})
                alert(self.s, "fondateur", safe_error(exc))
        self.s.set("last_run", iso(now()))
        self.s.log("SYSTEME", "fin_cycle")


def proposal_text(p, expires, header=None):
    risk_icon = {"R1": "🟢", "R2": "🟠", "R3": "🔴"}.get(p["risk_level"], "⚪")
    aid = p["action_id"][:8]
    c = p["content"]
    """Message court (4 lignes au plus) ; le détail complet reste dans le journal local."""
    label = ACTION_LABELS.get(p["action_type"], p["action_type"])
    target = html.escape(p["target"]["company"])
    why = html.escape(re.split(r"(?<=[.!?])\s", p["justification"])[0][:160])
    if header:  # R1 : contenu prêt à publier, à reprendre tel quel
        domains = ", ".join(dict.fromkeys(
            re.sub(r"^https?://(www\.)?", "", s["url"]).split("/")[0] for s in p["sources"]))
        return (f"{header}\n{label} · {why}\n<i>{html.escape(c['body'][:700])}</i>\n"
                f"Sources : {html.escape(domains)}")[:4096]
    lines = [f"{risk_icon} {label} → {target}",
             f"Pourquoi : {why}"]
    if c.get("subject"):
        lines.append(f"Objet : {html.escape(c['subject'])}")
    if expires:
        lines.append(f"⏳ {paris(expires)} · /valider {aid} · /refuser {aid}")
    return "\n".join(lines)[:4096]


ACTION_LABELS = {"cold_email": "Email de prospection", "premier_contact": "Premier contact",
                 "relance": "Relance", "google_post": "Publication Google Business", "article_blog": "Article",
                 "publication": "Publication", "devis": "Devis",
                 "proposition_commerciale": "Proposition commerciale",
                 "amelioration_regle": "Amélioration d'une règle",
                 "proposition_rdv": "Proposition de RDV", "diagnostic": "Diagnostic",
                 "reponse": "Réponse au prospect"}


HELP = ("🧠 <b>Commandes du Cortex</b>\n"
        "/etat : état du système\n/attente : actions en attente\n"
        "/jour : ta journée paramétrée · /ajuste … : la recaler\n"
        "/fait n · /reporte n · /jour off · /profil · /vie …\n"
        "/valider ID : valider une action\n/refuser ID [motif] : refuser\n"
        "/1 /2 /3 ou /r texte : répondre à un prospect\n"
        "/opposition email : ne plus jamais contacter cette adresse\n"
        "/stop : tout arrêter (I9)\n/reprise : relancer\n\n"
        "Tu peux aussi m'écrire librement. Je lis Telegram toutes les 5 min environ "
        "(plus si une analyse est en cours).")

CAPABILITIES = (
    "🧠 <b>Ce que fait le Cortex</b>\n"
    "• Priorité n°1 : ta vie — journée paramétrée, charge réaliste, solutions concrètes. "
    "L'entreprise s'adapte à toi, jamais l'inverse.\n"
    "• Domaines : fiche Google Business (publications), site web, boutique en ligne. Rien d'autre.\n"
    "• Veille : Frandroid, TechCrunch AI, Le Monde Informatique, Google Actualités (IA PME, "
    "RGPD/cyber), CNIL et CERT-FR (ANSSI).\n"
    "• Missions en rotation, une toutes les 30 min : Veille, Prospection, Visibilité, "
    "Relation client, Monétisation.\n"
    "• Prospection : entreprises de l'annuaire officiel (secteurs.json), email professionnel public "
    "et au moins un manque vérifié ; un email court écrit à partir de ce fait, jamais d'un gabarit.\n"
    "• Chaque email de prospection t'est soumis (/valider) ; 10 premiers emails par jour au plus ; "
    "liste d'opposition respectée.\n"
    "• R1 (publication Google Business) : préparée et notifiée. R2 (email) : ta validation, "
    "refus auto à l'expiration. R3 : ta validation.\n"
    "• Journal infalsifiable de chaque action. /stop arrête tout.\n"
    "• Modèle : " + " puis, en repli, ".join(
        f"{p['model']} via {p['name']}" + (" (local, sur ton PC)" if p["name"] == "ollama" else "")
        for p in LLM_CHAIN) + "."
)
FACTUAL_RE = re.compile(r"(que|quoi) (peux|sais)[- ]tu|tu (peux|sais) faire|capacit|"
                        r"fonctionnalit|ce que tu (fais|peux)|\b(é|e)tat\b|statut|status|"
                        r"analyse compl|bilan|r(é|e)sum(é|e) de ton", re.IGNORECASE)

CHAT_PROMPT = (
    "Tu es Le Cortex, l'assistant de JOSY, fondateur de JOSY EI (conseil en visibilité en ligne, "
    "IA, RGPD et automatisation pour TPE/PME, France, priorité Nouvelle-Aquitaine). Ta priorité "
    "absolue est la vie de JOSY : sa journée, son énergie, son argent, sa famille ; l'entreprise "
    "vient après, et c'est elle qui s'adapte à lui. Tu cherches des solutions concrètes, jamais des "
    "constats. Mode "
    "conversation : tu discutes naturellement avec lui sur Telegram, en français, comme un "
    "collègue de confiance : business, tech, idées, ou simplement parler. Réponses courtes et "
    "vivantes (2 à 6 phrases), sans liste, sans JSON, sans Markdown. Tu peux donner ton avis et "
    "argumenter. Appuie-toi sur la mémoire fournie quand elle est utile et cite la fiche "
    "(ex. « d'après la fiche notaires »). Tu ne déclenches aucune action : tu n'envoies, ne "
    "publies et ne paies rien ; pour agir, il utilise les commandes (/valider, /refuser, /stop). "
    "Si tu ne sais pas, dis-le. N'invente ni fait, ni chiffre, ni URL.")
MISSION_RE = re.compile(r"^\s*(fais|lance|envoie|publie|cr[ée]e|trouve|cherche|pr[ée]pare|r[ée]dige)\b",
                        re.IGNORECASE)


def main():
    store = Store(DB_PATH)
    tg = Telegram(TG_TOKEN, TG_CHAT, store)
    try:
        Cortex(store, tg).run()
    except Exception as exc:
        store.log("SYSTEME", "cycle_erreur", details={"erreur": safe_error(exc)})
        alert(store, "cycle", safe_error(exc))
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
