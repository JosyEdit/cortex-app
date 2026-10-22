"""Socle multi-utilisateurs (test local, 22/10/2026) : comptes entreprise, espaces isolés, mémoire.

Ce que c'est : un socle pour tester l'inscription de futurs clients SUR CE PC. Ce n'est pas un SaaS
exposé : avant un vrai client, il faudra un hébergement, un contrat de sous-traitance RGPD, un
registre des traitements et une politique de confidentialité (décision antérieure de JOSY).

  - Chaque table de données porte une colonne utilisateur_id. Les données existantes (751
    entreprises, emails, journal…) sont rattachées au compte fondateur (valeur par défaut).
  - Le moteur de prospection (cortex.py) reste celui de JOSY EI : un client n'en voit rien.
  - Un client a son Copilote, son historique, son prompt (issu du registre public) et sa mémoire.
  - Le fondateur voit, dans « Super Admin », la liste des comptes, leur date d'inscription et leur
    nombre d'échanges, jamais leurs conversations ni leur mémoire.
"""

import json
import re
import time

TABLES = ("entreprises", "proposals", "envois", "file_envoi", "reponses", "app_chat", "actions_copilote",
          "chat_historique", "journal", "candidates", "signaux", "articles")
SCHEMA = """
CREATE TABLE IF NOT EXISTS comptes_entreprise (
  utilisateur_id INTEGER PRIMARY KEY, nom TEXT, siren TEXT, naf TEXT, commune TEXT,
  prompt_systeme TEXT, cree_le TEXT);
CREATE TABLE IF NOT EXISTS memoire_agent (
  id INTEGER PRIMARY KEY AUTOINCREMENT, utilisateur_id INTEGER, fait TEXT, cree_le TEXT,
  UNIQUE(utilisateur_id, fait));
"""
SIREN_RE = re.compile(r"(?<!\d)(\d{3})\s?(\d{3})\s?(\d{3})(?!\d)")
INSCRIPTIONS_MAX_HEURE = 5
_inscriptions = []


def fondateur_id(store):
    row = store.db.execute("SELECT id FROM utilisateurs WHERE role='fondateur' ORDER BY id LIMIT 1").fetchone()
    return row[0] if row else 1


def migrer(store):
    """Ajoute utilisateur_id (défaut : le fondateur) aux tables de données. Sans perte, rejouable."""
    import connexion
    connexion.preparer(store)
    store.db.executescript(SCHEMA)
    fid = int(fondateur_id(store))
    ajoutees = []
    for t in TABLES:
        if not store.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone():
            continue
        cols = {r[1] for r in store.db.execute(f"PRAGMA table_info({t})")}
        if "utilisateur_id" not in cols:
            # DEFAULT : les lignes existantes et les insertions du moteur restent au fondateur.
            store.db.execute(f"ALTER TABLE {t} ADD COLUMN utilisateur_id INTEGER DEFAULT {fid}")
            ajoutees.append(t)
    store.db.commit()
    if ajoutees:
        store.log("SYSTEME", "migration_multi_utilisateurs", details={"tables": ajoutees, "fondateur_id": fid})
    return ajoutees


def utilisateur(store, email):
    return store.db.execute("SELECT * FROM utilisateurs WHERE email=?", ((email or "").lower(),)).fetchone()


def est_fondateur(session):
    return bool(session) and session[1] == "fondateur"


# --------------------------------------------------------------------------- inscription
def extraire_siren(texte):
    """SIREN (9 chiffres) à partir d'un SIREN, d'un SIRET (14 chiffres : les 9 premiers) ou d'un lien
    societe.com / pappers / annuaire."""
    chiffres = re.sub(r"[^\d]", " ", texte or "")
    siret = re.search(r"(?<!\d)(\d{14})(?!\d)", chiffres.replace(" ", "") if len(re.sub(r"\D", "", texte or "")) == 14
                      else chiffres)
    if siret:
        return siret.group(1)[:9]
    m = SIREN_RE.search(chiffres)
    return "".join(m.groups()) if m else None


def siren_valide(siren):
    """Clé de Luhn (contrôle officiel du SIREN)."""
    total = 0
    for i, ch in enumerate(reversed(siren)):
        n = int(ch) * (2 if i % 2 else 1)
        total += n - 9 if n > 9 else n
    return total % 10 == 0


# Secteur lisible à partir de la section NAF (nomenclature INSEE), et métier précis pour des codes courants.
SECTIONS_NAF = {"A": "Agriculture", "B": "Industries extractives", "C": "Industrie", "D": "Énergie",
                "E": "Eau et déchets", "F": "BTP", "G": "Commerce", "H": "Transport et logistique",
                "I": "Hôtellerie-restauration", "J": "Informatique et communication", "K": "Finance et assurance",
                "L": "Immobilier", "M": "Conseil et services aux entreprises", "N": "Services administratifs",
                "O": "Administration publique", "P": "Enseignement", "Q": "Santé et action sociale",
                "R": "Arts, spectacles et loisirs", "S": "Services de proximité", "T": "Services aux ménages",
                "U": "Organisations internationales"}
METIERS_NAF = {"43.22A": "la plomberie (installation d'eau et de gaz)", "43.22B": "le chauffage et la climatisation",
               "43.21A": "l'électricité du bâtiment", "43.32A": "la menuiserie", "43.34Z": "la peinture et la vitrerie",
               "41.20A": "la construction de maisons individuelles", "43.99C": "la maçonnerie",
               "56.10A": "la restauration traditionnelle", "56.10C": "la restauration rapide",
               "69.20Z": "l'expertise comptable", "69.10Z": "le conseil juridique", "86.21Z": "la médecine générale",
               "86.23Z": "la pratique dentaire", "96.02A": "la coiffure", "96.02B": "les soins de beauté",
               "45.20A": "l'entretien et la réparation automobile", "10.71C": "la boulangerie-pâtisserie",
               "68.31Z": "l'agence immobilière", "62.02A": "le conseil en systèmes et logiciels informatiques",
               "62.01Z": "le développement informatique", "47.73Z": "la pharmacie", "49.32Z": "le taxi",
               "55.10Z": "l'hôtellerie", "71.11Z": "l'architecture", "74.10Z": "le design",
               "73.11Z": "la publicité", "85.59A": "la formation continue"}


def secteur_naf(naf, section):
    """(secteur, métier) à partir du code NAF et de sa section ; jamais inventé."""
    secteur = SECTIONS_NAF.get((section or "").upper(), "Secteur à préciser")
    return secteur, METIERS_NAF.get(naf or "", f"l'activité NAF {naf}" if naf else "son activité")


def prompt_client(nom, libelle, commune, secteur=None, effectif=None):
    """Prompt système du client : uniquement des faits venus du registre public ou de l'inscription."""
    return (f"Tu es l'assistant IA de l'entreprise {nom}, spécialisée dans {libelle}"
            + (f" (secteur : {secteur})" if secteur else "")
            + (f", basée à {commune}" if commune else "")
            + (f", effectif déclaré : {effectif}" if effectif and effectif != "non publié" else "")
            + ". Tu accompagnes le dirigeant dans ses tâches quotidiennes : organisation, rédaction, analyse, "
            "relation client. Ton naturel et professionnel, "
            "vouvoiement, réponses directes et structurées (Analyse, Proposition, Action pour un problème). "
            "N'invente aucun fait, chiffre ni client ; si tu ne sais pas, dis-le. Tu ne déclenches aucune action : "
            "tu proposes, le dirigeant décide. Les données de cet espace restent sur le PC qui héberge le Cortex ; "
            "le texte de la conversation passe par le service Groq pour obtenir ta réponse.")


def _colonnes(store):
    """Colonnes ajoutées le 22/10/2026 (données du registre, vérification)."""
    cols = {r[1] for r in store.db.execute("PRAGMA table_info(comptes_entreprise)")}
    for nom, type_ in (("secteur", "TEXT"), ("effectif", "TEXT"), ("adresse", "TEXT"), ("raison_sociale", "TEXT"),
                       ("verifie", "INTEGER DEFAULT 1")):
        if nom not in cols:
            store.db.execute(f"ALTER TABLE comptes_entreprise ADD COLUMN {nom} {type_}")
    store.db.commit()


def inscrire(store, C, email, mdp, nom, siren_ou_lien, manuel=False):
    """Crée un compte client. Renvoie (ok, message, résumé ou None).

    Le SIREN (ou SIRET) est vérifié côté serveur dans le registre public. Introuvable : refus, avec la
    possibilité de créer le compte manuellement. Registre en panne : création en mode manuel, compte
    marqué « SIREN à vérifier »."""
    import analyse_entreprise as AE
    import connexion
    maintenant = time.time()
    _inscriptions[:] = [t for t in _inscriptions if maintenant - t < 3600]
    if len(_inscriptions) >= INSCRIPTIONS_MAX_HEURE:
        return False, "Trop d'inscriptions en une heure : réessayez plus tard.", None
    email = (email or "").strip().lower()
    nom = (nom or "").strip()[:120]
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", email):
        return False, "Adresse email invalide.", None
    if len(mdp or "") < connexion.MDP_MIN:
        return False, f"Le mot de passe doit faire au moins {connexion.MDP_MIN} caractères.", None
    if not nom:
        return False, "Indiquez le nom de l'entreprise.", None
    siren = extraire_siren(siren_ou_lien)
    if not siren or not siren_valide(siren):
        return False, "Numéro invalide : SIREN (9 chiffres) ou SIRET (14 chiffres).", None
    migrer(store)
    _colonnes(store)
    if utilisateur(store, email):
        return False, "Un compte existe déjà avec cette adresse.", None
    e, panne = None, False
    if not manuel:
        try:
            e, _ = AE.registre(siren)
        except Exception:
            panne = True  # registre en maintenance : on ne bloque pas l'inscription
        if not panne and (not e or e.get("siren") != siren):
            return False, ("Entreprise introuvable. Vérifiez votre SIREN ou créez votre compte manuellement."), "manuel"
    if e:
        siege = e.get("siege") or {}
        naf = e.get("activite_principale")
        secteur, metier = secteur_naf(naf, e.get("section_activite_principale"))
        effectif = AE.TRANCHES.get(e.get("tranche_effectif_salarie"), "non publié")
        ei = e.get("nature_juridique") == "1000"  # entreprise individuelle : nom et adresse personnels
        infos = {"raison_sociale": None if ei else e.get("nom_raison_sociale") or e.get("nom_complet"),
                 "naf": naf, "commune": siege.get("libelle_commune"), "secteur": secteur, "metier": metier,
                 "effectif": effectif, "adresse": None if ei else siege.get("adresse"), "verifie": 1}
    else:  # mode manuel (choisi, ou registre indisponible)
        infos = {"raison_sociale": None, "naf": None, "commune": None, "secteur": "Secteur à préciser",
                 "metier": "son activité", "effectif": None, "adresse": None, "verifie": 0}
    _inscriptions.append(maintenant)
    connexion.creer_compte(store, C, email, "client", mdp)
    uid = utilisateur(store, email)["id"]
    store.db.execute("INSERT INTO comptes_entreprise(utilisateur_id, nom, siren, naf, commune, prompt_systeme, cree_le, "
                     "secteur, effectif, adresse, raison_sociale, verifie) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                     (uid, nom, siren, infos["naf"], infos["commune"],
                      prompt_client(nom, infos["metier"], infos["commune"],
                                    infos["secteur"] if infos["verifie"] else None, infos["effectif"]),
                      C.iso(C.now()), infos["secteur"], infos["effectif"], infos["adresse"], infos["raison_sociale"],
                      infos["verifie"]))
    store.db.commit()
    store.log("SYSTEME", "compte_client_cree", details={"utilisateur_id": uid, "naf": infos["naf"],
                                                         "verifie": infos["verifie"], "registre_en_panne": panne})
    resume = dict(infos, nom=nom, siren=siren, panne=panne)
    if not infos["verifie"]:
        return True, ("Compte créé en mode manuel : le registre public " + ("ne répond pas" if panne else "n'a pas été "
                      "consulté") + f". Le SIREN {siren} reste à vérifier."), resume
    return True, f"Bienvenue {nom} ! Votre agent IA est configuré pour le secteur {infos['secteur']}.", resume


def compte(store, uid):
    return store.db.execute("SELECT * FROM comptes_entreprise WHERE utilisateur_id=?", (uid,)).fetchone()


# --------------------------------------------------------------------------- mémoire de l'agent
SENSIBLE_RE = re.compile(
    r"[\w.+-]+@[\w-]+\.[\w.]+|(?:\+33|0)\s*[1-9](?:[\s.-]*\d{2}){4}|\bFR\d{2}(?:\s?\d{4}){3,}|"
    r"\b(?:\d{4}[\s-]?){3}\d{4}\b|mot de passe|password|\bmdp\b|identifiant|login|"
    r"sant[ée]|maladie|m[ée]dical|religio|politique|syndica|orientation sexuelle|casier|"
    r"num[ée]ro de s[ée]curit[ée] sociale|\bnir\b|iban|carte bancaire", re.I)
EXTRACTION = """Extrais du message de l'utilisateur les FAITS DURABLES sur son entreprise, utiles à l'assistant plus tard
(ex. offre, tarifs qu'il pratique, cibles, zone, outils utilisés, contraintes, préférences de travail).
Interdit : données personnelles ou sensibles (santé, opinions, coordonnées, mots de passe, numéros bancaires,
noms de particuliers), faits sur des tiers, suppositions. Si rien de durable, renvoie une liste vide.
Réponds en JSON : {"faits": ["phrase courte, 15 mots max", ...]} (3 au plus)."""


def apprendre(store, uid, message, llm_json):
    """Mémorise les faits durables d'un message (filtrés). Renvoie la liste retenue."""
    if len(message or "") < 25 or SENSIBLE_RE.search(message or ""):
        return []  # message trop court, ou contenant une donnée sensible : rien n'est extrait
    migrer(store)
    rep = llm_json(EXTRACTION, message[:1500]) or {}
    retenus = []
    for f in (rep.get("faits") or [])[:3]:
        f = re.sub(r"\s+", " ", str(f)).strip()[:160]
        if len(f) < 8 or SENSIBLE_RE.search(f):
            continue
        store.db.execute("INSERT OR IGNORE INTO memoire_agent(utilisateur_id, fait, cree_le) VALUES(?,?,datetime('now'))",
                         (uid, f))
        retenus.append(f)
    store.db.execute("DELETE FROM memoire_agent WHERE utilisateur_id=? AND id NOT IN (SELECT id FROM memoire_agent "
                     "WHERE utilisateur_id=? ORDER BY id DESC LIMIT 60)", (uid, uid))
    store.db.commit()
    if retenus:
        store.log("EXECUTIF", "memoire_agent_ajout", details={"utilisateur_id": uid, "faits": len(retenus)})
    return retenus


def memoire(store, uid, n=25):
    migrer(store)
    return [r[0] for r in store.db.execute("SELECT fait FROM memoire_agent WHERE utilisateur_id=? ORDER BY id DESC "
                                           "LIMIT ?", (uid, n))]


# --------------------------------------------------------------------------- super admin
def comptes_activite(store):
    """Comptes et activité agrégée, sans aucun contenu de conversation ni mémoire."""
    migrer(store)
    _colonnes(store)
    return store.db.execute(
        "SELECT u.id, u.email, u.role, u.cree_le, c.nom, c.siren, c.secteur, c.verifie, "
        " (SELECT COUNT(*) FROM app_chat a WHERE a.utilisateur_id=u.id AND a.role='josy') AS messages, "
        " (SELECT MAX(ts) FROM app_chat a WHERE a.utilisateur_id=u.id) AS derniere, "
        " (SELECT COUNT(*) FROM memoire_agent m WHERE m.utilisateur_id=u.id) AS faits "
        "FROM utilisateurs u LEFT JOIN comptes_entreprise c ON c.utilisateur_id=u.id ORDER BY u.id").fetchall()


# --------------------------------------------------------------------------- onboarding personnalisé
SCHEMA_DEPART = """CREATE TABLE IF NOT EXISTS actions_depart (
  id INTEGER PRIMARY KEY AUTOINCREMENT, utilisateur_id INTEGER, titre TEXT, description TEXT,
  consigne TEXT, statut TEXT DEFAULT 'proposee', cree_le TEXT, decide_le TEXT)"""
DEPART_PROMPT = """Tu prépares 3 actions de démarrage pour le dirigeant d'une TPE/PME qui découvre son assistant IA.
Entreprise : {nom}. Secteur : {secteur}. Activité : {metier}. Commune : {commune}. Effectif déclaré : {effectif}.
Chaque action doit être concrète, faisable avec l'assistant en quelques minutes (rédiger, préparer, organiser,
vérifier), adaptée à ce métier. Aucune promesse de résultat, aucun chiffre ni fait inventé, aucun envoi automatique.
Réponds en JSON : {{"actions": [{{"titre": "4 à 6 mots", "description": "1 phrase", "consigne": "la demande exacte
que le dirigeant enverra à son assistant pour commencer"}}, ...]}}"""

# Boutons rapides par section NAF (titre, demande pré-remplie). Repli : boutons génériques.
BOUTONS_SECTEUR = {
    "F": [("Préparer un devis", "Aide-moi à préparer un devis pour "), ("Relancer une facture", "Rédige une relance polie pour une facture impayée de "),
          ("Planifier mes chantiers", "Organise ma semaine de chantiers : ")],
    "I": [("Créer un menu", "Aide-moi à créer un menu pour "), ("Répondre à un avis", "Aide-moi à répondre à cet avis client : "),
          ("Planifier le service", "Organise les plannings de service de la semaine : ")],
    "G": [("Fiche produit", "Rédige une fiche produit pour "), ("Répondre à un client", "Aide-moi à répondre à ce client : "),
          ("Organiser l'inventaire", "Aide-moi à organiser mon inventaire : ")],
    "Q": [("Organiser mes rendez-vous", "Organise ma semaine de rendez-vous : "), ("Message aux patients", "Rédige un message d'information aux patients sur "),
          ("Procédure interne", "Rédige une procédure interne pour ")],
    "M": [("Proposition commerciale", "Aide-moi à structurer une proposition pour "), ("Compte rendu", "Rédige le compte rendu de cette réunion : "),
          ("Organiser ma semaine", "Organise ma semaine avec ces priorités : ")],
    "S": [("Message aux clients", "Rédige un message à mes clients pour "), ("Organiser mes rendez-vous", "Organise ma semaine de rendez-vous : "),
          ("Répondre à un avis", "Aide-moi à répondre à cet avis : ")],
}
BOUTONS_DEFAUT = [("Rédiger un email", "Rédige un email pour "), ("Organiser ma semaine", "Organise ma semaine avec ces priorités : "),
                  ("Analyser un problème", "Voici un problème de mon entreprise : ")]


def section_naf(naf):
    """Section NAF (lettre) à partir de la division (2 premiers chiffres), d'après la nomenclature INSEE."""
    try:
        d = int((naf or "")[:2])
    except ValueError:
        return None
    bornes = [(3, "A"), (9, "B"), (33, "C"), (35, "D"), (39, "E"), (43, "F"), (47, "G"), (53, "H"), (56, "I"),
              (63, "J"), (66, "K"), (68, "L"), (75, "M"), (82, "N"), (84, "O"), (85, "P"), (88, "Q"), (93, "R"),
              (96, "S"), (98, "T"), (99, "U")]
    return next((s for b, s in bornes if d <= b), None)


def preparer_onboarding(store):
    store.db.execute(SCHEMA_DEPART)
    cols = {r[1] for r in store.db.execute("PRAGMA table_info(comptes_entreprise)")}
    for nom, type_ in (("site_web", "TEXT"), ("chiffre_affaires", "TEXT"), ("description", "TEXT")):
        if nom not in cols:
            store.db.execute(f"ALTER TABLE comptes_entreprise ADD COLUMN {nom} {type_}")
    store.db.commit()


def generer_actions_depart(store, uid, llm_json):
    """3 actions de démarrage (Groq) selon le secteur, enregistrées pour ce compte. Repli fixe si Groq échoue."""
    preparer_onboarding(store)
    if store.db.execute("SELECT 1 FROM actions_depart WHERE utilisateur_id=?", (uid,)).fetchone():
        return
    c = compte(store, uid)
    metier = METIERS_NAF.get(c["naf"] or "", f"l'activité NAF {c['naf']}" if c["naf"] else "son activité")
    rep = llm_json(DEPART_PROMPT.format(nom=c["nom"], secteur=c["secteur"] or "à préciser", metier=metier,
                                        commune=c["commune"] or "non précisée", effectif=c["effectif"] or "non publié"),
                   "Propose les 3 actions.") or {}
    actions = [a for a in (rep.get("actions") or []) if isinstance(a, dict) and a.get("titre")][:3]
    if len(actions) < 3:  # Groq indisponible : actions génériques, honnêtes
        actions = [{"titre": t, "description": "Une première tâche simple pour découvrir votre assistant.", "consigne": p}
                   for t, p in BOUTONS_SECTEUR.get(section_naf(c["naf"]), BOUTONS_DEFAUT)]
    for a in actions:
        store.db.execute("INSERT INTO actions_depart(utilisateur_id, titre, description, consigne, cree_le) "
                         "VALUES(?,?,?,?,datetime('now'))",
                         (uid, str(a["titre"])[:80], str(a.get("description", ""))[:240], str(a.get("consigne", a["titre"]))[:300]))
    store.db.commit()


def actions_depart(store, uid):
    preparer_onboarding(store)
    return store.db.execute("SELECT * FROM actions_depart WHERE utilisateur_id=? ORDER BY id", (uid,)).fetchall()


def decider_action(store, uid, aid, decision):
    if decision not in ("acceptee", "ignoree"):
        return
    store.db.execute("UPDATE actions_depart SET statut=?, decide_le=datetime('now') WHERE id=? AND utilisateur_id=?",
                     (decision, aid, uid))
    store.db.commit()
    store.log("HUMAIN", f"action_depart_{decision}", details={"utilisateur_id": uid, "id": aid})


def boutons(store, uid):
    """Boutons rapides du client : actions de départ acceptées, puis boutons de son secteur."""
    c = compte(store, uid)
    acceptees = [(a["titre"], a["consigne"]) for a in actions_depart(store, uid) if a["statut"] == "acceptee"]
    return acceptees + BOUTONS_SECTEUR.get(section_naf(c["naf"] if c else None), BOUTONS_DEFAUT)


def modifier_entreprise(store, C, uid, champs):
    """Le client corrige ou complète ses informations ; le prompt de son agent est régénéré."""
    preparer_onboarding(store)
    c = compte(store, uid)
    nom = (champs.get("nom") or c["nom"]).strip()[:120]
    site = (champs.get("site_web") or "").strip()[:200]
    if site and not re.match(r"https?://[\w.-]+\.[a-z]{2,}", site):
        return False, "Adresse du site invalide (https://…)."
    ca = (champs.get("chiffre_affaires") or "").strip()[:60]
    desc = re.sub(r"\s+", " ", champs.get("description") or "").strip()[:400]
    metier = METIERS_NAF.get(c["naf"] or "", f"l'activité NAF {c['naf']}" if c["naf"] else "son activité")
    prompt = prompt_client(nom, metier, c["commune"], c["secteur"] if c["verifie"] else None, c["effectif"])
    complements = " ".join(x for x in (f"Site web : {site}." if site else "", f"Chiffre d'affaires indiqué par le dirigeant : {ca}." if ca else "",
                                       f"Présentation par le dirigeant : {desc}" if desc else "") if x)
    store.db.execute("UPDATE comptes_entreprise SET nom=?, site_web=?, chiffre_affaires=?, description=?, prompt_systeme=? "
                     "WHERE utilisateur_id=?", (nom, site, ca, desc, prompt + (" " + complements if complements else ""), uid))
    store.db.commit()
    store.log("HUMAIN", "entreprise_modifiee", details={"utilisateur_id": uid})
    return True, "Informations enregistrées : votre assistant en tient compte dès maintenant."
