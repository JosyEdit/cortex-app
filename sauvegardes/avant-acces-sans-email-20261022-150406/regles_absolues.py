"""JUDICIAIRE — règles absolues des emails d'audit (décision de JOSY, 19/10/2026).

Contrôle déterministe, sans modèle de langage, appliqué à tout email avant sa soumission à JOSY sur
Telegram, puis de nouveau avant l'envoi (vente.process_queue) :
  1. zéro prix : aucun montant (€, EUR, euros), aucun mot commercial (prix, tarif, coût, abonnement,
     forfait, mensuel, annuel, offre, promotion, réduction, remise) ;
  2. zéro contact direct : ni appel, ni rendez-vous, ni visio, ni téléphone (tout se fait par email) ;
  3. signature complète de l'émetteur (SIREN, contact@josyei.com, mention RGPD et désinscription STOP) ;
  4. argument vérifié : le fait cité vient de Google Maps (Serper) ou de l'analyse publique du dossier,
     et aucun chiffre du texte n'est inventé.

Zéro prix (décision du 19/10/2026, 10:01) : mots entiers sans accents, plus la liste MOTS_INTERDITS_SOUS_CHAINE
cherchée en sous-chaîne comme JOSY l'a demandé (« solde », « promo », « pack », « formule » ajoutés), montants
« par mois / par an », et « gratuit » interdit dans l'objet. La sous-chaîne attrape aussi « écouter », « offrent »,
« coffre », « package », « formuler » : faux positifs connus, préférés à un prix qui passerait.
Contact direct : mots entiers sans accents (« rappel » passe).
Chaque veto est consigné dans audit.db (table journal_judiciaire, lignes chaînées par sha256, I1).
"""

import hashlib
import json
import os
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIT_DB = Path(os.environ.get("CORTEX_AUDIT_DB", "").strip() or BASE_DIR / "audit.db")

MOTS_INTERDITS = ("prix", "tarif", "cout", "abonnement", "forfait", "mensuel", "annuel",
                  "offre", "promotion", "reduction", "remise")
_MOTS_RE = re.compile(r"\b(prix|tarifs?|couts?|abonnements?|forfaits?|mensuel(?:le)?s?|annuel(?:le)?s?|"
                      r"offres?|promotions?|reductions?|remises?)\b")
# Décision JOSY 19/10/2026 (10:01), appliquée telle quelle : recherche par sous-chaîne dans le texte en
# minuscules (« offre » est aussi trouvé dans « offrent », « cout » dans « écouter », « pack » dans « package »).
MOTS_INTERDITS_SOUS_CHAINE = (
    "prix", "tarif", "coût", "cout", "abonnement", "forfait", "mensuel", "annuel", "offre", "promotion",
    "réduction", "remise", "solde", "promo", "pack", "formule")
PATTERNS_PRIX = (
    r"\d+[,.]?\d*\s*€",
    r"\d+[,.]?\d*\s*EUR\b",
    r"€\s*\d+[,.]?\d*",
    r"\d+[,.]?\d*\s*euros?\b",
    r"\d+[,.]?\d*\s*par\s*mois",
    r"\d+[,.]?\d*\s*par\s*an\b",
    r"€",
)
_OBJET_RE = re.compile(r"^\s*Objet\s*:(.*)$", re.I | re.M)
_CONTACT_RE = re.compile(r"\b(rendez[- ]?vous|rdv|appel\w*|call|calls|meeting|visio\w*|"
                         r"telephone\w*|telephoni\w*|creneau\w*|rencontr\w*)\b")
MAX_LIGNES = 15  # règle de JOSY (13/10/2026), signature comprise


def sans_accents(texte):
    """Minuscules sans accents, apostrophes typographiques normalisées."""
    t = unicodedata.normalize("NFKD", str(texte or "")).replace("’", "'").replace("œ", "oe")
    return "".join(ch for ch in t if not unicodedata.combining(ch)).lower()


# ----------------------------------------------------------------- journal judiciaire (audit.db)
def _now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log_judiciaire(message, dossier_id=None, db_path=None):
    """Journal append-only du veto (une ligne par décision, chaînée à la précédente)."""
    try:
        db = sqlite3.connect(db_path or AUDIT_DB, timeout=30)
        db.execute("CREATE TABLE IF NOT EXISTS journal_judiciaire (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                   "ts TEXT, dossier_id TEXT, message TEXT, prev_hash TEXT, hash TEXT)")
        row = db.execute("SELECT hash FROM journal_judiciaire ORDER BY id DESC LIMIT 1").fetchone()
        prev, ts = (row[0] if row else "GENESIS"), _now()
        digest = hashlib.sha256(f"{prev}|{ts}|{dossier_id or ''}|{message}".encode()).hexdigest()
        db.execute("INSERT INTO journal_judiciaire(ts, dossier_id, message, prev_hash, hash) VALUES(?,?,?,?,?)",
                   (ts, dossier_id, str(message)[:500], prev, digest))
        db.commit()
        db.close()
    except sqlite3.Error:
        pass  # le veto reste appliqué même si la trace échoue


# ----------------------------------------------------------------- 1. zéro prix
def motifs_zero_prix(email_content):
    motifs = []
    texte_bas = str(email_content or "").lower()
    trouves = list(dict.fromkeys(m.group(0) for m in _MOTS_RE.finditer(sans_accents(email_content))))
    trouves += [mot for mot in MOTS_INTERDITS_SOUS_CHAINE if mot in texte_bas]
    for mot in dict.fromkeys(trouves):
        motifs.append(f"VETO: email contient mot interdit '{mot}'")
    objet = _OBJET_RE.search(str(email_content or ""))
    if objet and "gratuit" in sans_accents(objet.group(1)):  # filtres anti-spam
        motifs.append("VETO: mot 'gratuit' dans l'objet")
    for pattern in PATTERNS_PRIX:
        if re.search(pattern, str(email_content or ""), re.IGNORECASE):
            motifs.append(f"VETO: email contient pattern de prix '{pattern}'")
            break
    return motifs


def valider_email_audit(email_content: str) -> bool:
    """Veto Judiciaire : bloque tout email contenant un prix ou une offre commerciale."""
    motifs = motifs_zero_prix(email_content)
    for m in motifs:
        log_judiciaire(m)
    return not motifs


# ----------------------------------------------------------------- règles absolues
def _avant_signature(texte, signature):
    if signature and signature.split("\n")[0] in texte:
        return texte.split(signature.split("\n")[0])[0]
    return texte


def _nombres(texte):
    """Nombres d'un texte, séparateurs de milliers retirés (« 1 250 » -> « 1250 »)."""
    return {re.sub(r"[\s.,  ]", "", n)
            for n in re.findall(r"\d{1,3}(?:[   .]\d{3})+(?!\d)|\d+(?:[.,]\d+)?", texte or "")}


class ReglesAbsolues:
    # Communication
    CANAL_UNIQUE = "email"  # zéro RDV, zéro appel
    SIGNATURE_EMAIL = "contact@josyei.com"

    # Validation
    VALIDATION_TELEGRAM_OBLIGATOIRE = True
    ARGUMENT_VERIFIE_OBLIGATOIRE = True
    ZERO_PRIX_OBLIGATOIRE = True

    # Périmètre (les sources de prospects actuelles couvrent la France : annuaire Sirene)
    PERIMETRE_GEOGRAPHIQUE = "Europe"

    @staticmethod
    def motifs(email_content, contexte):
        """Liste des motifs de veto ; vide = email conforme. `contexte` : dossier d'audit (dict) avec
        `preuves_verifiables` (dict ou JSON), `signature` et `email_tenant` facultatifs."""
        contexte = contexte or {}
        texte = str(email_content or "")
        signature = contexte.get("signature") or ""
        motifs = motifs_zero_prix(texte)
        corps = _avant_signature(texte, signature)
        if _CONTACT_RE.search(sans_accents(corps)):
            motifs.append("VETO: email propose RDV ou appel")
        adresse = contexte.get("email_tenant") or ReglesAbsolues.SIGNATURE_EMAIL
        if adresse not in texte or (signature and signature not in texte):
            motifs.append("VETO: signature absente")
        if not re.search(r"\bSTOP\b", texte):
            motifs.append("VETO: lien de désinscription absent")
        if len(re.sub(r"^\s*Objet\s*:[^\n]*\n+", "", texte).strip().splitlines()) > MAX_LIGNES:
            motifs.append(f"VETO: email de plus de {MAX_LIGNES} lignes")
        if not ReglesAbsolues._verifier_argument_concret(texte, contexte):
            motifs.append("VETO: argument non vérifiable")
        return motifs

    @staticmethod
    def valider_email_complet(email_content: str, tenant_context: dict) -> bool:
        """Veto Judiciaire complet : vérifie toutes les règles absolues."""
        motifs = ReglesAbsolues.motifs(email_content, tenant_context)
        for m in motifs:
            log_judiciaire(m, (tenant_context or {}).get("id"))
        return not motifs

    @staticmethod
    def _verifier_argument_concret(email_content: str, tenant_context: dict) -> bool:
        """L'email cite le fait vérifié du dossier (concurrent et nombre d'avis Google Maps, ou nombre
        d'avis du prospect et moyenne locale) et ne contient aucun chiffre absent des preuves."""
        preuves = (tenant_context or {}).get("preuves_verifiables") or {}
        if isinstance(preuves, str):
            try:
                preuves = json.loads(preuves)
            except ValueError:
                return False
        obligatoires = [str(x) for x in preuves.get("elements_obligatoires") or [] if str(x).strip()]
        if not preuves.get("fait") or not obligatoires:
            return False
        corps = _avant_signature(str(email_content or ""), (tenant_context or {}).get("signature") or "")
        plat = re.sub(r"\s+", " ", sans_accents(corps))
        nombres_corps = _nombres(corps)
        for element in obligatoires:
            if element.isdigit():
                if element not in nombres_corps:
                    return False
            elif re.sub(r"\s+", " ", sans_accents(element)) not in plat:
                return False
        autorises = {"1"}  # « 1er résultat »
        for x in list(preuves.get("chiffres_autorises") or []) + obligatoires:
            autorises |= _nombres(str(x))
        return _nombres(corps) <= autorises
