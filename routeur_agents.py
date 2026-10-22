"""Routeur d'agents du Copilote : choisit l'agent (prompt spécialisé + outils) selon la demande.

L'ordre compte : les intentions d'outils (copilote.py, analyse_multi_outils.py) d'abord, puis des
mots-clés, sinon le Copilote généraliste. Le badge s'affiche en haut de chaque réponse.

Outils réellement branchés (22/10/2026) :
  Développeur            : Black (formatage) + analyse syntaxique + Pylint (erreurs), sans exécuter le code
  Data Analyst           : pandas / openpyxl (lecture) + DuckDB (totaux et moyennes par catégorie)
  Designer               : Pillow (redimensionner, diaporama), rembg (fond supprimé, sur ce PC),
                           Pollinations.ai (génération d'image : seul le texte de la demande part)
  Analyste documentaire  : pdfplumber (PDF), python-docx (Word)
  Expert SEO & Web       : requests + BeautifulSoup + Playwright + certificat TLS (pyseoa et
                           website-seo-audit écartés : paquets d'un seul auteur, une à quatre versions)
  Planificateur          : icalendar (fichiers .ics)
"""

import re

R = re.IGNORECASE
AGENTS = {
    "dev": ("🛠️ Agent Développeur", "AGENT ACTIF : Développeur Python. Code propre, lisible, commenté en français ; "
            "explique en 2 phrases comment l'utiliser ; aucune dépendance inutile ; jamais de secret ni de mot de passe "
            "dans le code."),
    "data": ("📊 Agent Data Analyst", "AGENT ACTIF : Data Analyst. Appuie-toi sur les totaux et moyennes calculés par "
             "DuckDB fournis dans le contexte (ne recalcule pas de tête) ; chiffres clés, tendances, anomalies, puis 3 "
             "recommandations ; dis ce qui manque pour conclure."),
    "designer": ("🎨 Agent Designer", "AGENT ACTIF : Designer. Retouche, génération et montage de médias dans le "
                 "Workspace, toujours après validation. Jamais de faux avis, faux témoignages, fausses captures ni "
                 "visages de personnes réelles sans leur accord."),
    "doc": ("📄 Agent Analyste documentaire", "AGENT ACTIF : Analyste documentaire. Résume, structure, traduit ou "
            "compare des documents (PDF, Word, texte) fidèlement, sans rien ajouter ; cite la page ou la section."),
    "seo": ("📈 Agent Expert SEO", "AGENT ACTIF : Expert SEO & Web. Référencement local (fiche Google, balises, vitesse, "
            "mobile, contenu, liens) ; priorise par impact pour une TPE/PME ; chaque constat cite sa mesure."),
    "planif": ("🗓️ Agent Planificateur", "AGENT ACTIF : Planificateur. Priorités (urgent/important), créneaux "
               "matin/après-midi, pauses et marge d'imprévu ; une seule priorité absolue par jour."),
    "general": ("🧭 Copilote généraliste", ""),
}
MOTS = (
    ("designer", re.compile(r"\b(image|photo|logo|visuel|fond|arri[èe]re-plan|vid[ée]o|diaporama|montage|retouche\w*)\b", R)),
    ("doc", re.compile(r"\b(pdf|docx?|word|document|contrat|r[ée]sume\w*|tradu\w*)\b", R)),
    ("data", re.compile(r"\b(donn[ée]es|csv|excel|xlsx|tableau|statistiques?|chiffres?|graphique|ce fichier|le fichier)\b", R)),
    ("dev", re.compile(r"\b(code|coder|script|python|fonction|programme|html|css|javascript|bug)\b", R)),
    ("seo", re.compile(r"\b(seo|r[ée]f[ée]rencement|audit|site web|google|visibilit[ée]|balise|mots?-cl[ée]s)\b", R)),
    ("planif", re.compile(r"\b(planifi\w*|planning|agenda|journ[ée]e|semaine|organis\w*|priorit[ée]s?|calendrier)\b", R)),
)
PAR_OUTIL = {"creer": "dev", "modifier": "dev", "planifier": "planif", "graphique": "data", "image": "designer",
             "video": "designer", "fond": "designer", "generer_image": "designer", "diaporama": "designer",
             "video_texte": "designer", "liste": "general", "email": "general"}


def choisir(texte, fichier_actif=None):
    """Clé de l'agent pour ce message."""
    import analyse_multi_outils as M
    import copilote
    outil = copilote.detecter(texte)
    if outil == "document":
        nom = (texte or "").lower()
        return "data" if re.search(r"\.(csv|xlsx?)\b", nom) else "doc"
    if outil in PAR_OUTIL:
        return PAR_OUTIL[outil]
    analyse = M.detecter(texte)
    if analyse in ("audit_site", "clients"):
        return "seo"
    if analyse in ("entreprise", "concurrence", "osint"):
        return "data"
    cle = next((c for c, rx in MOTS if rx.search(texte or "")), None)
    if cle:
        return cle
    if fichier_actif:  # « analyse-le », « qu'en penses-tu » juste après un téléversement
        ext = fichier_actif.rsplit(".", 1)[-1].lower()
        return {"csv": "data", "xlsx": "data", "xls": "data", "pdf": "doc", "docx": "doc", "txt": "doc",
                "md": "doc", "png": "designer", "jpg": "designer", "jpeg": "designer", "webp": "designer"}.get(ext, "general")
    return "general"


def badge(cle):
    return AGENTS[cle][0]


def prompt(cle):
    return AGENTS[cle][1]
