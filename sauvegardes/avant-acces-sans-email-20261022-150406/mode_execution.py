"""Mode d'exécution du Cortex : « manuel » (défaut) ou « auto ».

Feu vert de JOSY du 21/10/2026 (22:21) pour l'envoi automatique des RELANCES, aux conditions :
plafond de 30 emails par jour, liste d'opposition, zéro prix, retour en manuel sur erreur critique.

  - manuel : rien ne part sans le clic de JOSY (interface locale ou Telegram) ;
  - auto   : au début de chaque cycle, le Cortex valide lui-même les relances en attente ;
             elles passent ensuite par la file d'envoi habituelle (vente.process_queue), donc par
             les mêmes contrôles : plafonds du jour, liste d'opposition, zéro prix, STOP.
             Les premiers emails, réponses et publications restent à valider par JOSY.

Sécurité : à la première erreur critique (échec SMTP, fichier, exception du cycle), le Cortex
repasse en manuel, suspend les envois qu'il avait validés seul (ils reviennent « à valider ») et
prévient JOSY sur Telegram. Le mode est stocké dans cortex.db (table kv, clé CLE) ; toute bascule
est journalisée (I1).
"""

from datetime import timedelta

CLE = "mode_execution"
MODES = ("manuel", "auto")
SOURCE_AUTO = "mode_auto"
TYPES_AUTO = {"relance"}  # périmètre exact du feu vert de JOSY


def lire(store):
    """Le mode courant ; toute valeur inconnue vaut « manuel » (défaut sûr)."""
    return "auto" if (store.get(CLE) or "").strip() == "auto" else "manuel"


def definir(store, mode, source, raison=""):
    if mode not in MODES:
        raise ValueError(mode)
    avant = lire(store)
    store.set(CLE, mode)
    store.log("HUMAIN" if source == "application locale" else "JUDICIAIRE", f"mode_{mode}",
              details={"avant": avant, "source": source, "raison": raison[:300]})
    return avant


def auto_valider(c, cortex):
    """Mode auto : valide les relances en attente (sans clic), puis les met en file d'envoi."""
    db, n = cortex.s.db, 0
    rows = db.execute("SELECT * FROM proposals WHERE status=? ORDER BY created_at", (c.PENDING,)).fetchall()
    for p in rows:
        if p["action_type"] not in TYPES_AUTO or c.now() > c.parse_iso(p["expires_at"]):
            continue
        db.execute("UPDATE proposals SET status='valide', decided_at=?, decision_source=? WHERE action_id=?",
                   (c.iso(c.now()), SOURCE_AUTO, p["action_id"]))
        db.commit()
        cortex.s.log("EXECUTIF", "decision_auto_valide", p["action_id"],
                     {"mode": "auto", "type": p["action_type"]})
        cortex.tg.clear_buttons(p["tg_message_id"])
        cortex.execute(c.json.loads(p["payload"]))
        n += 1
    return n


def basculer_manuel(c, cortex, raison):
    """Erreur critique en mode auto : retour en manuel, envois auto suspendus, alerte Telegram."""
    s = cortex.s
    if lire(s) != "auto":
        return False
    definir(s, "manuel", "securite", raison)
    db = s.db
    ids = [r[0] for r in db.execute(
        "SELECT DISTINCT f.action_id FROM file_envoi f JOIN proposals p ON p.action_id=f.action_id "
        "WHERE f.statut='en_file' AND p.decision_source=?", (SOURCE_AUTO,))]
    for aid in ids:  # rien de ce que le Cortex a validé seul ne part plus sans clic
        db.execute("UPDATE file_envoi SET statut='suspendu_manuel' WHERE action_id=? AND statut='en_file'", (aid,))
        db.execute("UPDATE proposals SET status=?, decided_at=NULL, decision_source=NULL, expires_at=? "
                   "WHERE action_id=?", (c.PENDING, c.iso(c.now() + timedelta(hours=24)), aid))
    db.commit()
    s.log("JUDICIAIRE", "envois_auto_suspendus", details={"actions": len(ids), "raison": raison[:300]})
    try:
        cortex.tg.send(f"⚠️ Mode automatique coupé : {c.html.escape(raison[:300])}.\n"
                       f"Le Cortex est repassé en MODE MANUEL. {len(ids)} envoi(s) suspendu(s), "
                       "de nouveau à valider. Rien ne part sans ton clic.")
    except Exception:
        pass  # l'alerte ne doit pas empêcher la bascule (déjà faite et journalisée)
    return True
