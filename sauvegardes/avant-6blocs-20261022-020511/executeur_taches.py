"""Exécuteur du Copilote : actions réelles sur le PC, UNIQUEMENT après le clic « Valider l'exécution ».

Principe (demande de JOSY du 22/10/2026) : le Copilote propose, JOSY valide, le Cortex agit.

  - Tout se passe dans un seul dossier : WORKSPACE (C:\\Users\\JOSY EI\\Cortex-Workspace).
    Chemins relatifs seulement ; refus de « .. », des chemins absolus, des lecteurs, des liens,
    des noms réservés de Windows et des extensions non prévues. Jamais le dossier du Cortex.
  - Le Cortex écrit des fichiers ; il n'exécute JAMAIS le code qu'il écrit. Seul ffmpeg (outil
    installé, arguments fixes) est lancé pour couper une vidéo du Workspace.
  - Écraser un fichier = copie préalable dans Workspace\\.sauvegardes\\.
  - Une action proposée est enregistrée (table actions_copilote) avec un jeton à usage unique ;
    elle ne s'exécute que si l'interface renvoie ce jeton, depuis une session ouverte. Elle
    expire au bout de 2 heures. Chaque proposition, exécution ou refus est journalisé (I1).
  - Une action n'est jamais proposée à partir d'un contenu lu sur le web : seulement à partir de
    ce que JOSY a tapé (protection contre l'injection d'instructions).
"""

import json
import re
import secrets
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKSPACE = Path(r"C:\Users\JOSY EI\Cortex-Workspace")
CORTEX_DIR = Path(__file__).resolve().parent
EXT_TEXTE = {".txt", ".md", ".html", ".htm", ".css", ".js", ".py", ".json", ".csv", ".ics", ".xml"}
EXT_IMAGE = {".png", ".jpg", ".jpeg", ".webp"}
EXT_VIDEO = {".mp4", ".mov", ".mkv", ".webm"}
EXT_TABLEUR = {".xlsx", ".xls"}
RESERVES = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
TAILLE_MAX = 2_000_000
EXPIRATION_S = 2 * 3600
SCHEMA = """CREATE TABLE IF NOT EXISTS actions_copilote (
  id TEXT PRIMARY KEY, cree_le TEXT, type TEXT, params TEXT, apercu TEXT, jeton TEXT,
  statut TEXT DEFAULT 'proposee', expire REAL, execute_le TEXT, resultat TEXT)"""


class Refus(ValueError):
    """Action refusée par les garde-fous (message lisible pour JOSY)."""


# --------------------------------------------------------------------------- chemins
def chemin_sur(relatif, extensions=None):
    """Chemin absolu sûr dans le Workspace, ou Refus."""
    brut = (relatif or "").strip().replace("\\", "/").strip("/")
    if not brut:
        raise Refus("nom de fichier vide")
    if re.match(r"^[a-zA-Z]:", brut) or brut.startswith(("/", "~")) or "\x00" in brut:
        raise Refus("chemin absolu refusé : indique un nom relatif au Workspace")
    parties = brut.split("/")
    for p in parties:
        if p in ("", ".", "..") or p.startswith("."):
            raise Refus("chemin invalide (.., dossier caché ou vide)")
        if p.split(".")[0].lower() in RESERVES or re.search(r'[<>:"|?*]', p):
            raise Refus(f"nom réservé ou caractère interdit : {p}")
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    cible = (WORKSPACE / Path(*parties)).resolve()
    racine = WORKSPACE.resolve()
    if racine not in cible.parents:
        raise Refus("le chemin sort du Workspace")
    if CORTEX_DIR == cible or CORTEX_DIR in cible.parents:
        raise Refus("le dossier du Cortex est interdit")
    courant = racine
    for p in parties:  # aucun lien symbolique ou jonction sur le trajet
        courant = courant / p
        if courant.is_symlink():
            raise Refus("lien symbolique refusé")
    if extensions is not None and cible.suffix.lower() not in extensions:
        raise Refus(f"extension {cible.suffix or '(aucune)'} non autorisée ici")
    return cible


def _sauvegarder(cible):
    """Copie d'un fichier existant avant écrasement. Renvoie le chemin de la copie."""
    if not cible.exists():
        return None
    dossier = WORKSPACE / ".sauvegardes"
    dossier.mkdir(exist_ok=True)
    copie = dossier / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{cible.name}"
    shutil.copy2(cible, copie)
    return copie


def relatif(p):
    return str(Path(p).resolve().relative_to(WORKSPACE.resolve()))


# --------------------------------------------------------------------------- lecture (sans validation)
def lister():
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    return sorted(relatif(p) for p in WORKSPACE.rglob("*")
                  if p.is_file() and ".sauvegardes" not in p.parts)[:200]


def lire(relatif_, max_car=12000):
    cible = chemin_sur(relatif_, EXT_TEXTE)
    if not cible.exists():
        raise Refus(f"fichier introuvable dans le Workspace : {relatif_}")
    return cible.read_text(encoding="utf-8", errors="replace")[:max_car]


def analyser_donnees(relatif_):
    """Résumé d'un CSV ou d'un Excel avec pandas (lecture seule)."""
    import pandas as pd
    cible = chemin_sur(relatif_, {".csv"} | EXT_TABLEUR)
    if not cible.exists():
        raise Refus(f"fichier introuvable dans le Workspace : {relatif_}")
    if cible.suffix.lower() == ".csv":
        df = pd.read_csv(cible, sep=None, engine="python", nrows=200_000)
    else:
        df = pd.read_excel(cible, nrows=200_000)
    resume = [f"Fichier : {relatif_} · {len(df)} lignes · {len(df.columns)} colonnes",
              "Colonnes : " + ", ".join(f"{c} ({t})" for c, t in df.dtypes.astype(str).items())]
    num = df.select_dtypes("number")
    if not num.empty:
        resume.append("Statistiques des colonnes numériques :\n" + num.describe().round(2).to_string())
    for col in df.select_dtypes(exclude="number").columns[:3]:
        resume.append(f"Valeurs les plus fréquentes de « {col} » :\n" + df[col].value_counts().head(5).to_string())
    resume.append("Valeurs manquantes : " + ", ".join(f"{c} {n}" for c, n in df.isna().sum().items() if n) or "aucune")
    return "\n\n".join(resume), df


# --------------------------------------------------------------------------- propositions
def preparer(db):
    db.execute(SCHEMA)
    db.commit()


def proposer(store, type_, params, apercu):
    """Enregistre une action en attente de validation. Renvoie (id, jeton)."""
    executeurs = {"ecrire_fichier": _ecrire, "image_redimensionner": _image_redimensionner,
                  "video_couper": _video_couper, "calendrier": _calendrier, "graphique": _graphique}
    if type_ not in executeurs:
        raise Refus(f"action inconnue : {type_}")
    preparer(store.db)
    _verifier_params(type_, params)  # refus immédiat si le chemin est mauvais
    aid, jeton = uuid.uuid4().hex[:12], secrets.token_urlsafe(24)
    store.db.execute("INSERT INTO actions_copilote(id, cree_le, type, params, apercu, jeton, expire) "
                     "VALUES(?,?,?,?,?,?,?)", (aid, datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                              type_, json.dumps(params, ensure_ascii=False), apercu[:20000],
                                              jeton, time.time() + EXPIRATION_S))
    store.db.commit()
    store.log("EXECUTIF", "copilote_action_proposee", details={"id": aid, "type": type_,
                                                               "cible": params.get("chemin") or params.get("dest")})
    return aid, jeton


def _verifier_params(type_, p):
    if type_ == "ecrire_fichier":
        chemin_sur(p["chemin"], EXT_TEXTE)
        if len(p.get("contenu", "").encode("utf-8")) > TAILLE_MAX:
            raise Refus("contenu trop volumineux")
    elif type_ == "image_redimensionner":
        chemin_sur(p["source"], EXT_IMAGE)
        chemin_sur(p["dest"], EXT_IMAGE)
    elif type_ == "video_couper":
        chemin_sur(p["source"], EXT_VIDEO)
        chemin_sur(p["dest"], EXT_VIDEO)
    elif type_ == "calendrier":
        chemin_sur(p["chemin"], {".ics"})
    elif type_ == "graphique":
        chemin_sur(p["source"], {".csv"} | EXT_TABLEUR)
        chemin_sur(p["dest"], {".png"})


def executer(store, aid, jeton):
    """Exécute l'action validée par JOSY. Renvoie un message ; lève Refus si invalide."""
    preparer(store.db)
    row = store.db.execute("SELECT * FROM actions_copilote WHERE id=?", (aid,)).fetchone()
    if not row or not secrets.compare_digest(row["jeton"] or "", jeton or ""):
        store.log("JUDICIAIRE", "copilote_validation_refusee", details={"id": aid, "raison": "jeton"})
        raise Refus("validation invalide (jeton incorrect)")
    if row["statut"] != "proposee":
        raise Refus(f"cette action est déjà « {row['statut']} »")
    if row["expire"] < time.time():
        store.db.execute("UPDATE actions_copilote SET statut='expiree' WHERE id=?", (aid,))
        store.db.commit()
        raise Refus("action expirée (plus de 2 heures) : redemande-la")
    store.db.execute("UPDATE actions_copilote SET statut='en_cours', jeton=NULL WHERE id=?", (aid,))
    store.db.commit()  # usage unique, même si l'exécution échoue
    params = json.loads(row["params"])
    try:
        message = {"ecrire_fichier": _ecrire, "image_redimensionner": _image_redimensionner,
                   "video_couper": _video_couper, "calendrier": _calendrier,
                   "graphique": _graphique}[row["type"]](params)
        statut = "executee"
    except Refus:
        statut, message = "refusee", None
        raise
    except Exception as exc:
        statut, message = "echec", f"Échec : {type(exc).__name__}. Rien d'autre n'a été modifié."
    finally:
        store.db.execute("UPDATE actions_copilote SET statut=?, execute_le=?, resultat=? WHERE id=?",
                         (statut, datetime.now(timezone.utc).isoformat(timespec="seconds"), message, aid))
        store.db.commit()
        store.log("HUMAIN" if statut == "executee" else "EXECUTIF", f"copilote_action_{statut}",
                  details={"id": aid, "type": row["type"]})
    return message


def annuler(store, aid):
    preparer(store.db)
    store.db.execute("UPDATE actions_copilote SET statut='annulee', jeton=NULL WHERE id=? AND statut='proposee'", (aid,))
    store.db.commit()
    store.log("HUMAIN", "copilote_action_annulee", details={"id": aid})


# --------------------------------------------------------------------------- exécuteurs
def _ecrire(p):
    cible = chemin_sur(p["chemin"], EXT_TEXTE)
    cible.parent.mkdir(parents=True, exist_ok=True)
    copie = _sauvegarder(cible)
    cible.write_text(p.get("contenu", ""), encoding="utf-8")
    return (f"Fichier enregistré : {cible}" + (f" (ancienne version copiée dans {copie.name})" if copie else ""))


def _image_redimensionner(p):
    from PIL import Image, ImageOps
    src, dest = chemin_sur(p["source"], EXT_IMAGE), chemin_sur(p["dest"], EXT_IMAGE)
    if not src.exists():
        raise Refus(f"image introuvable : {p['source']}")
    im = ImageOps.exif_transpose(Image.open(src))
    im.thumbnail((int(p["largeur"]), int(p["hauteur"])), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    copie = _sauvegarder(dest)
    (im.convert("RGB") if dest.suffix.lower() in (".jpg", ".jpeg") else im).save(dest)
    return f"Image enregistrée : {dest} ({im.width}×{im.height})" + (f", ancienne copiée ({copie.name})" if copie else "")


def ffmpeg():
    return shutil.which("ffmpeg")


def _video_couper(p):
    exe = ffmpeg()
    if not exe:
        raise Refus("ffmpeg n'est pas installé sur ce PC")
    src, dest = chemin_sur(p["source"], EXT_VIDEO), chemin_sur(p["dest"], EXT_VIDEO)
    if not src.exists():
        raise Refus(f"vidéo introuvable : {p['source']}")
    debut, fin = str(p["debut"]), str(p["fin"])
    if not all(re.fullmatch(r"\d{1,2}(:\d{2}){0,2}(\.\d+)?", t) for t in (debut, fin)):
        raise Refus("temps invalides (format 00:01:30 ou 90)")
    copie = _sauvegarder(dest)
    r = subprocess.run([exe, "-y", "-hide_banner", "-loglevel", "error", "-ss", debut, "-to", fin,
                        "-i", str(src), "-c", "copy", str(dest)], capture_output=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg")
    return f"Vidéo enregistrée : {dest}" + (f", ancienne copiée ({copie.name})" if copie else "")


def _ics_texte(t):
    return re.sub(r"([,;\\])", r"\\\1", str(t)).replace("\n", "\\n")


def _calendrier(p):
    cible = chemin_sur(p["chemin"], {".ics"})
    lignes = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//JOSY EI//Cortex Copilote//FR", "CALSCALE:GREGORIAN"]
    for ev in p["evenements"]:
        debut = datetime.fromisoformat(ev["debut"])
        fin = datetime.fromisoformat(ev["fin"]) if ev.get("fin") else debut + timedelta(hours=1)
        lignes += ["BEGIN:VEVENT", f"UID:{uuid.uuid4()}@cortex.josyei",
                   f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
                   f"DTSTART;TZID=Europe/Paris:{debut.strftime('%Y%m%dT%H%M%S')}",
                   f"DTEND;TZID=Europe/Paris:{fin.strftime('%Y%m%dT%H%M%S')}",
                   f"SUMMARY:{_ics_texte(ev['titre'])}"]
        if ev.get("description"):
            lignes.append(f"DESCRIPTION:{_ics_texte(ev['description'])}")
        lignes.append("END:VEVENT")
    lignes.append("END:VCALENDAR")
    cible.parent.mkdir(parents=True, exist_ok=True)
    copie = _sauvegarder(cible)
    cible.write_text("\r\n".join(lignes) + "\r\n", encoding="utf-8")
    return (f"Calendrier enregistré : {cible} ({len(p['evenements'])} événement(s)). Double-clique dessus pour "
            "l'importer dans ton agenda." + (f" Ancienne version copiée ({copie.name})." if copie else ""))


def _graphique(p):
    """Histogramme simple (Pillow) : une colonne, valeurs les plus fréquentes ou somme par catégorie."""
    from PIL import Image, ImageDraw, ImageFont
    _, df = analyser_donnees(p["source"])
    col = p["colonne"]
    if col not in df.columns:
        raise Refus(f"colonne introuvable : {col}")
    serie = df[col].value_counts().head(12)
    dest = chemin_sur(p["dest"], {".png"})
    larg, haut, marge = 1000, 600, 70
    im = Image.new("RGB", (larg, haut), (11, 20, 39))
    d = ImageDraw.Draw(im)
    police, petite = ImageFont.load_default(size=22), ImageFont.load_default(size=14)
    d.text((marge, 20), f"{col} : valeurs les plus fréquentes", font=police, fill="white")
    maxi = max(int(serie.max()), 1)
    pas = (larg - 2 * marge) / max(len(serie), 1)
    for i, (k, v) in enumerate(serie.items()):
        h = (haut - 2 * marge - 40) * int(v) / maxi
        x0 = marge + i * pas + 6
        d.rectangle([x0, haut - marge - h, x0 + pas - 12, haut - marge], fill=(43, 181, 173))
        d.text((x0, haut - marge - h - 18), str(v), font=petite, fill="white")
        d.text((x0, haut - marge + 6), str(k)[:14], font=petite, fill=(180, 195, 215))
    dest.parent.mkdir(parents=True, exist_ok=True)
    copie = _sauvegarder(dest)
    im.save(dest)
    return f"Graphique enregistré : {dest}" + (f", ancien copié ({copie.name})" if copie else "")
