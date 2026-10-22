#!/usr/bin/env python3
"""Mémoire du Cortex — index plein texte en lecture seule (SQLite FTS5).

Usage :
  python memoire.py build  [--src DIR] [--db FICHIER]   # (re)construit l'index
  python memoire.py search "experts-comptables facturation électronique" [-k 5] [--type secteur]
  python memoire.py check  [--src DIR]                  # contrôle qualité des fiches

Principes (voir 70-acces-cortex/spec-acces-memoire.md) :
  - L'index est reconstruit depuis les fiches Markdown ; le Cortex l'ouvre en
    LECTURE SEULE (URI SQLite mode=ro). Il ne peut ni écrire ni modifier la mémoire.
  - Seuls les fichiers *.md sous le dossier de la mémoire sont lus. Les fichiers
    sensibles (.env, clés, secrets) sont refusés, et toute fiche contenant un motif
    de secret ou de donnée personnelle est rejetée de l'index.
  - Chaque passage renvoyé porte son identifiant `fiche#section`, sa date, son
    niveau de confiance et ses sources (URL + date) : le Cortex doit les citer.
Aucune dépendance hors bibliothèque standard Python 3.9+.
"""
import argparse
import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # dossier cortex-memoire/
DEFAULT_DB = ROOT / "memoire.db"
EXCLUDED_DIRS = {"outils", ".git", "__pycache__"}
FORBIDDEN_NAMES = re.compile(r"(^\.env|secret|token|credential|\.key$|\.pem$|id_rsa)", re.I)

# Motifs qui ne doivent jamais entrer dans la mémoire (I4 + sécurité).
SECRET_PATTERNS = {
    "cle_groq": re.compile(r"\bgsk_[A-Za-z0-9]{20,}"),
    "cle_openai": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    "token_telegram": re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"),
    "cle_aws": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "cle_google": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "mot_de_passe": re.compile(r"(?i)\b(password|mot de passe|passwd|pwd)\s*[:=]\s*[\w!@#$%^&*.\-]{6,}"),
}
PERSONAL_PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "telephone": re.compile(r"(?:\+33|\b0)\s*[1-9](?:[\s.-]*\d{2}){4}\b"),
}
SOURCE_LINE = re.compile(r"^\s*[-*]?\s*\[(S\d+)\]\s*(.+)$")
URL_RE = re.compile(r"https?://[^\s)>\]]+")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
REF_RE = re.compile(r"\[(S\d+)\]")

SCHEMA = """
CREATE TABLE IF NOT EXISTS fiches(
  id TEXT PRIMARY KEY, type TEXT, titre TEXT, chemin TEXT, mis_a_jour TEXT,
  confiance TEXT, revoir_avant TEXT, tags TEXT, sha256 TEXT);
CREATE TABLE IF NOT EXISTS sources(
  fiche_id TEXT, ref TEXT, titre TEXT, url TEXT, publie TEXT, consulte TEXT,
  PRIMARY KEY(fiche_id, ref));
CREATE TABLE IF NOT EXISTS sections(
  id INTEGER PRIMARY KEY, fiche_id TEXT, section TEXT, ancre TEXT, texte TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(
  titre, section, texte, tags,
  tokenize='unicode61 remove_diacritics 2');
CREATE TABLE IF NOT EXISTS meta(cle TEXT PRIMARY KEY, valeur TEXT);
"""


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def parse_frontmatter(text):
    """En-tête YAML minimal (clé: valeur, listes [a, b]) sans dépendance externe."""
    meta, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                if ":" not in line or line.strip().startswith("#"):
                    continue
                k, v = line.split(":", 1)
                v = v.split(" #", 1)[0].strip().strip('"').strip("'")
                if v.startswith("[") and v.endswith("]"):
                    v = [x.strip().strip('"').strip("'") for x in v[1:-1].split(",") if x.strip()]
                meta[k.strip()] = v
            body = text[end + 4:].lstrip("\n")
    return meta, body


def split_sections(body):
    """Découpe sur les titres `## ` ; le texte avant le premier titre devient « Résumé »."""
    sections, title, buf = [], "Résumé", []
    for line in body.splitlines():
        if line.startswith("## "):
            if "".join(buf).strip():
                sections.append((title, "\n".join(buf).strip()))
            title, buf = line[3:].strip(), []
        else:
            buf.append(line)
    if "".join(buf).strip():
        sections.append((title, "\n".join(buf).strip()))
    return sections


def parse_sources(text):
    out = {}
    for line in text.splitlines():
        m = SOURCE_LINE.match(line)
        if not m:
            continue
        ref, rest = m.group(1), m.group(2)
        url = URL_RE.search(rest)
        dates = DATE_RE.findall(rest)
        out[ref] = {
            "titre": re.split(r"\s+[—–-]\s+", rest, maxsplit=1)[0].strip()[:200],
            "url": url.group(0).rstrip(".,;") if url else "",
            "publie": dates[0] if len(dates) >= 2 else (dates[0] if dates and "publi" in rest else ""),
            "consulte": dates[-1] if dates else "",
        }
    return out


GENERIC_LOCAL = {"contact", "accueil", "info", "infos", "cabinet", "office", "secretariat",
                 "bonjour", "hello", "admin", "direction", "commercial", "dpo", "rgpd", "support"}
FICTIVE_DOMAIN = re.compile(r"(\.invalid|\.example|\.test|example\.(com|fr|org))$", re.I)


def personal_email(addr):
    """Adresse nominative réelle ? Les génériques (contact@…) et domaines fictifs sont tolérés."""
    local, _, domain = addr.lower().rpartition("@")
    gabarit = re.fullmatch(r"(prenom|nom|p|n|initiale)([._-](prenom|nom|p|n|initiale))*", local)
    return not (local in GENERIC_LOCAL or gabarit or FICTIVE_DOMAIN.search(domain.rstrip(".")))


def scan_forbidden(text):
    hits = [k for k, rx in SECRET_PATTERNS.items() if rx.search(text)]
    if any(personal_email(m) for m in PERSONAL_PATTERNS["email"].findall(text)):
        hits.append("email_nominatif")
    if PERSONAL_PATTERNS["telephone"].search(text):
        hits.append("telephone")
    return hits


def iter_fiches(src):
    src = src.resolve()
    for p in sorted(src.rglob("*.md")):
        rel = p.relative_to(src)
        if any(part in EXCLUDED_DIRS or part.startswith(".") for part in rel.parts[:-1]):
            continue
        if FORBIDDEN_NAMES.search(p.name) or p.is_symlink():
            continue
        if src not in p.resolve().parents:          # pas de sortie du dossier
            continue
        yield p, rel


# ---------------------------------------------------------------- construction
def build(src=ROOT, db_path=DEFAULT_DB, verbose=True):
    tmp = Path(str(db_path) + ".tmp")
    if tmp.exists():
        tmp.unlink()
    db = sqlite3.connect(tmp)
    db.executescript(SCHEMA)
    rejets, n_sec = [], 0
    for path, rel in iter_fiches(Path(src)):
        text = path.read_text(encoding="utf-8")
        hits = scan_forbidden(text)
        if hits:
            rejets.append((str(rel), hits))
            continue
        meta, body = parse_frontmatter(text)
        fid = meta.get("id") or path.stem
        tags = meta.get("tags", [])
        tags = " ".join(tags) if isinstance(tags, list) else str(tags)
        sections = split_sections(body)
        srcs = {}
        for title, content in sections:
            if title.lower().startswith("sources"):
                srcs.update(parse_sources(content))
        db.execute("INSERT OR REPLACE INTO fiches VALUES(?,?,?,?,?,?,?,?,?)", (
            fid, meta.get("type", ""), meta.get("titre", path.stem), str(rel),
            meta.get("mis_a_jour", ""), meta.get("confiance", "basse"),
            meta.get("revoir_avant", ""), tags, hashlib.sha256(text.encode()).hexdigest()))
        for ref, s in srcs.items():
            db.execute("INSERT OR REPLACE INTO sources VALUES(?,?,?,?,?,?)",
                       (fid, ref, s["titre"], s["url"], s["publie"], s["consulte"]))
        for title, content in sections:
            if title.lower().startswith("sources"):
                continue
            cur = db.execute("INSERT INTO sections(fiche_id, section, ancre, texte) VALUES(?,?,?,?)",
                             (fid, title, slug(title), content))
            db.execute("INSERT INTO sections_fts(rowid, titre, section, texte, tags) VALUES(?,?,?,?,?)",
                       (cur.lastrowid, meta.get("titre", ""), title, content, tags))
            n_sec += 1
    db.execute("INSERT OR REPLACE INTO meta VALUES('construit_le', ?)", (date.today().isoformat(),))
    db.execute("INSERT OR REPLACE INTO meta VALUES('rejets', ?)", (json.dumps(rejets, ensure_ascii=False),))
    db.commit()
    db.close()
    Path(tmp).replace(db_path)
    if verbose:
        n_f = sqlite3.connect(db_path).execute("SELECT COUNT(*) FROM fiches").fetchone()[0]
        print(f"Index : {n_f} fiches, {n_sec} sections -> {db_path}")
        for r, h in rejets:
            print(f"  REJETÉE {r} : {', '.join(h)}")
    return rejets


# ---------------------------------------------------------------- lecture seule
class Memoire:
    """Accès en lecture seule utilisé par cortex.py (pouvoir exécutif)."""

    def __init__(self, db_path=DEFAULT_DB):
        uri = Path(db_path).resolve().as_uri() + "?mode=ro"
        self.db = sqlite3.connect(uri, uri=True)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA query_only = ON")

    @staticmethod
    def fts_query(texte):
        """Texte libre -> requête FTS5 sûre (aucun opérateur injecté)."""
        mots = [m for m in re.findall(r"\w+", texte.lower()) if len(m) > 2]
        return " OR ".join(f'"{m}"' for m in mots[:12])

    def search(self, texte, k=5, type_=None):
        q = self.fts_query(texte)
        if not q:
            return []
        sql = ("SELECT s.id, s.fiche_id, s.section, s.ancre, s.texte, f.titre, f.type, "
               "f.mis_a_jour, f.confiance, f.revoir_avant, bm25(sections_fts, 2.0, 3.0, 1.0, 2.0) AS score "
               "FROM sections_fts JOIN sections s ON s.id = sections_fts.rowid "
               "JOIN fiches f ON f.id = s.fiche_id WHERE sections_fts MATCH ?")
        args = [q]
        if type_:
            sql += " AND f.type = ?"
            args.append(type_)
        sql += " ORDER BY score LIMIT ?"
        args.append(k)
        out = []
        for r in self.db.execute(sql, args):
            refs = sorted(set(REF_RE.findall(r["texte"])), key=lambda x: int(x[1:]))
            srcs = [dict(ref=x["ref"], url=x["url"], publie=x["publie"], consulte=x["consulte"])
                    for x in self.db.execute(
                        f"SELECT * FROM sources WHERE fiche_id=? AND ref IN ({','.join('?' * len(refs))})",
                        [r["fiche_id"], *refs])] if refs else []
            perime = bool(r["revoir_avant"]) and r["revoir_avant"] < date.today().isoformat()
            out.append({
                "citation": f"memoire:{r['fiche_id']}#{r['ancre']}",
                "fiche": r["titre"], "section": r["section"], "type": r["type"],
                "mis_a_jour": r["mis_a_jour"], "confiance": r["confiance"], "perime": perime,
                "texte": r["texte"], "sources": srcs,
            })
        return out

    def contexte_pour_prompt(self, texte, k=4, max_chars=6000):
        """Bloc à insérer dans le message utilisateur envoyé au modèle."""
        blocs, total = [], 0
        for p in self.search(texte, k=k):
            extrait = p["texte"][:1800]
            src = "; ".join(f"[{s['ref']}] {s['url']} ({s['publie'] or s['consulte']})" for s in p["sources"])
            alerte = " — FICHE À REVÉRIFIER" if p["perime"] else ""
            bloc = (f"### {p['citation']} | {p['fiche']} > {p['section']} | maj {p['mis_a_jour']} "
                    f"| confiance {p['confiance']}{alerte}\n{extrait}\nSources : {src or 'aucune'}")
            if total + len(bloc) > max_chars:
                break
            blocs.append(bloc)
            total += len(bloc)
        return "\n\n".join(blocs)

    def sources_connues(self, passages):
        """{url normalisée: (url, date)} des sources citées par les passages, pour le Judiciaire."""
        out = {}
        for p in passages:
            for s in p["sources"]:
                if s["url"]:
                    out[s["url"].lower().rstrip("/")] = (s["url"], s["publie"] or s["consulte"])
        return out


# ---------------------------------------------------------------- contrôle qualité
def check(src=ROOT):
    today, problemes = date.today().isoformat(), 0
    num = re.compile(r"\b\d[\d  ,.]*\s?(%|€|k€|M€|millions?|milliards?|salariés|entreprises)")
    for path, rel in iter_fiches(Path(src)):
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        notes = []
        for k in ("id", "type", "titre", "mis_a_jour", "confiance"):
            if k not in meta:
                notes.append(f"en-tête sans '{k}'")
        if meta.get("id") and meta["id"] != path.stem:
            notes.append("id différent du nom de fichier")
        if meta.get("revoir_avant") and meta["revoir_avant"] < today:
            notes.append("fiche périmée (revoir_avant dépassé)")
        if meta.get("type") not in ("schema", "acces", "entreprise"):
            sections = split_sections(body)
            srcs = {}
            for t, c in sections:
                if t.lower().startswith("sources"):
                    srcs.update(parse_sources(c))
            if not srcs:
                notes.append("aucune section Sources")
            cited = set(REF_RE.findall(body))
            if cited - set(srcs):
                notes.append(f"renvois sans source : {sorted(cited - set(srcs))}")
            sans = 0
            for line in body.splitlines():
                if num.search(line) and not REF_RE.search(line) and "estimation" not in line \
                        and "non vérifié" not in line and not line.lstrip().startswith(("[S", "|---")):
                    sans += 1
            if sans:
                notes.append(f"{sans} ligne(s) chiffrée(s) sans renvoi ni marqueur")
        hits = scan_forbidden(text)
        if hits:
            notes.append(f"MOTIF INTERDIT : {hits}")
        if notes:
            problemes += 1
            print(f"{rel}:")
            for n in notes:
                print(f"   - {n}")
    print(f"{problemes} fiche(s) avec remarques.")
    return problemes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--src", default=ROOT); b.add_argument("--db", default=DEFAULT_DB)
    s = sub.add_parser("search"); s.add_argument("texte"); s.add_argument("-k", type=int, default=5)
    s.add_argument("--type"); s.add_argument("--db", default=DEFAULT_DB)
    s.add_argument("--prompt", action="store_true", help="affiche le bloc tel qu'envoyé au modèle")
    c = sub.add_parser("check"); c.add_argument("--src", default=ROOT)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        build(Path(a.src), Path(a.db))
    elif a.cmd == "search":
        m = Memoire(a.db)
        if a.prompt:
            print(m.contexte_pour_prompt(a.texte, k=a.k))
        else:
            for p in m.search(a.texte, k=a.k, type_=a.type):
                print(f"{p['citation']}  ({p['confiance']}, maj {p['mis_a_jour']})"
                      f"{'  PÉRIMÉE' if p['perime'] else ''}\n   {p['texte'][:220].replace(chr(10), ' ')}…")
                for s_ in p["sources"]:
                    print(f"   [{s_['ref']}] {s_['url']}")
    elif a.cmd == "check":
        sys.exit(1 if check(Path(a.src)) else 0)


if __name__ == "__main__":
    main()
