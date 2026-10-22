"""Migration du schéma pour le module OSINT : ALTER TABLE uniquement, colonnes testées avant ajout.

- audit.db : ajoute à dossiers_audit les colonnes OSINT manquantes (osint_legal_data, osint_technologies,
  osint_google_maps, osint_social_profiles, osint_emails_pro, osint_timestamp, osint_purge_date).
  Si audit.db ou la table n'existent pas encore (première mise en service), elles sont créées par
  dossier_audit_manager (CREATE TABLE IF NOT EXISTS : aucune table existante n'est touchée).
- cortex.db : schema_sync.py ajoute les colonnes que le code déclare et que la base n'a pas.
Jamais de DROP, jamais de colonne retirée ou renommée, jamais de CREATE sur une table existante.

    python migrate_osint_schema.py [dossier]               # applique (dossier par défaut : celui du script)
    python migrate_osint_schema.py [dossier] --simulation  # liste seulement
Code de sortie : 0 si tout est en place, 1 sinon.
"""

import sqlite3
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))

OSINT_COLONNES = ("osint_legal_data", "osint_technologies", "osint_google_maps", "osint_social_profiles",
                  "osint_emails_pro", "osint_timestamp", "osint_purge_date")


def colonnes(db, table):
    return {r[1] for r in db.execute(f"PRAGMA table_info('{table}')")}


def migrer_audit(audit_db, simulation=False):
    """Renvoie (ordres, manquantes_apres)."""
    ordres = []
    if not Path(audit_db).exists() or not sqlite3.connect(audit_db).execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='dossiers_audit'").fetchone():
        if simulation:
            return ["(création d'audit.db et de dossiers_audit par dossier_audit_manager)"], list(OSINT_COLONNES)
        import dossier_audit_manager
        dossier_audit_manager.connecter(str(audit_db)).close()  # CREATE TABLE IF NOT EXISTS + colonnes OSINT
        ordres.append("dossier_audit_manager.connecter : tables créées (base neuve)")
    db = sqlite3.connect(audit_db, timeout=30)
    presentes = colonnes(db, "dossiers_audit")
    for col in OSINT_COLONNES:
        if col in presentes:  # testée avant ajout : pas d'erreur de colonne en double
            continue
        ordre = f"ALTER TABLE dossiers_audit ADD COLUMN {col} TEXT"
        ordres.append(ordre)
        if not simulation:
            db.execute(ordre)
    if not simulation:
        db.commit()
    manquantes = [c for c in OSINT_COLONNES if c not in colonnes(db, "dossiers_audit")]
    db.close()
    return ordres, manquantes


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dossier = Path(args[0]) if args else ICI
    simulation = "--simulation" in sys.argv
    ordres, manquantes = migrer_audit(dossier / "audit.db", simulation)
    print(("SIMULATION" if simulation else "MIGRATION") + f" audit.db : {len(ordres)} opération(s)")
    for o in ordres:
        print("  " + o)
    ok = simulation or not manquantes
    if (dossier / "cortex.db").exists():
        import schema_sync
        r = schema_sync.synchroniser(dossier / "cortex.db", appliquer=not simulation)
        print(f"cortex.db : {len(r['ajoutees'])} colonne(s) " + ("à ajouter" if simulation else "ajoutée(s)"))
        for o in r["ajoutees"]:
            print("  " + o)
    if not ok:
        print("ÉCHEC : colonnes OSINT encore absentes : " + ", ".join(manquantes))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
