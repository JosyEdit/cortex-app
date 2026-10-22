#!/usr/bin/env python3
"""Surveillance locale du Cortex : relance ce qui s'arrête, sans aucun droit administrateur.

Pourquoi ce programme existe : sur ce PC, le Planificateur de tâches refuse toute
création ou modification de tâche à un utilisateur normal (« Accès refusé »). La
tâche « JOSY EI Cortex Chat » est de plus restée désactivée, ce qui a laissé le
lecteur Telegram arrêté quatre heures et demie.

Cette surveillance la remplace. Lancée à l'ouverture de session par
`demarrage-veille.vbs` (dossier Démarrage), elle vérifie toutes les 60 secondes
que les deux services répondent et les relance sinon :

  * le **lecteur Telegram instantané** — vivant si son battement de cœur a moins
    de 3 minutes ;
  * l'**interface locale** — vivante si son port répond.

Elle n'écrit jamais dans cortex.db (lecture seule) et ne touche à aucune donnée.
Aucune fenêtre : elle est lancée avec pythonw.exe.
"""

import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

VIVANT = Path(__file__).resolve().parent
JOURNAL = VIVANT / "surveillance.log"
BATTEMENT_TOLERE_S = 120        # au-delà, le lecteur est considéré arrêté
PAUSE_S = 30
PORTS_INTERFACE = range(8765, 8771)
DELAI_MIN_RELANCE_S = 120       # jamais deux relances rapprochées pour un même service


def dire(message):
    """Trace horodatée, dans un fichier : personne ne lit de console ici."""
    ligne = f"{datetime.now().strftime('%d/%m %H:%M:%S')}  {message}"
    try:
        with JOURNAL.open("a", encoding="utf-8") as f:
            f.write(ligne + "\n")
            if JOURNAL.stat().st_size > 200_000:      # on garde les 200 derniers ko
                contenu = JOURNAL.read_text(encoding="utf-8").splitlines()[-1500:]
                JOURNAL.write_text("\n".join(contenu) + "\n", encoding="utf-8")
    except OSError:
        pass
    return ligne


def pythonw():
    for candidat in (shutil.which("pythonw"),
                     Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Python/Python312/pythonw.exe"):
        if candidat and Path(candidat).exists():
            return str(candidat)
    return sys.executable


def lancer(script):
    """Démarre un service détaché, sans fenêtre, sans rien capturer."""
    options = {"cwd": str(VIVANT), "stdin": subprocess.DEVNULL,
               "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        options["creationflags"] = 0x00000008 | 0x08000000
    subprocess.Popen([pythonw(), str(script)], **options)
    dire(f"relance de {Path(script).name}")


def age_battement():
    """Secondes depuis le dernier battement de cœur du lecteur. None si illisible."""
    try:
        con = sqlite3.connect(f"file:{(VIVANT / 'cortex.db').as_posix()}?mode=ro", uri=True, timeout=5)
        try:
            ligne = con.execute("SELECT value FROM kv WHERE key='chat_daemon_heartbeat'").fetchone()
        finally:
            con.close()
        if not ligne or not ligne[0]:
            return None
        return (datetime.now(timezone.utc) - datetime.fromisoformat(ligne[0])).total_seconds()
    except (sqlite3.Error, ValueError):
        return None


def interface_vivante():
    """Vrai si un port de l'interface accepte une connexion."""
    for port in PORTS_INTERFACE:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=3):
                return True
        except OSError:
            continue
    return False


def main():
    dire(f"surveillance démarrée (lecteur toléré {BATTEMENT_TOLERE_S} s, contrôle toutes les "
         f"{PAUSE_S} s)")
    dernier = {}
    while True:
        try:
            # 1. le lecteur Telegram
            age = age_battement()
            if age is None:
                dire("battement de cœur illisible (base occupée) : je ne touche à rien")
            elif age > BATTEMENT_TOLERE_S:
                if time.time() - dernier.get("lecteur", 0) > DELAI_MIN_RELANCE_S:
                    dernier["lecteur"] = time.time()
                    dire(f"lecteur arrêté depuis {int(age)} s -> relance")
                    lancer(VIVANT / "chat_daemon.py")
            # 2. l'interface
            if not interface_vivante():
                if time.time() - dernier.get("interface", 0) > DELAI_MIN_RELANCE_S:
                    dernier["interface"] = time.time()
                    dire("interface muette -> relance")
                    lancer(VIVANT / "app.py")
        except Exception as exc:                      # rien ne doit arrêter la surveillance
            dire(f"erreur de contrôle : {type(exc).__name__}")
        time.sleep(PAUSE_S)


if __name__ == "__main__":
    sys.exit(main())
