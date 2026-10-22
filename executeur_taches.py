"""Exécuteur du Copilote : actions réelles sur le PC, UNIQUEMENT après le clic « Valider l'exécution ».

Principe (demande de JOSY du 22/10/2026) : le Copilote propose, JOSY valide, le Cortex agit.

  - Tout se passe dans un seul dossier : WORKSPACE (C:\\Users\\JOSY EI\\C:\Users\JOSY EI\cortex).
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

WORKSPACE = Path(r"C:\Users\JOSY EI\C:\Users\JOSY EI\cortex")
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
    resume += totaux_duckdb(df)
    return "\n\n".join(resume), df


def totaux_duckdb(df):
    """Totaux et moyennes par catégorie, calculés par DuckDB (le modèle ne recalcule pas de tête)."""
    try:
        import duckdb
    except ImportError:
        return []
    blocs = []
    nums = list(df.select_dtypes("number").columns[:2])
    cats = [c for c in df.select_dtypes(exclude="number").columns if df[c].nunique() <= 50][:3]
    con = duckdb.connect()
    try:
        con.register("t", df)
        for cat in cats:
            for num in nums:
                rows = con.execute(f'SELECT "{cat}", SUM("{num}"), AVG("{num}"), COUNT(*) FROM t GROUP BY 1 '
                                   f'ORDER BY 2 DESC NULLS LAST LIMIT 8').fetchall()
                blocs.append(f"Total de « {num} » par « {cat} » (calcul DuckDB, du plus grand au plus petit) :\n"
                             + "\n".join(f"  {k} : total {s:,.2f} · moyenne {m:,.2f} · {n} ligne(s)".replace(",", " ")
                                         for k, s, m, n in rows))
    finally:
        con.close()
    return blocs


# --------------------------------------------------------------------------- téléversement / téléchargement
EXT_AUDIO = {".wav", ".mp3", ".m4a", ".ogg"}
EXT_UPLOAD = {".csv", ".txt", ".md", ".json", ".pdf", ".xlsx", ".xls", ".docx"} | EXT_IMAGE | EXT_VIDEO | EXT_AUDIO
UPLOAD_MAX = 50 * 1024 * 1024        # vidéos comprises ; les autres fichiers : 10 Mo
UPLOAD_MAX_HORS_VIDEO = 10 * 1024 * 1024
SIGNATURES = {".pdf": (b"%PDF",), ".png": (b"\x89PNG",), ".jpg": (b"\xff\xd8",), ".jpeg": (b"\xff\xd8",),
              ".webp": (b"RIFF",), ".xlsx": (b"PK",), ".docx": (b"PK",), ".xls": (b"\xd0\xcf\x11\xe0",)}


def nom_propre(nom):
    """Nom de fichier sûr : sans dossier, sans caractère spécial, 80 caractères au plus."""
    nom = re.split(r"[\\/]", nom or "")[-1]
    base, _, ext = nom.rpartition(".")
    base = re.sub(r"[^\w\-]+", "-", base or "fichier", flags=re.UNICODE).strip("-._")[:70] or "fichier"
    return f"{base}.{ext.lower()}" if ext else base


def televerser(nom, donnees, dossier="uploads"):
    """Enregistre un fichier envoyé par JOSY dans Workspace\\uploads\\. Le fichier n'est jamais
    exécuté. Renvoie le chemin relatif ; lève Refus si type, taille ou contenu ne conviennent pas."""
    nom = nom_propre(nom)
    ext = Path(nom).suffix.lower()
    if ext not in EXT_UPLOAD:
        raise Refus(f"type {ext or '(aucun)'} non accepté (CSV, TXT, PDF, Excel, images)")
    if not donnees or len(donnees) > (UPLOAD_MAX if ext in EXT_VIDEO else UPLOAD_MAX_HORS_VIDEO):
        raise Refus("fichier vide ou trop gros (10 Mo au plus, 50 Mo pour une vidéo)")
    if ext in SIGNATURES and not donnees.startswith(SIGNATURES[ext]):
        raise Refus("le contenu ne correspond pas à l'extension du fichier")
    if ext in {".csv", ".txt", ".md", ".json"} and b"\x00" in donnees[:4096]:
        raise Refus("ce fichier n'est pas un texte")
    if dossier not in ("uploads", "voix"):
        raise Refus("dossier de dépôt inconnu")
    if (dossier == "voix") != (ext in EXT_AUDIO):
        raise Refus("les échantillons de voix vont dans « voix », les autres fichiers dans « uploads »")
    cible = chemin_sur(f"{dossier}/{nom}", EXT_UPLOAD)
    n = 1
    while cible.exists():  # ne jamais écraser un envoi précédent
        cible = chemin_sur(f"{dossier}/{Path(nom).stem}-{n}{ext}", EXT_UPLOAD)
        n += 1
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_bytes(donnees)
    return relatif(cible).replace("\\", "/")


def extrait(relatif_, max_car=8000):
    """Contenu lisible d'un fichier du Workspace, pour le contexte (DONNÉES, jamais instructions)."""
    cible = chemin_sur(relatif_, EXT_UPLOAD | EXT_TEXTE)
    ext = cible.suffix.lower()
    if ext in {".csv", ".xlsx", ".xls"}:
        return analyser_donnees(relatif_)[0][:max_car]
    if ext == ".pdf":  # pdfplumber : texte page par page (et tableaux simples)
        import pdfplumber
        with pdfplumber.open(str(cible)) as pdf:
            n = len(pdf.pages)
            texte = "\n".join(f"[page {i}] {(p.extract_text() or '').strip()}" for i, p in enumerate(pdf.pages[:30], 1))
        return (f"PDF de {n} page(s).\n" + texte)[:max_car] if re.search(r"\w", re.sub(r"\[page \d+\]", "", texte)) \
            else f"PDF de {n} page(s), sans texte extractible (document scanné : il faudrait l'OCR Tesseract)."
    if ext == ".docx":  # python-docx : paragraphes et tableaux
        import docx
        d = docx.Document(str(cible))
        parties = [p.text for p in d.paragraphs if p.text.strip()]
        for t in d.tables[:5]:
            parties += [" | ".join(c.text.strip() for c in row.cells) for row in t.rows[:30]]
        return (f"Document Word, {len(d.paragraphs)} paragraphe(s).\n" + "\n".join(parties))[:max_car]
    if ext in EXT_IMAGE:
        from PIL import Image
        with Image.open(cible) as im:
            return (f"Image {im.width}×{im.height} px, format {im.format}. Le Cortex ne voit pas le contenu de "
                    "l'image : aucun modèle de vision n'est disponible (Groq n'en propose pas sur ce compte, "
                    "Tesseract n'est pas installé).")
    if ext in EXT_VIDEO:
        return f"Vidéo de {round(cible.stat().st_size / 1_048_576, 1)} Mo (le contenu n'est pas analysé)."
    if ext in EXT_AUDIO:
        return f"Échantillon audio de {round(cible.stat().st_size / 1024)} Ko, gardé sur ce PC (rien n'est envoyé)."
    return cible.read_text(encoding="utf-8", errors="replace")[:max_car]


def pour_telechargement(relatif_):
    """Chemin d'un fichier du Workspace à télécharger, ou Refus."""
    cible = chemin_sur(relatif_, EXT_UPLOAD | EXT_TEXTE | EXT_VIDEO | {".png"})
    if not cible.is_file():
        raise Refus("fichier introuvable")
    return cible


# --------------------------------------------------------------------------- propositions
def preparer(db):
    db.execute(SCHEMA)
    db.commit()


def proposer(store, type_, params, apercu):
    """Enregistre une action en attente de validation. Renvoie (id, jeton)."""
    if type_ not in EXECUTEURS:
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
    elif type_ == "image_fond":
        chemin_sur(p["source"], EXT_IMAGE)
        chemin_sur(p["dest"], {".png"})
    elif type_ == "image_generer":
        chemin_sur(p["dest"], {".png", ".jpg"})
        if not (3 <= len(p.get("description", "")) <= 400):
            raise Refus("description d'image vide ou trop longue")
    elif type_ in ("video_diaporama", "video_texte"):
        for s in p.get("sources", []):
            chemin_sur(s, EXT_IMAGE)
        chemin_sur(p["dest"], {".mp4"})


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
        message = EXECUTEURS[row["type"]](params)
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


def fichier_produit(store, aid):
    """Chemin relatif du fichier écrit par une action exécutée (bouton Télécharger), ou None."""
    row = store.db.execute("SELECT params, statut FROM actions_copilote WHERE id=?", (aid,)).fetchone()
    if not row or row["statut"] != "executee":
        return None
    p = json.loads(row["params"])
    return (p.get("chemin") or p.get("dest") or "").replace("\\", "/") or None


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
    """Fichier .ics standard (bibliothèque icalendar, RFC 5545), heure de Paris."""
    from zoneinfo import ZoneInfo
    from icalendar import Calendar, Event
    cible = chemin_sur(p["chemin"], {".ics"})
    paris = ZoneInfo("Europe/Paris")
    cal = Calendar()
    cal.add("prodid", "-//JOSY EI//Cortex Copilote//FR")
    cal.add("version", "2.0")
    for ev in p["evenements"]:
        debut = datetime.fromisoformat(ev["debut"]).replace(tzinfo=paris)
        fin = datetime.fromisoformat(ev["fin"]).replace(tzinfo=paris) if ev.get("fin") else debut + timedelta(hours=1)
        e = Event()
        e.add("uid", f"{uuid.uuid4()}@cortex.josyei")
        e.add("dtstamp", datetime.now(timezone.utc))
        e.add("dtstart", debut)
        e.add("dtend", fin)
        e.add("summary", str(ev["titre"]))
        if ev.get("description"):
            e.add("description", str(ev["description"]))
        cal.add_component(e)
    cible.parent.mkdir(parents=True, exist_ok=True)
    copie = _sauvegarder(cible)
    cible.write_bytes(cal.to_ical())
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


# --------------------------------------------------------------------------- designer (médias)
POLLINATIONS = "https://image.pollinations.ai/prompt/"


def _image_fond(p):
    """Supprime l'arrière-plan avec rembg, sur ce PC (le modèle u2net se télécharge au premier usage)."""
    from PIL import Image, ImageOps
    from rembg import new_session, remove
    src, dest = chemin_sur(p["source"], EXT_IMAGE), chemin_sur(p["dest"], {".png"})
    if not src.exists():
        raise Refus(f"image introuvable : {p['source']}")
    # u2net (~170 Mo, quelques secondes par image) plutôt que le modèle par défaut (1 Go, plusieurs minutes).
    resultat = remove(ImageOps.exif_transpose(Image.open(src)), session=new_session("u2net"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    copie = _sauvegarder(dest)
    resultat.save(dest)
    return f"Fond supprimé : {dest} (PNG transparent)" + (f", ancien copié ({copie.name})" if copie else "")


def _image_generer(p):
    """Image générée par Pollinations.ai (gratuit, sans clé). Seule la description quitte le PC."""
    import urllib.parse
    import requests
    from PIL import Image
    import io
    dest = chemin_sur(p["dest"], {".png", ".jpg"})
    url = POLLINATIONS + urllib.parse.quote(p["description"]) + "?width=1024&height=1024&nologo=true&safe=true"
    r = requests.get(url, timeout=120, headers={"User-Agent": "JOSY-EI-Cortex/1.0"})
    if r.status_code != 200 or not r.headers.get("Content-Type", "").startswith("image/"):
        raise RuntimeError(f"pollinations {r.status_code}")
    im = Image.open(io.BytesIO(r.content))  # vérifie que c'est bien une image
    dest.parent.mkdir(parents=True, exist_ok=True)
    copie = _sauvegarder(dest)
    (im.convert("RGB") if dest.suffix.lower() == ".jpg" else im).save(dest)
    return f"Image générée : {dest} ({im.width}×{im.height})" + (f", ancienne copiée ({copie.name})" if copie else "")


def _carton(texte, taille=(1280, 720)):
    """Image de texte (Pillow) : fond bleu nuit, texte centré, retour à la ligne automatique."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", taille, (11, 20, 39))
    d = ImageDraw.Draw(im)
    police = ImageFont.load_default(size=54)
    mots, lignes, ligne = texte.split(), [], ""
    for m in mots:
        essai = (ligne + " " + m).strip()
        if d.textlength(essai, font=police) > taille[0] - 160 and ligne:
            lignes.append(ligne)
            ligne = m
        else:
            ligne = essai
    lignes.append(ligne)
    y = taille[1] / 2 - len(lignes) * 34
    for l in lignes[:8]:
        d.text((taille[0] / 2, y), l, font=police, fill="white", anchor="ma")
        y += 68
    return im


def _video(images, dest, secondes):
    """Assemble des images (Pillow) en MP4 avec moviepy (ffmpeg du PC)."""
    import numpy as np
    from moviepy.editor import ImageClip, concatenate_videoclips
    clips = [ImageClip(np.array(im.convert("RGB").resize((1280, 720)))).set_duration(secondes) for im in images]
    film = concatenate_videoclips(clips, method="compose")
    dest.parent.mkdir(parents=True, exist_ok=True)
    copie = _sauvegarder(dest)
    film.write_videofile(str(dest), fps=24, codec="libx264", audio=False, logger=None)
    film.close()
    return copie


def _video_diaporama(p):
    from PIL import Image, ImageOps
    dest = chemin_sur(p["dest"], {".mp4"})
    images = []
    for s in p["sources"][:30]:
        src = chemin_sur(s, EXT_IMAGE)
        if not src.exists():
            raise Refus(f"image introuvable : {s}")
        images.append(ImageOps.pad(ImageOps.exif_transpose(Image.open(src)).convert("RGB"), (1280, 720),
                                   color=(11, 20, 39)))
    if not images:
        raise Refus("aucune image pour le diaporama")
    copie = _video(images, dest, float(p.get("secondes", 3)))
    return f"Diaporama enregistré : {dest} ({len(images)} image(s))" + (f", ancien copié ({copie.name})" if copie else "")


def _video_texte(p):
    dest = chemin_sur(p["dest"], {".mp4"})
    cartons = [_carton(t) for t in p["textes"][:10] if t.strip()]
    if not cartons:
        raise Refus("aucun texte pour la vidéo")
    copie = _video(cartons, dest, float(p.get("secondes", 4)))
    return f"Vidéo enregistrée : {dest} ({len(cartons)} carton(s))" + (f", ancienne copiée ({copie.name})" if copie else "")


# --------------------------------------------------------------------------- développeur (vérification)
def verifier_python(code):
    """Formate avec Black et vérifie la syntaxe (ast) puis les erreurs (Pylint, analyse statique).
    Le code n'est JAMAIS exécuté. Renvoie (code formaté, liste de remarques)."""
    import ast
    remarques = []
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return code, [f"Erreur de syntaxe ligne {exc.lineno} : {exc.msg}"]
    try:
        import black
        code = black.format_str(code, mode=black.Mode(line_length=100))
        remarques.append("Formaté par Black.")
    except Exception as exc:
        remarques.append(f"Black n'a pas pu formater ({type(exc).__name__}).")
    dossier = WORKSPACE / ".verif"
    dossier.mkdir(parents=True, exist_ok=True)
    tmp = dossier / f"verif_{uuid.uuid4().hex[:8]}.py"
    tmp.write_text(code, encoding="utf-8")
    try:
        import sys
        r = subprocess.run([sys.executable, "-m", "pylint", "--errors-only", "--disable=import-error",
                            "--score=n", "--output-format=text", str(tmp)],
                           capture_output=True, text=True, timeout=60, cwd=str(dossier))
        erreurs = [l.split(":", 3)[-1].strip() for l in r.stdout.splitlines() if re.match(r".*:\d+:\d+: E\d+", l)]
        remarques.append("Pylint : aucune erreur détectée." if not erreurs
                         else "Pylint : " + " ; ".join(erreurs[:5]))
    except Exception as exc:
        remarques.append(f"Pylint indisponible ({type(exc).__name__}).")
    finally:
        tmp.unlink(missing_ok=True)
    return code, remarques


EXECUTEURS = {"ecrire_fichier": _ecrire, "image_redimensionner": _image_redimensionner,
              "video_couper": _video_couper, "calendrier": _calendrier, "graphique": _graphique,
              "image_fond": _image_fond, "image_generer": _image_generer,
              "video_diaporama": _video_diaporama, "video_texte": _video_texte}
