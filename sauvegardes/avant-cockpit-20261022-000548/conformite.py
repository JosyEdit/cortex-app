"""Catégorie 7 : sécurité et conformité (fonctionnalités 31 à 33).

31. journal inviolable : la chaîne SHA-256 existe (Store.log / verify_journal) ; ici, contrôle à chaque
    cycle et alerte (format F) si elle est rompue ;
32. liste d'opposition : définitive (table liste_opposition, vérifiée avant chaque envoi dans vente.py) ;
33. RGPD : droit à l'oubli (`oublier`) et portabilité (`donnees`) pour une adresse email. Le hash de
    l'adresse est conservé dans la liste d'opposition (c'est le seul moyen de ne plus jamais la contacter) ;
    le journal chaîné ne contient jamais d'email, donc n'est pas modifié.
Les fonctionnalités 34 (isolation par client) et 35 (OAuth2 partout) sont « à décider » : voir le tableau.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def _hash(email):
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def _tables_avec_email(db):
    return (("entreprises", "email_contact"), ("candidates", "email"), ("file_envoi", "to_email"),
            ("envois", "to_email"), ("audits", "email"), ("reponses_attente", "to_email"))


def _existe(db, table):
    return bool(db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())


def donnees(store, email, dossier):
    """Portabilité : toutes les lignes qui contiennent cette adresse, en JSON lisible."""
    db, email = store.db, email.strip().lower()
    out = {"adresse": email, "date": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tables": {}}
    for table, col in _tables_avec_email(db):
        if not _existe(db, table):
            continue
        cur = db.execute(f"SELECT * FROM {table} WHERE lower({col})=?", (email,))
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        if rows:
            out["tables"][table] = rows
    props = [dict(r) for r in db.execute("SELECT action_id, action_type, status, created_at FROM proposals "
                                         "WHERE lower(payload) LIKE ?", (f"%{email}%",))]
    if props:
        out["tables"]["proposals"] = props
    chemin = Path(dossier) / f"donnees-{_hash(email)[:10]}.json"
    chemin.parent.mkdir(exist_ok=True)
    chemin.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return chemin, {t: len(v) for t, v in out["tables"].items()}


def oublier(store, email):
    """Droit à l'oubli : efface ou anonymise l'adresse partout (sauf le journal, qui n'en contient pas),
    puis l'inscrit à la liste d'opposition (hash seulement)."""
    db, email = store.db, email.strip().lower()
    h = _hash(email)
    compte = {}
    marque = f"oublie-{h[:10]}"
    for table, col in _tables_avec_email(db):
        if not _existe(db, table):
            continue
        if table in ("file_envoi", "audits", "reponses_attente"):
            cur = db.execute(f"DELETE FROM {table} WHERE lower({col})=?", (email,))
        elif table == "envois":
            cur = db.execute("UPDATE envois SET to_email=? WHERE lower(to_email)=?", (marque, email))
        else:
            cur = db.execute(f"UPDATE {table} SET {col}=NULL WHERE lower({col})=?", (email,))
        compte[table] = cur.rowcount
    n = 0
    for aid, payload in db.execute("SELECT action_id, payload FROM proposals WHERE lower(payload) LIKE ?",
                                   (f"%{email}%",)).fetchall():
        db.execute("UPDATE proposals SET payload=? WHERE action_id=?",
                   (payload.replace(email, marque).replace(email.upper(), marque), aid))
        n += 1
    compte["proposals"] = n
    db.execute("INSERT OR IGNORE INTO liste_opposition(siren, email_hash, date_opposition) VALUES('', ?, ?)",
               (h, datetime.now(timezone.utc).isoformat(timespec="seconds")))
    db.commit()
    store.log("HUMAIN", "droit_oubli_applique", details={"tables": compte})  # aucune adresse dans le journal
    return compte


def verifier_journal(c, cortex):
    """Contrôle d'intégrité à chaque cycle ; alerte (format F) si la chaîne est rompue."""
    ok, bad = cortex.s.verify_journal()
    if not ok:
        c.alert(cortex.s, "journal", f"chaîne SHA-256 rompue à la ligne {bad}")
    return ok
