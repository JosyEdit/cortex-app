"""Dossiers d'audit multi-entreprise (tenants), dans audit.db (SQLite), séparé de cortex.db.

Un tenant = une entreprise cliente pour le compte de laquelle le Cortex prospecte (aujourd'hui : JOSY EI).
Un dossier d'audit = un prospect analysé : faits vérifiés, problème principal, email généré, veto du
judiciaire, décision de JOSY, envoi. Chaque requête de lecture filtre par tenant_id (isolation).
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import prompts_audit
import regles_absolues
from regles_absolues import ReglesAbsolues

BASE_DIR = Path(__file__).resolve().parent
AUDIT_DB = Path(os.environ.get("CORTEX_AUDIT_DB", "").strip() or BASE_DIR / "audit.db")
TENANT_JOSY = "JOSY EI"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    nom_entreprise TEXT NOT NULL UNIQUE,
    site_web TEXT,
    fiche_google_url TEXT,
    email_contact TEXT,
    telephone TEXT,
    adresse TEXT,
    signature TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    statut TEXT DEFAULT 'actif'
);
CREATE TABLE IF NOT EXISTS dossiers_audit (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    prospect_nom TEXT NOT NULL,
    prospect_site_web TEXT,
    prospect_fiche_google TEXT,
    prospect_metier TEXT,
    prospect_ville TEXT,
    prospect_email TEXT,
    analyse_site_web TEXT,
    analyse_fiche_google TEXT,
    probleme_principal TEXT,
    impact_business TEXT,
    preuves_verifiables TEXT,
    osint_legal_data TEXT,
    osint_technologies TEXT,
    osint_google_maps TEXT,
    osint_social_profiles TEXT,
    osint_emails_pro TEXT,
    osint_timestamp TEXT,
    osint_purge_date TEXT,
    email_genere TEXT,
    email_valide INTEGER DEFAULT 0,
    motifs_veto TEXT,
    action_id TEXT,
    email_envoye INTEGER DEFAULT 0,
    date_envoi TEXT,
    statut TEXT DEFAULT 'en_cours',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_dossiers_audit_tenant ON dossiers_audit(tenant_id);
CREATE INDEX IF NOT EXISTS idx_dossiers_audit_statut ON dossiers_audit(statut);
CREATE INDEX IF NOT EXISTS idx_dossiers_audit_action ON dossiers_audit(action_id);
CREATE TABLE IF NOT EXISTS journal_judiciaire (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, dossier_id TEXT, message TEXT, prev_hash TEXT, hash TEXT);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, fonction TEXT, cible TEXT, statut TEXT, detail TEXT,
    prev_hash TEXT, hash TEXT);
CREATE TABLE IF NOT EXISTS exclusion (
    id INTEGER PRIMARY KEY AUTOINCREMENT, domaine TEXT, siren TEXT, motif TEXT, date TEXT);
CREATE INDEX IF NOT EXISTS idx_exclusion_domaine ON exclusion(domaine);
CREATE INDEX IF NOT EXISTS idx_exclusion_siren ON exclusion(siren);
"""
# Statuts : en_cours, sans_probleme, exclu, email_nominatif, rejete_veto, attente_validation, valide, refuse,
# expire, non_soumis, envoye, repondu
OSINT_COLONNES = ("osint_legal_data", "osint_technologies", "osint_google_maps", "osint_social_profiles",
                  "osint_emails_pro", "osint_timestamp", "osint_purge_date")
OSINT_CONSERVATION_JOURS = 90  # données OSINT brutes purgées ensuite ; les conclusions restent


def _now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connecter(path=None):
    db = sqlite3.connect(path or AUDIT_DB, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(SCHEMA)
    colonnes = {r[1] for r in db.execute("PRAGMA table_info(dossiers_audit)")}
    for col in OSINT_COLONNES:  # migration d'une base créée avant le module OSINT : ALTER TABLE, jamais DROP
        if col not in colonnes:
            db.execute(f"ALTER TABLE dossiers_audit ADD COLUMN {col} TEXT")
    db.commit()
    return db


def migrer(path=None):
    """Création des tables (idempotente). Renvoie la liste des tables présentes."""
    db = connecter(path)
    tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    db.close()
    return tables


# ----------------------------------------------------------------- faits vérifiés -> preuves
def preuves_depuis_audit(a):
    """Preuves exigées par le judiciaire, tirées de l'analyse (audit.audit_prospect). None sans fait
    Google Maps vérifié : pas d'email (règle de JOSY du 14/10/2026)."""
    detail = (a or {}).get("manques_detail") or []
    g = ((a or {}).get("site") or {}).get("google_maps") or {}
    if not detail or not g:
        return None
    fait, sorte = detail[0][0], detail[0][1]
    nom = ((a.get("entreprise") or {}).get("nom")) or ""
    if sorte == "concurrents" and g.get("premier"):
        premier = g["premier"]
        obligatoires = [premier["nom"], str(premier["avis"])]
        chiffres = [premier["avis"], g.get("total"), premier["nom"]]
    elif sorte == "avis" and g.get("prospect"):
        obligatoires = [str(g["prospect"]["avis"]), str(g["moyenne_avis"])]
        chiffres = [g["prospect"]["avis"], g["moyenne_avis"], g.get("nb_autres")]
    else:
        return None
    return {"fait": fait, "type": sorte, "source": g.get("source", "Google Maps (Serper)"),
            "requete": g.get("requete"), "elements_obligatoires": obligatoires,
            "chiffres_autorises": [str(x) for x in chiffres + [g.get("requete"), nom] if x not in (None, "")]}


def _resume_site(site):
    if not site.get("joignable"):
        return "Site : non lu (introuvable ou injoignable), rien n'est affirmé."
    oui = lambda v: "oui" if v else "non"  # noqa: E731
    return (f"Site {site.get('url_finale')} : HTTPS {oui(site.get('https'))}, version mobile "
            f"{oui(site.get('mobile'))}, description Google {oui(site.get('meta_description'))}, "
            f"mentions légales {oui(site.get('mentions_legales') or site.get('page_mentions'))}.")


def _resume_google(g):
    if not g:
        return "Fiche Google : non vérifiée."
    if g.get("prospect"):
        return (f"Google Maps « {g['requete']} » : rang {g['rang']} sur {g['total']}, "
                f"{g['prospect']['avis']} avis (moyenne des autres : {g.get('moyenne_avis')}).")
    return (f"Google Maps « {g['requete']} » : absente des {g['total']} premiers résultats ; 1er : "
            f"{g['premier']['nom']} ({g['premier']['avis']} avis).")


def synthese_osint(o):
    """Ce que l'OSINT ajoute aux preuves : données légales, technologies, réseaux, Google Maps (Serper)."""
    legal = o.get("legal_data") or {}
    return {"legal": {k: legal.get(k) for k in ("siren", "activite", "date_creation", "source") if legal.get(k)}
            | ({"dirigeants": [d.get("qualite") for d in legal.get("dirigeants") or []]} if legal.get("dirigeants") else {}),
            "technologies": [t["nom"] for t in (o.get("technologies") or {}).get("technologies", [])][:10],
            "reseaux": [p["plateforme"] for p in (o.get("social_profiles") or {}).get("plateformes", [])][:10],
            "google_maps": (o.get("google_maps") or {}).get("status"),
            "collecte": o.get("timestamp")}


def _resume_osint(o):
    if not o:
        return ""
    s = synthese_osint(o)
    parts = []
    if s["technologies"]:
        parts.append("technologies visibles : " + ", ".join(s["technologies"]))
    if s["reseaux"]:
        parts.append("présence de la marque sur : " + ", ".join(s["reseaux"]))
    if o.get("emails_pro"):
        parts.append(f"{len(o['emails_pro'])} adresse(s) générique(s) publiée(s)")
    if s["legal"].get("activite"):
        parts.append(f"activité déclarée {s['legal']['activite']}")
    erreurs = [e.get("etape") for e in o.get("erreurs") or []]
    if erreurs:
        parts.append("non vérifié : " + ", ".join(erreurs))
    return (" OSINT : " + " ; ".join(parts) + ".") if parts else ""


class DossierAuditManager:
    def __init__(self, db_connection=None):
        self.db = db_connection if isinstance(db_connection, sqlite3.Connection) else connecter(db_connection)

    # ---------- tenants ----------
    def assurer_tenant(self, nom_entreprise, **champs):
        row = self.db.execute("SELECT id FROM tenants WHERE nom_entreprise=?", (nom_entreprise,)).fetchone()
        if row:
            return row["id"]
        tid = str(uuid.uuid4())
        cols = ["id", "nom_entreprise"] + [k for k in champs if k in
                                           ("site_web", "fiche_google_url", "email_contact", "signature")]
        self.db.execute(f"INSERT INTO tenants({', '.join(cols)}) VALUES({', '.join('?' * len(cols))})",
                        [tid, nom_entreprise] + [champs[k] for k in cols[2:]])
        self.db.commit()
        return tid

    def tenant(self, tenant_id):
        row = self.db.execute("SELECT * FROM tenants WHERE id=?", (tenant_id,)).fetchone()
        return dict(row) if row else None

    # ---------- dossiers ----------
    def creer_dossier_audit(self, tenant_id: str, prospect_data: dict) -> str:
        """Crée un nouveau dossier d'audit pour un prospect."""
        dossier_id = str(uuid.uuid4())
        self.db.execute("""
            INSERT INTO dossiers_audit
            (id, tenant_id, prospect_nom, prospect_site_web, prospect_fiche_google,
             prospect_metier, prospect_ville, prospect_email, statut, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'en_cours', ?, ?)
        """, (dossier_id, tenant_id, prospect_data["nom"], prospect_data.get("site_web"),
              prospect_data.get("fiche_google") or prospect_data.get("fiche_google_url"),
              prospect_data.get("metier"), prospect_data.get("ville"),
              prospect_data.get("email_contact") or prospect_data.get("email"), _now(), _now()))
        self.db.commit()
        return dossier_id

    def obtenir(self, dossier_id):
        row = self.db.execute("SELECT * FROM dossiers_audit WHERE id=?", (dossier_id,)).fetchone()
        return dict(row) if row else None

    def enregistrer_analyse(self, dossier_id, a, osint=None):
        """Analyse (audit.audit_prospect) et résultat OSINT -> champs du dossier. Le fait vérifié qui ouvre un
        email reste celui de Google Maps (Serper) ; l'OSINT complète l'analyse et les preuves."""
        site = a.get("site") or {}
        preuves = preuves_depuis_audit(a)
        if preuves and osint:
            preuves["osint"] = synthese_osint(osint)
        probleme = preuves["fait"] if preuves else None
        impact = None
        if preuves:
            import audit
            impact = audit.WHY.get(preuves["type"])
        ent = a.get("entreprise") or {}
        self.db.execute("""
            UPDATE dossiers_audit
            SET analyse_site_web=?, analyse_fiche_google=?, probleme_principal=?, impact_business=?,
                preuves_verifiables=?, prospect_metier=COALESCE(prospect_metier, ?),
                prospect_site_web=COALESCE(prospect_site_web, ?), statut=?, updated_at=?
            WHERE id=?
        """, (_resume_site(site) + _resume_osint(osint), _resume_google(site.get("google_maps")), probleme, impact,
              json.dumps(preuves, ensure_ascii=False) if preuves else None, ent.get("metier"),
              site.get("url_finale"), "en_cours" if preuves else "sans_probleme", _now(), dossier_id))
        if osint:
            from datetime import timedelta
            ts = osint.get("timestamp") or _now()
            purge = (datetime.fromisoformat(ts) + timedelta(days=OSINT_CONSERVATION_JOURS)).isoformat()
            j = lambda v: json.dumps(v, ensure_ascii=False) if v is not None else None  # noqa: E731
            self.db.execute("UPDATE dossiers_audit SET osint_legal_data=?, osint_technologies=?, osint_google_maps=?, "
                            "osint_social_profiles=?, osint_emails_pro=?, osint_timestamp=?, osint_purge_date=? "
                            "WHERE id=?", (j(osint.get("legal_data")), j(osint.get("technologies")),
                                           j(osint.get("google_maps")), j(osint.get("social_profiles")),
                                           j(osint.get("emails_pro")), ts, purge, dossier_id))
        self.db.commit()
        return {"analyse_site": _resume_site(site) + _resume_osint(osint),
                "analyse_google": _resume_google(site.get("google_maps")), "probleme": probleme, "preuves": preuves,
                "osint": osint}

    def analyser_prospect(self, dossier_id: str, analyseur=None, osint=None) -> dict:
        """Lance l'analyse complète du prospect : site, Google Maps (Serper), annuaire officiel, puis OSINT
        (osint_tools.run_full_osint_audit). `osint` : fonction simulée (tests) ou False pour s'en passer."""
        d = self.obtenir(dossier_id)
        import audit
        row = {"nom": d["prospect_nom"], "ville": d["prospect_ville"] or "", "email": d["prospect_email"] or "",
               "site": d["prospect_site_web"]}
        a = (analyseur or audit.audit_prospect)(row)
        return self.enregistrer_analyse(dossier_id, a, self.collecter_osint(dossier_id, a, osint))

    def collecter_osint(self, dossier_id, a, osint=None):
        if osint is False:
            return None
        d = self.obtenir(dossier_id)
        import osint_tools
        site = (a.get("site") or {}).get("url_finale") or d["prospect_site_web"]
        siren = (((a.get("entreprise") or {}).get("officiel")) or {}).get("siren", "")
        try:
            return (osint or osint_tools.run_full_osint_audit)(d["prospect_nom"], site, siren)
        except Exception as exc:  # noqa: BLE001  l'OSINT ne bloque jamais l'audit
            return {"erreurs": [{"etape": "osint", "detail": type(exc).__name__}], "timestamp": _now()}

    # ---------- exclusion (F1.6) et purge (90 jours) ----------
    def exclure(self, domaine=None, siren=None, motif=""):
        self.db.execute("INSERT INTO exclusion(domaine, siren, motif, date) VALUES(?,?,?,?)",
                        ((domaine or "").lower().removeprefix("www.") or None, siren or None, motif, _now()))
        self.db.commit()

    def est_exclu(self, email=None, siren=None, site=None):
        domaines = {x for x in ((email or "").split("@")[-1].lower() if email and "@" in email else "",
                                (site or "").lower().split("//")[-1].split("/")[0].removeprefix("www.")) if x}
        for dom in domaines:
            if self.db.execute("SELECT 1 FROM exclusion WHERE domaine=?", (dom,)).fetchone():
                return True
        return bool(siren and self.db.execute("SELECT 1 FROM exclusion WHERE siren=?", (siren,)).fetchone())

    def purger_osint(self, jours=OSINT_CONSERVATION_JOURS):
        """Données OSINT brutes et preuves détaillées effacées après `jours` ; problème, impact et analyse
        synthétique restent. Renvoie le nombre de dossiers purgés."""
        from datetime import timedelta
        maintenant = datetime.now(timezone.utc).replace(microsecond=0)
        limite = (maintenant - timedelta(days=jours)).isoformat()
        bruts = ", ".join(f"{c}=NULL" for c in OSINT_COLONNES[:5])
        cur = self.db.execute(f"UPDATE dossiers_audit SET {bruts}, preuves_verifiables=NULL, updated_at=? "
                              "WHERE osint_timestamp IS NOT NULL AND (osint_purge_date<? OR osint_timestamp<?) "
                              "AND (osint_legal_data IS NOT NULL OR preuves_verifiables IS NOT NULL)",
                              (_now(), maintenant.isoformat(), limite))
        self.db.commit()
        return cur.rowcount

    def contexte_validation(self, dossier_id):
        d = self.obtenir(dossier_id)
        t = self.tenant(d["tenant_id"]) or {}
        return dict(d, signature=t.get("signature") or "", email_tenant=t.get("email_contact") or
                    ReglesAbsolues.SIGNATURE_EMAIL)

    def generer_email_audit(self, dossier_id: str, llm=None) -> str:
        """Génère l'email d'audit du dossier, puis le soumet au veto du judiciaire."""
        dossier = self.obtenir(dossier_id)
        tenant = self.tenant(dossier["tenant_id"]) or {}
        preuves = json.loads(dossier["preuves_verifiables"] or "null")
        tenant_context = {"nom_tenant": tenant.get("nom_entreprise"), "signature": tenant.get("signature") or "",
                          "analyse_site_web": dossier["analyse_site_web"] or "",
                          "analyse_fiche_google": dossier["analyse_fiche_google"] or "",
                          "fuites_acquisition_detectees": [dossier["probleme_principal"]] if dossier["probleme_principal"] else [],
                          "preuves_verifiables": preuves or {}}
        prospect_data = {"nom": dossier["prospect_nom"], "site_web": dossier["prospect_site_web"],
                         "fiche_google_url": dossier["prospect_fiche_google"], "metier": dossier["prospect_metier"],
                         "ville": dossier["prospect_ville"]}
        email = prompts_audit.generer_email_audit(tenant_context, prospect_data, llm=llm) if preuves else ""
        contexte = self.contexte_validation(dossier_id)
        motifs = ReglesAbsolues.motifs(email, contexte) if email else ["VETO: aucun email produit"]
        for m in motifs:
            regles_absolues.log_judiciaire(m, dossier_id)
        regles_absolues.log_judiciaire("ADMIS" if not motifs else "REJETE", dossier_id)
        self.db.execute("""
            UPDATE dossiers_audit
            SET email_genere=?, email_valide=?, motifs_veto=?, statut=?, updated_at=?
            WHERE id=?
        """, (email, int(not motifs), json.dumps(motifs, ensure_ascii=False),
              "rejete_veto" if motifs else "en_cours", _now(), dossier_id))
        self.db.commit()
        return email

    def maj_statut(self, dossier_id, statut, **champs):
        sets = ", ".join(["statut=?", "updated_at=?"] + [f"{k}=?" for k in champs])
        self.db.execute(f"UPDATE dossiers_audit SET {sets} WHERE id=?",
                        [statut, _now()] + list(champs.values()) + [dossier_id])
        self.db.commit()

    def maj_par_action(self, action_id, statut, **champs):
        row = self.db.execute("SELECT id FROM dossiers_audit WHERE action_id=?", (action_id,)).fetchone()
        if row:
            self.maj_statut(row["id"], statut, **champs)
        return bool(row)

    def lister_dossiers_par_tenant(self, tenant_id: str) -> list:
        """Liste tous les dossiers d'audit d'un tenant (isolation)."""
        return [dict(r) for r in self.db.execute("""
            SELECT * FROM dossiers_audit
            WHERE tenant_id = ?
            ORDER BY created_at DESC
        """, (tenant_id,))]

    def close(self):
        self.db.close()


def maj_par_action(action_id, statut, path=None, **champs):
    """Raccourci pour le Cortex et vente.py : met à jour le dossier lié à une proposition, s'il existe."""
    if not action_id:
        return False
    m = DossierAuditManager(path)
    try:
        return m.maj_par_action(action_id, statut, **champs)
    finally:
        m.close()


def signature_tenant_josy():
    import cortex
    return cortex.SIGNATURE
