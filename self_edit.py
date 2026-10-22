#!/usr/bin/env python3
"""Modification d'un fichier du Cortex par le modèle, SOUS VALIDATION HUMAINE.

Principe : le modèle reçoit le contenu ACTUEL du fichier et la demande, et renvoie le fichier complet modifié.
Rien n'est écrit dans la cible sans /valider_edit ID sur Telegram.

  python self_edit.py --request "..." --target cortex.py [--dry-run] [--sans-telegram]
      -> écrit la proposition dans nouveau_code.py (+ nouveau_code.diff), notifie sur Telegram, s'arrête.
  /valider_edit ID  ou  python self_edit.py --valider ID   -> sauvegarde, écrit, contrôle la syntaxe (retour arrière si échec)
  /refuser_edit ID  ou  python self_edit.py --refuser ID   -> ne fait rien

Garde-fous : sauvegarde obligatoire avant toute écriture (5 dernières conservées), proposition refusée si la
réponse du modèle est tronquée ou si le fichier rétrécit de plus de 20 %, empreinte SHA-256 vérifiée entre la
proposition et l'écriture, une seule proposition en attente à la fois.
"""

import argparse
import datetime
import difflib
import glob
import hashlib
import os
import py_compile
import re
import shutil
import sqlite3
import sys
import tempfile
import traceback

try:
    import requests
except Exception:
    print("Le module 'requests' est requis. Installez-le: pip install requests")
    sys.exit(2)

BASE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DB_PATH = os.path.join(BASE, "cortex.db")
NEW_CODE = os.path.join(BASE, "nouveau_code.py")
NEW_DIFF = os.path.join(BASE, "nouveau_code.diff")
KEEP_BACKUPS = 5
TPM_LIMIT = int(os.getenv("GROQ_TPM_LIMIT", "8000"))  # jetons par minute du compte (mesuré le 13/10/2026)
MIN_SIZE_RATIO = 0.8


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(BASE, ".env"))
        return
    except Exception:
        pass
    path = os.path.join(BASE, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS edits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, request TEXT, target TEXT, status TEXT,
        backup_path TEXT, error_text TEXT, sha256 TEXT, taille INTEGER)""")
    cols = {r[1] for r in conn.execute("PRAGMA table_info(edits)")}
    for col, typ in (("sha256", "TEXT"), ("taille", "INTEGER")):
        if col not in cols:
            conn.execute(f"ALTER TABLE edits ADD COLUMN {col} {typ}")
    conn.commit()
    return conn


def log_edit(request_text, target, status, backup_path=None, error_text=None, sha=None, taille=None):
    conn = db()
    cur = conn.execute("INSERT INTO edits (timestamp, request, target, status, backup_path, error_text, sha256, taille) "
                       "VALUES (?,?,?,?,?,?,?,?)", (now_iso(), request_text, target, status, backup_path, error_text,
                                                    sha, taille))
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


def set_status(edit_id, status, **fields):
    conn = db()
    conn.execute("UPDATE edits SET status=? WHERE id=?", (status, edit_id))
    for k, v in fields.items():
        conn.execute(f"UPDATE edits SET {k}=? WHERE id=?", (v, edit_id))
    conn.commit()
    conn.close()


def call_groq(prompt, api_key, max_tokens=32000, temperature=0.1):
    endpoint = os.getenv("GROQ_ENDPOINT", DEFAULT_GROQ_ENDPOINT)
    payload = {"model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
               "messages": [{"role": "user", "content": prompt}],
               "max_tokens": max_tokens, "temperature": float(temperature)}
    if "gpt-oss" in payload["model"]:
        payload["reasoning_effort"] = "low"  # moins de jetons de raisonnement, comptés dans la réponse
    try:
        resp = requests.post(endpoint, headers={"Authorization": f"Bearer {api_key}",
                                                 "Content-Type": "application/json"},
                             json=payload, timeout=180)
    except Exception as e:
        raise RuntimeError(f"Erreur reseau vers Groq: {type(e).__name__}")
    if resp.status_code >= 400:
        raise RuntimeError(f"Groq API erreur {resp.status_code}: {resp.text[:300]}")
    choice = (resp.json().get("choices") or [{}])[0]
    if choice.get("finish_reason") == "length":
        raise RuntimeError("Reponse du modele tronquee (limite de longueur) : proposition refusee")
    content = (choice.get("message") or {}).get("content")
    if not content:
        raise RuntimeError("Reponse Groq vide")
    return content


def extract_code(text):
    m = re.search(r"```(?:python)?\s*\n([\s\S]*?)```\s*$", text.strip(), re.IGNORECASE)
    if m:
        return m.group(1).strip("\n") + "\n"
    return text.strip("\n") + "\n"


def validate_syntax(path):
    try:
        py_compile.compile(path, doraise=True, cfile=os.path.join(tempfile.gettempdir(), "selfedit_check.pyc"))
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)


def backup_file(path):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bak = f"{path}.bak.{ts}"
    shutil.copy2(path, bak)
    # on ne garde que les KEEP_BACKUPS dernières sauvegardes de ce fichier
    for old in sorted(glob.glob(path + ".bak.*"))[:-KEEP_BACKUPS]:
        os.remove(old)
    return bak


def send_telegram(text):
    token, chat = os.getenv("TG_TOKEN"), os.getenv("TG_CHAT")
    if not (token and chat):
        print("Telegram non configure : notification non envoyee.")
        return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat, "text": text}, timeout=30)
        return bool(r.json().get("ok"))
    except Exception:
        return False


def propose(request, target, dry_run=False, telegram=True):
    load_env()
    key = os.getenv("GROQ_API_KEY")
    if not key:
        print("GROQ_API_KEY introuvable. Abandon.")
        return 3
    target_path = os.path.abspath(os.path.join(BASE, target) if not os.path.isabs(target) else target)
    if not os.path.exists(target_path):
        print("Fichier cible introuvable :", target_path)
        return 4
    if not dry_run:
        pending = db().execute("SELECT id FROM edits WHERE status='en_attente'").fetchone()
        if pending:
            print(f"Une proposition est deja en attente (ID {pending['id']}) : /valider_edit ou /refuser_edit d'abord.")
            return 9
    with open(target_path, "r", encoding="utf-8") as f:
        current_code = f.read()
    name = os.path.basename(target_path)
    prompt = (f"Voici le contenu actuel du fichier {name} :\n---\n{current_code}\n---\n"
              f"Applique cette modification : {request}\n"
              "Renvoie UNIQUEMENT le fichier complet modifié, sans explications, sans rien retirer du reste du "
              "fichier, entouré d'un seul bloc ```python ... ```.")
    # Plafond Groq gratuit : 8000 jetons par minute, demande + réponse demandée (max_tokens) comptées ensemble.
    est_prompt = int(len(prompt) / 3.6)
    est_file = int(len(current_code) / 3.6)
    max_out = min(int(est_file * 1.3) + 500, TPM_LIMIT - est_prompt - 300)
    if max_out < est_file * 1.05:
        msg = (f"module trop gros pour le plafond Groq ({TPM_LIMIT} jetons/min) : demande ~{est_prompt} jetons, "
               f"reponse ~{est_file} jetons. Decoupez le module ou utilisez un modele sans ce plafond.")
        print(msg)
        log_edit(request, target, "refuse_plafond_tpm", error_text=msg)
        return 11
    print("Envoi du fichier actuel et de la demande a Groq...")
    try:
        new_code = extract_code(call_groq(prompt, key, max_tokens=max_out))
    except Exception as e:
        print("Erreur Groq:", e)
        log_edit(request, target, "groq_error", error_text=str(e))
        return 4
    if len(new_code) < MIN_SIZE_RATIO * len(current_code):
        msg = (f"proposition refusee : le fichier propose ({len(new_code)} caracteres) est plus de 20 % plus petit que "
               f"l'actuel ({len(current_code)}) : probable perte de contenu")
        print(msg)
        log_edit(request, target, "refuse_taille", error_text=msg)
        return 10
    fd, tmp = tempfile.mkstemp(suffix=".py", prefix="selfedit_")
    os.close(fd)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(new_code)
    ok, err = validate_syntax(tmp)
    os.remove(tmp)
    if not ok:
        print("Erreur de syntaxe :", err)
        log_edit(request, target, "syntax_error", error_text=err)
        return 7
    diff = "".join(difflib.unified_diff(current_code.splitlines(True), new_code.splitlines(True),
                                        f"{name} (actuel)", f"{name} (propose)"))
    added = sum(1 for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff.splitlines() if l.startswith("-") and not l.startswith("---"))
    size = len(new_code.encode("utf-8"))
    sha = hashlib.sha256(new_code.encode("utf-8")).hexdigest()
    if dry_run:
        print(f"DRY RUN : +{added} / -{removed} lignes, {size} octets (actuel {len(current_code.encode('utf-8'))}). "
              "Rien n'est ecrit.\n")
        print(diff[:4000] or "(aucune difference)")
        log_edit(request, target, "dry_run", sha=sha, taille=size)
        return 0
    with open(NEW_CODE, "w", encoding="utf-8") as f:
        f.write(new_code)
    with open(NEW_DIFF, "w", encoding="utf-8") as f:
        f.write(diff)
    edit_id = log_edit(request, target_path, "en_attente", sha=sha, taille=size)
    msg = (f"Modification proposee pour {name}. Taille : {size} octets (+{added} / -{removed} lignes). "
           f"/valider_edit {edit_id} /refuser_edit {edit_id}")
    print(msg, "\nProposition : nouveau_code.py ; differences : nouveau_code.diff")
    if telegram:
        send_telegram(msg)
    return 0


def appliquer(edit_id):
    """Après /valider_edit : sauvegarde, écriture, contrôle, retour arrière si échec."""
    conn = db()
    row = conn.execute("SELECT * FROM edits WHERE id=?", (edit_id,)).fetchone()
    conn.close()
    if not row or row["status"] != "en_attente":
        return False, "Aucune proposition en attente avec cet ID."
    if not os.path.exists(NEW_CODE):
        return False, "nouveau_code.py introuvable."
    new_code = open(NEW_CODE, "r", encoding="utf-8").read()
    if hashlib.sha256(new_code.encode("utf-8")).hexdigest() != row["sha256"]:
        set_status(edit_id, "refuse_empreinte", error_text="nouveau_code.py modifie depuis la proposition")
        return False, "nouveau_code.py a ete modifie depuis la proposition : refuse."
    target = row["target"]
    backup = backup_file(target)
    try:
        fd, tmp = tempfile.mkstemp(suffix=".py", prefix="selfedit_", dir=os.path.dirname(target))
        os.close(fd)
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(new_code)
        os.replace(tmp, target)
        ok, err = validate_syntax(target)
        if not ok:
            raise RuntimeError(err)
    except Exception as e:
        shutil.copy2(backup, target)
        set_status(edit_id, "update_error", backup_path=backup, error_text=str(e)[:500])
        return False, f"Echec, retour arriere effectue : {str(e)[:200]}"
    set_status(edit_id, "success", backup_path=backup)
    return True, f"{os.path.basename(target)} mis a jour. Sauvegarde : {os.path.basename(backup)}."


def refuser(edit_id):
    conn = db()
    row = conn.execute("SELECT status FROM edits WHERE id=?", (edit_id,)).fetchone()
    conn.close()
    if not row or row["status"] != "en_attente":
        return False, "Aucune proposition en attente avec cet ID."
    set_status(edit_id, "refuse")
    return True, "Proposition refusee : rien n'a ete modifie."


def main():
    p = argparse.ArgumentParser(description="Modification du Cortex par le modele, sous validation Telegram")
    p.add_argument("--request", "-r")
    p.add_argument("--target", "-t", default="cortex.py")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sans-telegram", action="store_true", help="n'envoie pas la notification (tests)")
    p.add_argument("--valider", type=int, metavar="ID")
    p.add_argument("--refuser", type=int, metavar="ID")
    a = p.parse_args()
    try:
        if a.valider:
            ok, msg = appliquer(a.valider)
            print(msg)
            return 0 if ok else 1
        if a.refuser:
            ok, msg = refuser(a.refuser)
            print(msg)
            return 0 if ok else 1
        if not a.request:
            p.error("--request est obligatoire")
        return propose(a.request, a.target, a.dry_run, telegram=not a.sans_telegram)
    except Exception:
        traceback.print_exc()
        return 8


if __name__ == "__main__":
    sys.exit(main())
