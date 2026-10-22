"""Synchronisation du schéma des bases (cortex.db, audit.db) avec le code : ALTER TABLE uniquement.

Le schéma de référence est celui que le code déclare (cortex.SCHEMA, dossier_audit_manager.SCHEMA,
vente.SCHEMA, cycle_emails.SCHEMA), rejoué dans une base en mémoire. Pour chaque table qui existe déjà
dans la vraie base, chaque colonne manquante est ajoutée par ALTER TABLE ... ADD COLUMN.

Jamais de DROP, jamais de CREATE sur une table existante, jamais de colonne retirée ni renommée.
Une table absente est seulement signalée : le module qui la possède la crée lui-même (IF NOT EXISTS).
Simulation par défaut : rien n'est écrit sans --appliquer.

    python schema_sync.py chemin\\cortex.db              # liste ce qui manque
    python schema_sync.py chemin\\cortex.db --appliquer  # ajoute les colonnes manquantes
"""

import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def schemas_reference():
    """Scripts CREATE déclarés par le code (modules importés sans effet de bord)."""
    scripts = []
    for nom in ("cortex", "dossier_audit_manager", "vente", "cycle_emails"):
        try:
            mod = __import__(nom)
        except Exception:
            continue
        s = getattr(mod, "SCHEMA", None)
        if isinstance(s, str):
            scripts.append(s)
    return scripts


def colonnes_reference(scripts):
    ref = sqlite3.connect(":memory:")
    for s in scripts:
        try:
            ref.executescript(s)
        except sqlite3.Error:
            pass
    out = {}
    for (table,) in ref.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        out[table] = [(r[1], r[2] or "TEXT", r[4]) for r in ref.execute(f"PRAGMA table_info('{table}')")]
    ref.close()
    return out


def _defaut_ajoutable(defaut):
    """ADD COLUMN n'accepte qu'un défaut constant (pas CURRENT_TIMESTAMP)."""
    if defaut is None:
        return ""
    if re.fullmatch(r"-?\d+(\.\d+)?|'[^']*'|NULL", str(defaut).strip(), re.I):
        return f" DEFAULT {defaut}"
    return ""


def synchroniser(db_path, appliquer=False, scripts=None):
    """Renvoie {"ajoutees": [...], "tables_absentes": [...]} ; écrit seulement si appliquer."""
    reference = colonnes_reference(scripts if scripts is not None else schemas_reference())
    db = sqlite3.connect(db_path, timeout=30)
    presentes = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    ajoutees, absentes = [], []
    for table, colonnes in reference.items():
        if table not in presentes:
            absentes.append(table)
            continue
        existantes = {r[1] for r in db.execute(f"PRAGMA table_info('{table}')")}
        for nom, typ, defaut in colonnes:
            if nom in existantes:
                continue
            ordre = f"ALTER TABLE \"{table}\" ADD COLUMN \"{nom}\" {typ}{_defaut_ajoutable(defaut)}"
            assert ordre.upper().startswith("ALTER TABLE") and " DROP " not in ordre.upper()
            if appliquer:
                db.execute(ordre)
            ajoutees.append(ordre)
    if appliquer:
        db.commit()
    db.close()
    return {"ajoutees": ajoutees, "tables_absentes": absentes}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    r = synchroniser(sys.argv[1], appliquer="--appliquer" in sys.argv)
    print(("Appliqué" if "--appliquer" in sys.argv else "Simulation") + f" : {len(r['ajoutees'])} colonne(s)")
    for o in r["ajoutees"]:
        print("  " + o)
    if r["tables_absentes"]:
        print("Tables absentes (créées par leur module, non touchées) : " + ", ".join(r["tables_absentes"]))
