"""Super-pouvoirs du Copilote (22/10/2026) : documentation locale, recherche approfondie, rapports PDF,
mémoire long terme explicite.

Choix techniques (local, léger, sans téléchargement de modèle) :
  - Documentation : index plein texte SQLite FTS5 (classement BM25) dans cortex.db, par utilisateur.
    LangChain/LlamaIndex + ChromaDB/FAISS demanderaient un modèle d'embeddings (PyTorch, plus d'1 Go)
    pour un gain faible sur quelques dizaines de documents d'entreprise.
  - Recherche web : DuckDuckGo (bibliothèque ddgs, déjà installée), résultats publics seulement.
  - PDF : fpdf2 (pur Python), police Arial de Windows pour les accents.
"""

import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import executeur_taches as X

DOCS = X.WORKSPACE / "documentation"
RAPPORTS = X.WORKSPACE / "rapports"
EXT_DOCS = {".pdf", ".docx", ".xlsx", ".xls", ".csv", ".txt", ".md"}
MORCEAU = 900
SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS docs_index USING fts5(texte, fichier UNINDEXED, utilisateur_id UNINDEXED,
  tokenize = "unicode61 remove_diacritics 2");
CREATE TABLE IF NOT EXISTS docs_fichiers (id INTEGER PRIMARY KEY AUTOINCREMENT, utilisateur_id INTEGER, fichier TEXT,
  morceaux INTEGER, ajoute_le TEXT, UNIQUE(utilisateur_id, fichier));
"""
MOTS_VIDES = set("le la les un une des de du au aux et ou en à a est sont dans pour par sur avec que qui quoi quel quelle "
                 "quels quelles mon ma mes ton ta tes son sa ses ce cette ces il elle ils elles je tu nous vous on ne pas "
                 "plus moins comment combien pourquoi où quand y se sa leur leurs être avoir fait faire".split())


def preparer(db):
    db.executescript(SCHEMA)
    db.commit()


# --------------------------------------------------------------------------- documentation (RAG local)
def dossier_docs(uid):
    d = DOCS / f"u{int(uid)}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def indexer(store, uid, nom, donnees):
    """Enregistre un document de l'utilisateur et l'indexe par morceaux. Renvoie (ok, message)."""
    preparer(store.db)
    nom = X.nom_propre(nom)
    if Path(nom).suffix.lower() not in EXT_DOCS:
        return False, "Type non accepté : PDF, Word, Excel, CSV ou texte."
    if not donnees or len(donnees) > X.UPLOAD_MAX_HORS_VIDEO:
        return False, "Fichier vide ou trop gros (10 Mo au plus)."
    ext = Path(nom).suffix.lower()
    if ext in X.SIGNATURES and not donnees.startswith(X.SIGNATURES[ext]):
        return False, "Le contenu ne correspond pas à l'extension du fichier."
    cible = dossier_docs(uid) / nom
    cible.write_bytes(donnees)
    rel = cible.relative_to(X.WORKSPACE).as_posix()
    try:
        texte = X.extrait(rel, max_car=400_000)
    except Exception as exc:
        cible.unlink(missing_ok=True)
        return False, f"Texte illisible ({type(exc).__name__})."
    if len(texte.strip()) < 40:
        return False, "Ce document ne contient pas de texte lisible (scan ? il faudrait l'OCR)."
    store.db.execute("DELETE FROM docs_index WHERE fichier=? AND utilisateur_id=?", (nom, uid))
    morceaux = [texte[i:i + MORCEAU] for i in range(0, len(texte), MORCEAU - 150)]  # chevauchement de 150
    store.db.executemany("INSERT INTO docs_index(texte, fichier, utilisateur_id) VALUES(?,?,?)",
                         [(m, nom, uid) for m in morceaux if m.strip()])
    store.db.execute("INSERT INTO docs_fichiers(utilisateur_id, fichier, morceaux, ajoute_le) VALUES(?,?,?,datetime('now')) "
                     "ON CONFLICT(utilisateur_id, fichier) DO UPDATE SET morceaux=excluded.morceaux, ajoute_le=excluded.ajoute_le",
                     (uid, nom, len(morceaux)))
    store.db.commit()
    store.log("HUMAIN", "document_indexe", details={"utilisateur_id": uid, "fichier": nom, "morceaux": len(morceaux)})
    return True, f"« {nom} » indexé ({len(morceaux)} passage(s)) : le Cortex le consultera pour répondre."


def documents(store, uid):
    preparer(store.db)
    return store.db.execute("SELECT * FROM docs_fichiers WHERE utilisateur_id=? ORDER BY id DESC", (uid,)).fetchall()


def retirer(store, uid, fichier):
    preparer(store.db)
    store.db.execute("DELETE FROM docs_index WHERE fichier=? AND utilisateur_id=?", (fichier, uid))
    store.db.execute("DELETE FROM docs_fichiers WHERE fichier=? AND utilisateur_id=?", (fichier, uid))
    store.db.commit()
    (dossier_docs(uid) / X.nom_propre(fichier)).unlink(missing_ok=True)


def chercher(store, uid, question, n=4):
    """Passages les plus pertinents (BM25) de la documentation de l'utilisateur : [(fichier, extrait)]."""
    preparer(store.db)
    mots = [m for m in re.findall(r"\w{3,}", (question or "").lower()) if m not in MOTS_VIDES][:12]
    if not mots:
        return []
    requete = " OR ".join(f'"{m}"' for m in mots)
    try:
        rows = store.db.execute("SELECT fichier, texte FROM docs_index WHERE docs_index MATCH ? AND utilisateur_id=? "
                                "ORDER BY bm25(docs_index) LIMIT ?", (requete, uid, n)).fetchall()
    except sqlite3.OperationalError:
        return []
    return [(r[0], re.sub(r"\s+", " ", r[1]).strip()) for r in rows]


# --------------------------------------------------------------------------- mémoire long terme explicite
RETIENS_RE = re.compile(r"^\s*(?:retiens|souviens[- ]toi|m[ée]morise|note)\s+(?:bien\s+)?(?:que|qu['’]|de|:)?\s*(.+)$",
                        re.IGNORECASE | re.S)
OUBLIE_RE = re.compile(r"^\s*oublie\s+(?:que|qu['’])?\s*(.+)$", re.IGNORECASE | re.S)


def commande_memoire(store, uid, texte):
    """« Retiens que je facture 50 €/h » → fait enregistré tel quel (sans IA). Renvoie la réponse ou None."""
    import comptes
    m = RETIENS_RE.match(texte or "")
    if m:
        fait = re.sub(r"\s+", " ", m.group(1)).strip(" .")[:300]
        if len(fait) < 4:
            return "Que dois-je retenir ? Exemple : « Retiens que je facture 50 €/h »."
        if comptes.SENSIBLE_RE.search(fait):
            return ("Je ne retiens pas cette information : elle contient une donnée sensible (coordonnées, mot de passe, "
                    "numéro bancaire, santé…).")
        fait = fait[0].upper() + fait[1:]
        comptes.migrer(store)
        store.db.execute("INSERT OR IGNORE INTO memoire_agent(utilisateur_id, fait, cree_le) VALUES(?,?,datetime('now'))",
                         (uid, "Retenu à ta demande : " + fait))
        store.db.commit()
        store.log("HUMAIN", "memoire_retenue", details={"utilisateur_id": uid})
        return (f"C'est noté : « {fait} ». Je l'utiliserai dans mes réponses, devis et calculs. Tu peux le voir ou "
                "l'effacer dans Mon Agent › Ce que je sais de vous.")
    m = OUBLIE_RE.match(texte or "")
    if m:
        cle = m.group(1).strip(" .")[:80]
        n = store.db.execute("DELETE FROM memoire_agent WHERE utilisateur_id=? AND fait LIKE ?", (uid, f"%{cle}%")).rowcount
        store.db.commit()
        return f"{n} souvenir(s) effacé(s)." if n else "Je ne trouve rien de tel dans ma mémoire."
    return None


# --------------------------------------------------------------------------- recherche approfondie (3 en parallèle)
def actualites(nom, commune=None, n=6):
    """Résultats web publics (actualités, avis, presse) sur une entreprise, par la recherche déjà configurée
    du Cortex (source_web : Serper si autorisé, sinon Brave ou DuckDuckGo). Rien n'est inventé : [] si rien."""
    import source_web
    requete = f"{nom}" + (f" {commune}" if commune else "") + " avis actualités"
    res = source_web.recherche(requete, n) or []
    actualites.source = source_web.derniere_source
    return [{"titre": r.get("title"), "extrait": (r.get("description") or "")[:220], "lien": r.get("url")} for r in res]


def recherche_approfondie(nom, url=None):
    """Registre public, audit du site et actualités/avis, lancés en parallèle (3 fils)."""
    import analyse_multi_outils as M
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_reg = pool.submit(M.analyse_entreprise_siren, nom)
        f_site = pool.submit(M.analyse_site_web, url) if url else None
        reg = f_reg.result()
        commune = next((r["donnees"].get("commune") for r in reg if r["ok"]), None)
        f_web = pool.submit(actualites, next((r["donnees"].get("nom") for r in reg if r["ok"]), nom), commune)
        resultats = list(reg)
        if f_site:
            resultats.append(f_site.result())
        try:
            items = f_web.result()
            resultats.append(M._resultat("actualites_avis_web", f"recherche web ({getattr(actualites, 'source', None) or '?'})",
                                         {"resultats": len(items), "exemples": [f"{i['titre']} : {i['extrait']} ({i['lien']})"
                                                                                for i in items]}))
        except Exception as exc:
            resultats.append(M._resultat("actualites_avis_web", "DuckDuckGo", erreur=type(exc).__name__))
    return resultats


# --------------------------------------------------------------------------- rapports PDF
def _texte_pdf(s):
    """Caractères que la police Arial sait dessiner (les émojis sont retirés)."""
    return re.sub(r"[\U00010000-\U0010FFFF\u2600-\u27BF\uFE0F]", "", s or "")


def generer_rapport_pdf(contenu_texte, nom_fichier, titre="Rapport d'analyse"):
    """PDF avec en-tête JOSY EI, date, contenu et pied de page. Renvoie le chemin relatif au Workspace."""
    from fpdf import FPDF
    RAPPORTS.mkdir(parents=True, exist_ok=True)
    nom = X.nom_propre(nom_fichier if nom_fichier.lower().endswith(".pdf") else nom_fichier + ".pdf")

    class Rapport(FPDF):
        def header(self):
            self.set_fill_color(11, 21, 48)
            self.rect(0, 0, 210, 22, "F")
            self.set_text_color(255, 255, 255)
            self.set_font("Arial", "B", 14)
            self.set_xy(12, 7)
            self.cell(0, 8, "JOSY EI · Le Cortex")
            self.set_font("Arial", "", 9)
            self.set_xy(-72, 8)
            self.cell(60, 8, datetime.now().strftime("Généré le %d/%m/%Y à %H:%M"), align="R")
            self.set_text_color(20, 20, 20)
            self.set_y(30)

        def footer(self):
            self.set_y(-14)
            self.set_font("Arial", "", 8)
            self.set_text_color(110, 110, 110)
            self.cell(0, 6, f"JOSY EI · Montmorillon (86) · josyei.com · Document généré par le Cortex, à vérifier "
                            f"avant diffusion · page {self.page_no()}/{{nb}}", align="C")

    pdf = Rapport()
    pdf.add_font("Arial", "", r"C:\Windows\Fonts\arial.ttf")
    pdf.add_font("Arial", "B", r"C:\Windows\Fonts\arialbd.ttf")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(True, margin=20)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.multi_cell(0, 9, _texte_pdf(titre), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    for ligne in _texte_pdf(contenu_texte).splitlines():
        if not ligne.strip():
            pdf.ln(3)
            continue
        majuscules = ligne.strip().isupper() and len(ligne.strip()) > 3
        pdf.set_font("Arial", "B" if majuscules else "", 12 if majuscules else 10)
        pdf.multi_cell(0, 6 if majuscules else 5, ligne.rstrip(), new_x="LMARGIN", new_y="NEXT")
    cible = RAPPORTS / nom
    pdf.output(str(cible))
    return cible.relative_to(X.WORKSPACE).as_posix()
