"""Catégorie 2 : auto-amélioration supervisée (fonctionnalités 6 à 10).

6. apprentissage par l'expérience : taux de réponse par type d'argument, tirés des envois réels
   (aucun principe sans échantillon suffisant : MIN_ECHANTILLON envois) ;
7. détection d'anomalies : taux de réponse effondré, erreur répétée -> alerte Telegram (format F) ;
8. décroissance de confiance : un principe perd en poids (demi-vie 30 jours) tant qu'il n'est pas revalidé ;
9. suggestion d'amendement : proposition `amelioration_regle` (R2) soumise à JOSY, jamais appliquée seule ;
10. historique des versions : AGENTS.md est versionné ; un retour
    arrière (`rollback_regles`, R3) est une proposition que JOSY valide.
"""

import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

MIN_ECHANTILLON = 10        # envois minimum avant d'énoncer un principe
MIN_POUR_AMENDEMENT = 30    # envois minimum avant de proposer de changer une règle
SEUIL_TAUX_BAS = 0.03       # sous 3 % de réponses (sur MIN_POUR_AMENDEMENT envois), on propose une révision
DEMI_VIE_JOURS = 30
POIDS_MIN = 0.2
FICHIERS_VERSIONNES = ("AGENTS.md",)  # secteurs.json supprimé (moteur d'audit universel, 19/10/2026)

SCHEMA = """
CREATE TABLE IF NOT EXISTS principes (
  id INTEGER PRIMARY KEY AUTOINCREMENT, regle TEXT UNIQUE, n INTEGER, taux REAL, valide_le TEXT,
  actif INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS regles_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, fichier TEXT, sha256 TEXT, contenu TEXT, motif TEXT);
"""

TYPES = (("concurrents", re.compile(r"1er résultat", re.I)),
         ("avis", re.compile(r"fiche Google compte", re.I)),
         ("site_date", re.compile(r"affiche encore", re.I)))


def _now():
    return datetime.now(timezone.utc)


def _iso(d):
    return d.isoformat(timespec="seconds")


def setup(store):
    store.db.executescript(SCHEMA)
    store.db.commit()


def type_argument(corps):
    for nom, rx in TYPES:
        if rx.search(corps or ""):
            return nom
    return "autre"


# ---------------------------------------------------------------- 6. apprentissage
def statistiques(store):
    """Par type d'argument : (envois, réponses). Données réelles : envois du mode réel uniquement."""
    setup(store)
    rows = store.db.execute(
        "SELECT e.repondu AS repondu, f.body AS body FROM envois e JOIN file_envoi f ON f.action_id=e.action_id "
        "AND lower(f.to_email)=lower(e.to_email) WHERE e.kind='premier' AND e.simule=0").fetchall()
    stats = {}
    for r in rows:
        t = type_argument(r["body"])
        n, rep = stats.get(t, (0, 0))
        stats[t] = (n + 1, rep + int(bool(r["repondu"])))
    return stats


def apprendre(store):
    """Écrit un principe par type d'argument ayant au moins MIN_ECHANTILLON envois."""
    setup(store)
    nouveaux = []
    for t, (n, rep) in statistiques(store).items():
        if n < MIN_ECHANTILLON:
            continue
        taux = rep / n
        regle = f"Argument « {t} » : {round(100 * taux)} % de réponses sur {n} envois"
        store.db.execute("INSERT INTO principes(regle, n, taux, valide_le) VALUES(?,?,?,?) "
                         "ON CONFLICT(regle) DO UPDATE SET valide_le=excluded.valide_le, actif=1",
                         (regle, n, taux, _iso(_now())))
        nouveaux.append(regle)
    store.db.commit()
    return nouveaux


# ---------------------------------------------------------------- 8. décroissance
def poids(valide_le, maintenant=None):
    age = ((maintenant or _now()) - datetime.fromisoformat(valide_le)).total_seconds() / 86400
    return 0.5 ** (max(age, 0) / DEMI_VIE_JOURS)


def principes_actifs(store, maintenant=None):
    """Principes classés par poids ; ceux sous POIDS_MIN sont désactivés (jamais supprimés)."""
    setup(store)
    out = []
    for r in store.db.execute("SELECT id, regle, n, taux, valide_le FROM principes WHERE actif=1"):
        w = poids(r["valide_le"], maintenant)
        if w < POIDS_MIN:
            store.db.execute("UPDATE principes SET actif=0 WHERE id=?", (r["id"],))
            continue
        out.append({"regle": r["regle"], "poids": round(w, 2)})
    store.db.commit()
    return sorted(out, key=lambda x: -x["poids"])


# ---------------------------------------------------------------- 7. anomalies
def anomalies(store):
    """Renvoie une liste de (type, message). Aucune anomalie tant que l'échantillon est insuffisant."""
    setup(store)
    res = []
    stats = statistiques(store)
    n = sum(v[0] for v in stats.values())
    rep = sum(v[1] for v in stats.values())
    if n >= MIN_POUR_AMENDEMENT:
        recents = store.db.execute(
            "SELECT repondu FROM envois WHERE kind='premier' AND simule=0 ORDER BY id DESC LIMIT 20").fetchall()
        taux_global = rep / n
        taux_recent = sum(int(bool(r["repondu"])) for r in recents) / len(recents)
        if taux_global >= 0.05 and taux_recent < taux_global / 2:
            res.append(("anomalie", f"taux de réponse récent {round(100 * taux_recent)} % contre "
                                    f"{round(100 * taux_global)} % sur l'ensemble ({len(recents)} derniers envois)"))
    depuis = _iso(_now() - timedelta(hours=24))
    for r in store.db.execute("SELECT event, COUNT(*) AS c FROM journal WHERE ts>=? AND event LIKE '%erreur%' "
                              "GROUP BY event HAVING c>=5", (depuis,)):
        res.append(("erreur répétée", f"{r['event']} : {r['c']} fois en 24 h"))
    return res


# ---------------------------------------------------------------- 10. versions
def _fichier(base, nom):
    return Path(base) / nom


def versionner(store, base, motif="modification détectée"):
    """Enregistre une nouvelle version de chaque fichier de règles dont le contenu a changé."""
    setup(store)
    ajoutees = []
    for nom in FICHIERS_VERSIONNES:
        f = _fichier(base, nom)
        if not f.exists():
            continue
        contenu = f.read_text(encoding="utf-8")
        sha = hashlib.sha256(contenu.encode()).hexdigest()
        last = store.db.execute("SELECT sha256 FROM regles_versions WHERE fichier=? ORDER BY id DESC LIMIT 1",
                                (nom,)).fetchone()
        if not last or last["sha256"] != sha:
            store.db.execute("INSERT INTO regles_versions(ts, fichier, sha256, contenu, motif) VALUES(?,?,?,?,?)",
                             (_iso(_now()), nom, sha, contenu, motif if last else "version initiale"))
            ajoutees.append(nom)
    store.db.commit()
    return ajoutees


def liste_versions(store, n=10):
    setup(store)
    return [dict(r) for r in store.db.execute(
        "SELECT id, ts, fichier, substr(sha256,1,10) AS sha, motif FROM regles_versions ORDER BY id DESC LIMIT ?", (n,))]


def proposer_rollback(c, cortex, version_id):
    """Retour arrière : proposition R3 que JOSY valide ; rien n'est modifié avant son /valider."""
    setup(cortex.s)
    v = cortex.s.db.execute("SELECT * FROM regles_versions WHERE id=?", (version_id,)).fetchone()
    if not v:
        cortex.tg.send("Version inconnue. /versions pour la liste.")
        return None
    aid = str(uuid.uuid4())
    p = {"action_id": aid, "timestamp": c.iso(c.now()), "risk_level": "R3", "mission": "M5_Veille",
         "action_type": "rollback_regles", "version_id": v["id"], "fichier": v["fichier"],
         "target": {"company": f"{v['fichier']} (version {v['id']} du {v['ts'][:10]})", "contact": "règles"},
         "content": {"subject": "", "body": f"Restaurer {v['fichier']} dans sa version {v['id']} ({v['ts'][:16]})."},
         "sources": [{"url": "regles_versions (cortex.db)", "date": v["ts"][:10]}],
         "justification": "Retour arrière demandé par JOSY.", "reversibility": "L'état actuel est versionné avant.",
         "timeout_hours": 24}
    cortex.dispatch(p, text=f"♻️ Restaurer {v['fichier']} (version {v['id']}, {v['ts'][:10]}) ? "
                            f"/valider {aid[:8]} /refuser {aid[:8]}")
    return aid


def appliquer_rollback(c, cortex, p, base):
    """Appelée après /valider : sauvegarde l'état actuel, puis restaure."""
    nom = p["fichier"]
    if nom not in FICHIERS_VERSIONNES:  # liste blanche
        raise ValueError("fichier non versionné")
    v = cortex.s.db.execute("SELECT contenu FROM regles_versions WHERE id=?", (p["version_id"],)).fetchone()
    versionner(cortex.s, base, motif="avant retour arrière")
    _fichier(base, nom).write_text(v["contenu"], encoding="utf-8")
    versionner(cortex.s, base, motif=f"retour arrière vers la version {p['version_id']}")
    cortex.s.log("HUMAIN", "regles_restaurees", p["action_id"], {"fichier": nom, "version": p["version_id"]})
    cortex.tg.send(f"✅ {nom} restauré (version {p['version_id']}).")


# ---------------------------------------------------------------- 9. amendements
def suggerer(c, cortex):
    """Propose un amendement si les chiffres réels le justifient. Une proposition par jour au plus."""
    s = cortex.s
    setup(s)
    jour = c.now().date().isoformat()
    if s.get("amendement_jour") == jour:
        return None
    stats = statistiques(s)
    n = sum(v[0] for v in stats.values())
    rep = sum(v[1] for v in stats.values())
    if n < MIN_POUR_AMENDEMENT or rep / n >= SEUIL_TAUX_BAS:
        return None
    s.set("amendement_jour", jour)
    detail = ", ".join(f"{t} {r}/{k}" for t, (k, r) in sorted(stats.items()))
    aid = str(uuid.uuid4())
    p = {"action_id": aid, "timestamp": c.iso(c.now()), "risk_level": "R2", "mission": "M5_Veille",
         "action_type": "amelioration_regle",
         "target": {"company": "règles des emails de prospection", "contact": "JOSY"},
         "content": {"subject": "", "body": f"Taux de réponse : {rep} réponses pour {n} emails ({detail}). "
                                           "Proposition : revoir l'accroche et le type de fait cité en premier."},
         "sources": [{"url": "envois et réponses (cortex.db)", "date": jour}],
         "justification": f"{rep} réponses sur {n} emails envoyés.", "reversibility": "Aucune règle n'est modifiée sans toi.",
         "timeout_hours": 24}
    cortex.dispatch(p, text=f"💡 Proposition d'amendement : {rep} réponses pour {n} emails ({detail}). "
                            f"Revoir l'accroche et le fait cité en premier ? /valider {aid[:8]} /refuser {aid[:8]}")
    return aid


def cycle(c, cortex, base):
    """Un passage par cycle : versions, apprentissage, anomalies, amendement."""
    s = cortex.s
    versionner(s, base)
    apprendre(s)
    principes_actifs(s)
    for kind, msg in anomalies(s):
        c.alert(s, kind, msg)
    suggerer(c, cortex)
