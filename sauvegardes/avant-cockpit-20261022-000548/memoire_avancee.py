"""Catégorie 1 : mémoire avancée du Cortex (fonctionnalités 1 à 5).

1. épisodique  : table `episodes` (date, entreprise, action, résultat) ; rappel « la dernière fois… ».
2. sémantique  : table `faits` (faits, règles métier, préférences) séparée des épisodes.
3. de travail  : table `memoire_travail`, vidée à la fin de chaque cycle (mission).
4. de saillance: chaque épisode a un score ; `importants()` liste les plus saillants.
5. portabilité : `exporter()` / `importer()` en JSON (toutes les tables de cortex.db, journal compris).
Rien n'est inventé : tout vient d'événements réellement enregistrés.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, entreprise TEXT, action TEXT, resultat TEXT,
  salience INTEGER DEFAULT 1);
CREATE INDEX IF NOT EXISTS idx_episodes_ent ON episodes(entreprise);
CREATE TABLE IF NOT EXISTS faits (
  cle TEXT PRIMARY KEY, valeur TEXT, source TEXT, maj_le TEXT);
CREATE TABLE IF NOT EXISTS memoire_travail (
  mission TEXT, cle TEXT, valeur TEXT, PRIMARY KEY (mission, cle));
"""

# Saillance : événements qui comptent (échelle 1 à 5)
SALIENCE = {"envoi": 1, "reponse": 3, "interesse": 5, "stop": 4, "pas_interesse": 3,
            "mecontent": 5, "erreur_critique": 5, "relance": 1}

# Faits décidés par JOSY (source : ses messages du 13/10/2026) ; aucun autre fait n'est préchargé.
FAITS_INITIAUX = {
    "zone": ("France uniquement (métropole et DOM-TOM), francophone", "JOSY, 13/10/2026"),
    "emails_par_jour": ("30 premiers emails par jour au plus", "JOSY, 19/10/2026 10:29 (option B)"),
    "signature": ("LE CORTEX par JOSY EI, SIREN 914 113 543, Montmorillon (86), France.", "JOSY, 13/10/2026"),
    "contact": ("Tout par email : aucun appel, aucune visio, aucun rendez-vous", "JOSY, 13/10/2026"),
    "zero_prix": ("Aucun prix ni abonnement dans aucun contenu ; seul un audit gratuit est proposé",
                  "JOSY, 19/10/2026"),
    "domaines": ("Publication Google Business, site web, boutique en ligne", "JOSY, 13/10/2026"),
}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def setup(store):
    store.db.executescript(SCHEMA)
    for cle, (valeur, source) in FAITS_INITIAUX.items():
        store.db.execute("INSERT OR IGNORE INTO faits VALUES(?,?,?,?)", (cle, valeur, source, _now()))
    store.db.commit()


# ---------------------------------------------------------------- 1. épisodique
def enregistrer(store, entreprise, action, resultat="", evenement=None):
    """Mémorise un épisode ; `evenement` fixe la saillance (clé de SALIENCE)."""
    setup(store)
    store.db.execute("INSERT INTO episodes(ts, entreprise, action, resultat, salience) VALUES(?,?,?,?,?)",
                     (_now(), entreprise, action[:200], resultat[:300], SALIENCE.get(evenement, 1)))
    store.db.commit()


def rappel(store, entreprise, n=5):
    """« La dernière fois… » : les n derniers épisodes de cette entreprise, du plus récent au plus ancien."""
    setup(store)
    rows = store.db.execute("SELECT ts, action, resultat FROM episodes WHERE lower(entreprise) LIKE ? "
                            "ORDER BY id DESC LIMIT ?", (f"%{entreprise.lower()}%", n)).fetchall()
    if not rows:
        return f"Aucun épisode enregistré pour « {entreprise} »."
    return "\n".join(f"{r['ts'][:10]} : {r['action']}" + (f" → {r['resultat']}" if r["resultat"] else "")
                     for r in rows)


# ---------------------------------------------------------------- 2. sémantique
def definir_fait(store, cle, valeur, source="JOSY"):
    setup(store)
    store.db.execute("INSERT INTO faits VALUES(?,?,?,?) ON CONFLICT(cle) DO UPDATE SET valeur=excluded.valeur, "
                     "source=excluded.source, maj_le=excluded.maj_le", (cle.strip()[:60], valeur.strip()[:500], source, _now()))
    store.db.commit()


def faits(store):
    setup(store)
    return {r["cle"]: r["valeur"] for r in store.db.execute("SELECT cle, valeur FROM faits ORDER BY cle")}


# ---------------------------------------------------------------- 3. de travail
def travail_definir(store, mission, cle, valeur):
    setup(store)
    store.db.execute("INSERT OR REPLACE INTO memoire_travail VALUES(?,?,?)", (mission, cle, str(valeur)[:500]))
    store.db.commit()


def travail_lire(store, mission):
    setup(store)
    return {r["cle"]: r["valeur"] for r in store.db.execute(
        "SELECT cle, valeur FROM memoire_travail WHERE mission=?", (mission,))}


def travail_vider(store, mission=None):
    """Appelée à la fin de chaque mission : la mémoire de travail ne survit pas à la tâche."""
    setup(store)
    if mission:
        store.db.execute("DELETE FROM memoire_travail WHERE mission=?", (mission,))
    else:
        store.db.execute("DELETE FROM memoire_travail")
    store.db.commit()


# ---------------------------------------------------------------- 4. saillance
def importants(store, n=5, depuis_jours=30):
    setup(store)
    rows = store.db.execute(
        "SELECT ts, entreprise, action, resultat, salience FROM episodes "
        "WHERE ts >= datetime('now', ?) ORDER BY salience DESC, id DESC LIMIT ?",
        (f"-{int(depuis_jours)} days", n)).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------- 5. portabilité
def exporter(store, chemin):
    """Export complet de cortex.db en JSON (toutes les tables, tous les champs)."""
    db = store.db
    tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE "
                                       "'sqlite_%' ORDER BY name")]
    out = {"format": "cortex-export-v1", "date": _now(), "tables": {}}
    for t in tables:
        cur = db.execute(f"SELECT * FROM {t}")
        cols = [d[0] for d in cur.description]
        out["tables"][t] = {"colonnes": cols, "lignes": [list(r) for r in cur.fetchall()],
                            "schema": db.execute("SELECT sql FROM sqlite_master WHERE name=?", (t,)).fetchone()[0]}
    Path(chemin).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return {t: len(v["lignes"]) for t, v in out["tables"].items()}


def importer(chemin, db_destination):
    """Import dans une base NEUVE (refuse d'écraser une base qui contient déjà des données).
    Renvoie (nombre de lignes, journal_intègre)."""
    data = json.loads(Path(chemin).read_text(encoding="utf-8"))
    if data.get("format") != "cortex-export-v1":
        raise ValueError("format d'export inconnu")
    dest = Path(db_destination)
    if dest.exists() and dest.stat().st_size > 0:
        raise FileExistsError("la base de destination n'est pas vide : import refusé (aucun écrasement)")
    db = sqlite3.connect(dest)
    total = 0
    for t, d in data["tables"].items():
        db.execute(d["schema"])
        marks = ",".join("?" * len(d["colonnes"]))
        db.executemany(f"INSERT INTO {t}({','.join(d['colonnes'])}) VALUES({marks})", d["lignes"])
        total += len(d["lignes"])
    db.commit()
    ok = True
    if "journal" in data["tables"]:
        import hashlib
        prev = "GENESIS"
        for r in db.execute("SELECT ts, power, event, action_id, details, prev_hash, hash FROM journal ORDER BY id"):
            digest = hashlib.sha256(f"{prev}|{r[0]}|{r[1]}|{r[2]}|{r[3] or ''}|{r[4]}".encode()).hexdigest()
            if r[5] != prev or r[6] != digest:
                ok = False
                break
            prev = r[6]
    db.close()
    return total, ok
