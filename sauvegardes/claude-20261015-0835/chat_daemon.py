"""Lecteur Telegram permanent du Cortex : réponses instantanées.

- Long polling getUpdates (le message arrive dès qu'il est envoyé, sans boucle agressive).
- Seul lecteur de Telegram tant qu'il tourne : cortex.py s'efface (battement de cœur dans cortex.db).
- Traite chaque message comme le Cortex : discussion libre, et commandes (/valider, /etat…)
  pour qu'aucune ne se perde. Il ne lance ni veille, ni prospection, ni envoi d'email par lui-même.

Trois correctifs issus de pannes réelles :

1. le battement vit dans **son propre fil** : une réponse lente (quota du modèle atteint,
   repli sur le modèle local) ne doit plus faire croire à cortex.py que le lecteur est mort.
   Sinon les deux lisent Telegram en même temps et JOSY reçoit ses réponses en double,
   en retard, ou pas du tout ;
2. le verrou contient le **PID** du lecteur, pas seulement une date : un verrou d'âge ne
   distinguait pas un lecteur vivant d'un processus tué, et un redémarrage était alors
   refusé pendant 90 secondes — ou volé par l'ancien processus ;
3. `--status` et `--stop` permettent de savoir qui lit et d'arrêter proprement, sans
   dépendre d'un outil système.

Usage :
    python chat_daemon.py            # lecteur permanent (relancé par la tâche Windows)
    python chat_daemon.py --status   # qui lit, et depuis quand ?
    python chat_daemon.py --stop     # arrête le lecteur en cours
"""

import ctypes
import os
import sqlite3
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cortex  # noqa: E402  (charge .env et la configuration)

LOCK = cortex.BASE_DIR / "chat_daemon.lock"
BATTEMENT_S = 15
ACTIVITE = [0.0]   # horloge du dernier message de JOSY (pour garder la connexion au modèle ouverte)


def _vivant(pid):
    """Le processus existe-t-il encore ? (ctypes : rien à installer)"""
    try:
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))  # QUERY_LIMITED
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
    except Exception:
        pass
    return False


def pid_du_verrou():
    try:
        return int(LOCK.read_text().strip().split()[0])
    except (ValueError, IndexError, OSError):
        return None


def already_running():
    """Une seule instance, vérifiée par le PID inscrit dans le verrou."""
    pid = pid_du_verrou()
    if pid and pid != os.getpid() and _vivant(pid):
        return True
    LOCK.write_text(str(os.getpid()))
    return False


def _toucher():
    """Rafraîchit la date du verrou sans écraser le PID qu'il contient."""
    try:
        os.utime(LOCK, None)
    except OSError:
        pass


def age_battement():
    """Âge du battement en secondes, ou None s'il n'y en a jamais eu."""
    try:
        connexion = sqlite3.connect(cortex.DB_PATH, timeout=10)
        ligne = connexion.execute(
            "SELECT value FROM kv WHERE key='chat_daemon_heartbeat'").fetchone()
        connexion.close()
    except sqlite3.Error:
        return None
    if not ligne or not ligne[0]:
        return None
    try:
        return (cortex.now() - cortex.parse_iso(ligne[0])).total_seconds()
    except (ValueError, TypeError):
        return None


def etat():
    pid = pid_du_verrou()
    age = age_battement()
    vivant = bool(pid) and _vivant(pid)
    return (f"lecteur Telegram : {'VIVANT' if vivant else 'ARRÊTÉ'}"
            f" (PID {pid if pid else '—'}) · battement : "
            f"{str(int(age)) + ' s' if age is not None else 'jamais'}")


def main():
    if "--status" in sys.argv:
        print(etat())
        return 0
    if "--stop" in sys.argv:
        pid = pid_du_verrou()
        if pid and pid != os.getpid() and _vivant(pid):
            os.kill(pid, 9)  # sous Windows : arrêt inconditionnel du processus visé
            print(f"lecteur arrêté (PID {pid})")
        else:
            print("aucun lecteur à arrêter")
        try:
            LOCK.unlink()
        except OSError:
            pass
        return 0

    if already_running():
        print("un lecteur tourne déjà (voir --status)")
        return 0
    store = cortex.Store(cortex.DB_PATH)
    tg = cortex.Telegram(cortex.TG_TOKEN, cortex.TG_CHAT, store)
    cx = cortex.Cortex(store, tg)
    if not tg.enabled:
        store.log("SYSTEME", "chat_daemon_sans_telegram")
        return 1
    store.log("SYSTEME", "chat_daemon_demarre")

    def battement():
        """Battement indépendant : il continue même pendant une réponse lente."""
        try:
            connexion = sqlite3.connect(cortex.DB_PATH, timeout=10)
        except sqlite3.Error:
            return
        while True:
            try:
                connexion.execute(
                    "INSERT INTO kv(key, value) VALUES('chat_daemon_heartbeat', ?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (cortex.iso(cortex.now()),))
                connexion.commit()
                _toucher()
            except Exception:
                pass
            time.sleep(BATTEMENT_S)

    threading.Thread(target=battement, daemon=True).start()

    def garder_chaud():
        """Garde la connexion à Groq ouverte en permanence : ouvrir une connexion coûte environ 5 s sur ce PC
        (chargement des certificats), un appel sur une connexion ouverte 0,2 s. Ouverte dès le démarrage,
        rafraîchie toutes les 30 s."""
        cle = os.environ.get("GROQ_API_KEY", "")
        while cle:
            try:  # GET /models : aucun jeton, aucune requête décomptée (mesuré), connexion gardée ≥ 60 s
                cortex.HTTP.get("https://api.groq.com/openai/v1/models", timeout=15,
                                headers={"Authorization": f"Bearer {cle}"})
            except Exception:
                pass
            time.sleep(30)

    threading.Thread(target=garder_chaud, daemon=True).start()
    while True:
        _toucher()
        store.set("chat_daemon_heartbeat", cortex.iso(cortex.now()))
        offset = int(store.get("tg_offset", "0"))
        try:
            r = cortex.HTTP.post(f"https://api.telegram.org/bot{tg.token}/getUpdates",
                                     json={"offset": offset, "timeout": 25,
                                           "allowed_updates": ["message", "callback_query"]},
                                     timeout=35)
            res = r.json()
        except (cortex.requests.RequestException, ValueError) as exc:
            store.log("SYSTEME", "chat_daemon_reseau", details={"erreur": cortex.safe_error(exc)})
            time.sleep(5)
            continue
        if not res.get("ok"):
            store.log("SYSTEME", "chat_daemon_getupdates_echec", details={"code": res.get("error_code")})
            time.sleep(10)
            continue
        for upd in res.get("result", []):
            ACTIVITE[0] = time.monotonic()
            cx.chat_count = 0  # chaque message reçoit sa réponse
            try:
                cx.handle_update(upd)
            except Exception as exc:  # un message défectueux ne bloque pas les suivants
                store.log("SYSTEME", "commande_erreur", details={"erreur": cortex.safe_error(exc)})
            store.set("tg_offset", upd["update_id"] + 1)


if __name__ == "__main__":
    sys.exit(main())
