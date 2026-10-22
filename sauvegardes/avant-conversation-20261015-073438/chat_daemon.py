"""Lecteur Telegram permanent du Cortex : réponses instantanées.

- Long polling getUpdates (le message arrive dès qu'il est envoyé, sans boucle agressive).
- Seul lecteur de Telegram tant qu'il tourne : cortex.py s'efface (battement de cœur dans cortex.db).
- Traite chaque message comme le Cortex : discussion libre, et commandes (/valider, /etat…)
  pour qu'aucune ne se perde. Il ne lance ni veille, ni prospection, ni envoi d'email par lui-même.
- Relancé par le Planificateur Windows s'il s'arrête (tâche « JOSY EI Cortex Chat », toutes les
  5 minutes : le verrou ci-dessous fait que le relancer quand il tourne déjà ne fait rien).

Robustesse (15/10/2026) : tout le corps de la boucle est protégé. Auparavant, une écriture
dans cortex.db — battement de cœur, position de lecture — se trouvait hors du bloc protégé :
quand un cycle du Cortex tenait la base, l'erreur de verrou tuait le lecteur, qui restait mort
jusqu'à la prochaine relance. Une panne d'un instant ne doit plus arrêter le service.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cortex  # noqa: E402  (charge .env et la configuration)

LOCK = cortex.BASE_DIR / "chat_daemon.lock"
PAUSE_ERREUR = 5          # secondes avant de réessayer après une panne inattendue
PAUSE_RESEAU = 5
PAUSE_TELEGRAM = 10


def already_running():
    """Une seule instance : verrou rafraîchi à chaque boucle, considéré mort après 90 s."""
    if LOCK.exists() and time.time() - LOCK.stat().st_mtime < 90:
        return True
    LOCK.write_text(str(time.time()))
    return False


def journal(store, evenement, details=None):
    """Écrire au journal ne doit jamais faire tomber le lecteur."""
    try:
        store.log("SYSTEME", evenement, details=details or {})
    except Exception:
        pass


def main():
    if already_running():
        return 0
    store = cortex.Store(cortex.DB_PATH)
    tg = cortex.Telegram(cortex.TG_TOKEN, cortex.TG_CHAT, store)
    cx = cortex.Cortex(store, tg)
    if not tg.enabled:
        journal(store, "chat_daemon_sans_telegram")
        return 1
    journal(store, "chat_daemon_demarre")
    while True:
        try:
            LOCK.write_text(str(time.time()))
            store.set("chat_daemon_heartbeat", cortex.iso(cortex.now()))
            offset = int(store.get("tg_offset", "0"))
        except Exception as exc:                     # base verrouillée par un cycle du Cortex
            journal(store, "chat_daemon_boucle_erreur", {"erreur": cortex.safe_error(exc)})
            time.sleep(PAUSE_ERREUR)
            continue
        try:
            r = cortex.requests.post(f"https://api.telegram.org/bot{tg.token}/getUpdates",
                                     json={"offset": offset, "timeout": 25,
                                           "allowed_updates": ["message", "callback_query"]},
                                     timeout=35)
            res = r.json()
        except (cortex.requests.RequestException, ValueError) as exc:
            journal(store, "chat_daemon_reseau", {"erreur": cortex.safe_error(exc)})
            time.sleep(PAUSE_RESEAU)
            continue
        if not res.get("ok"):
            journal(store, "chat_daemon_getupdates_echec", {"code": res.get("error_code")})
            time.sleep(PAUSE_TELEGRAM)
            continue
        for upd in res.get("result", []):
            cx.chat_count = 0  # chaque message reçoit sa réponse
            try:
                cx.handle_update(upd)
            except Exception as exc:  # un message défectueux ne bloque pas les suivants
                journal(store, "commande_erreur", {"erreur": cortex.safe_error(exc)})
            try:
                store.set("tg_offset", upd["update_id"] + 1)
            except Exception as exc:
                journal(store, "chat_daemon_boucle_erreur", {"erreur": cortex.safe_error(exc)})
                time.sleep(PAUSE_ERREUR)
                break


if __name__ == "__main__":
    sys.exit(main())
