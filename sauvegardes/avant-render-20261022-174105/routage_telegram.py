"""Routage d'intention des messages libres Telegram (couche Interface, I8).

Le bot ne décide pas : il reçoit, classe, route, répond. Il n'exécute aucune action (I3) :
une demande d'analyse devient au mieux une proposition notée, jamais un lancement.

Deux niveaux (fichier 4 §4.4 : modèle léger pour classer, modèle puissant pour rédiger) :
  - niveau 1, sans modèle : salutations, demandes d'état, « es-tu un robot ? » ;
  - niveau 2, modèle léger Groq (CLASSIFIER_MODEL) : sector_query, audit_query, osint_query,
    general_question, unknown, avec extraction du secteur, de l'entreprise et du lieu.

Chaque message et chaque réponse sont inscrits au journal chaîné de cortex.db (puissance
INTERFACE), qui tient lieu d'audit_log (I7). Les commandes « / » restent traitées par
Cortex.handle_update, comme avant.

Remplace la réponse figée « Actif · N en attente » que recevait toute phrase contenant
« ce que tu peux », « état » ou « bilan » (dont « Qu'est-ce que tu peux me dire sur les
garages ? ») : l'état n'est plus envoyé qu'en réponse à une vraie demande d'état.
"""

import json
import re
import unicodedata
from pathlib import Path

# Le plus léger des modèles Groq disponibles sur ce compte (llama-3.1-8b-instant n'y est plus
# proposé, vérifié le 19/10/2026 par GET /models).
CLASSIFIER_MODEL = "openai/gpt-oss-20b"
INTENTS = ("sector_query", "audit_query", "osint_query", "general_question", "unknown")
CONFIRMATION_S = 600  # une proposition d'analyse attend « oui » ou « non » 10 minutes

COMMANDS = {  # niveau 1 : commandes explicites (traitées par Cortex.handle_update)
    "/etat": "status", "/état": "status", "/status": "status", "/rapport": "report",
    "/pause": "pause", "/reprise": "resume", "/stop": "emergency_stop",
    "/arret": "emergency_stop", "/arrêt": "emergency_stop",
    "/valider": "validate", "/refuser": "refuse",
}
GREETINGS = ("bonjour", "salut", "hello", "bonsoir", "hey", "coucou")
STATUS_KEYWORDS = ("état", "etat", "status", "statut", "où tu en es", "ou tu en es",
                   "quoi de neuf", "bilan")
AGENT_RE = re.compile(r"\b(es|êtes|es-tu|etes)[- ]?(tu|vous)?\s*(un|une)?\s*"
                      r"(robot|bot|ia|humain|intelligence artificielle|machine|agent)\b", re.I)

INTENT_CLASSIFICATION_PROMPT = """Tu es un classificateur d'intention pour le bot Telegram de JOSY EI.
Classifie la requête suivante en UNE seule catégorie parmi :
- "sector_query" : l'utilisateur mentionne un secteur d'activité (garages, boulangerie, restaurant, coiffeur, avocat, etc.)
- "audit_query" : l'utilisateur pose une question sur un audit, un diagnostic, une analyse d'entreprise
- "osint_query" : l'utilisateur demande une recherche OSINT, des données sur une entreprise
- "general_question" : l'utilisateur pose une question générale sur le système, ses capacités, ou autre
- "unknown" : la requête n'est pas claire

Extrais aussi :
- "sector" : le nom du secteur mentionné (si applicable)
- "company_name" : le nom d'une entreprise mentionnée (si applicable)
- "location" : une ville ou région mentionnée (si applicable)

Requête : "{message}"

Réponds UNIQUEMENT en JSON : {{"intent": "...", "sector": "...", "company_name": "...", "location": "..."}}"""

BOT_SYSTEM_PROMPT = """Tu es le Cortex, l'agent IA de JOSY EI, accessible via Telegram et via son interface locale (onglet « Discuter »).

TA MISSION PREMIÈRE : l'audit, le diagnostic d'entreprise et l'analyse OSINT.

RÈGLES DE RÉPONSE :
1. Tu es factuel et concis. Pas de bla-bla inutile.
2. Si JOSY mentionne un secteur d'activité (garages, boulangerie, restaurant, etc.), tu proposes immédiatement de lancer une recherche de prospects ou une analyse OSINT pour ce secteur.
3. Si JOSY pose une question sur une entreprise, tu proposes un audit ou un diagnostic.
4. Tu ne fais AUCUNE promesse de résultat. Tu décris ce que tu peux faire.
5. Tu ne mentionnes AUCUN prix. Tu parles uniquement d'audit et de diagnostic.
6. Si tu n'as pas la réponse, tu le dis clairement et tu proposes une escalade humaine.
7. Tu t'identifies comme agent automatisé si on te le demande.

FORMAT DE RÉPONSE :
- Direct, professionnel, en français.
- Pas de listes à puces inutiles.
- Pas de répétition de la question.
- Une seule réponse claire et actionnable.

FAÇON D'AGIR (5 règles d'or, demandées par JOSY le 21/10/2026) :
1. Rédaction : ton naturel, professionnel et structuré. Pas de phrases de robot ni de formules creuses.
2. Efficacité : va droit au but. Pas de préambule, pas de résumé de la question, pas de blabla.
3. Méthode : quand JOSY expose un problème, structure ta réponse en trois temps courts : Analyse, puis Proposition, puis Action (la prochaine étape concrète, qu'il exécute ou valide lui-même).
4. Veille : tiens compte des actualités récentes, mais uniquement celles des articles que le Cortex a réellement lus (fournis ci-dessous, avec leur source). Sans article pertinent, dis que tu n'as rien lu de récent là-dessus ; n'invente aucune actualité.
5. Souveraineté : les données du Cortex (prospects, journal, profil, historique) sont stockées sur le PC de JOSY, dans cortex.db. Pour te répondre, le texte de la conversation est envoyé au service Groq, hors de son PC : ne dis jamais que tout reste 100 % local. Quand la question touche aux données, à la confidentialité ou au RGPD, donne les deux faits ensemble : stockage sur son PC, et passage du texte de la conversation par Groq.
"""

# Métiers courants -> préfixes NAF (pour retrouver « garages » dans l'annuaire déjà collecté).
METIERS_NAF = {
    "garage": ("45.20",), "garagiste": ("45.20",), "mecanicien": ("45.20",),
    "carrosserie": ("45.20",), "boulangerie": ("10.71",), "boulanger": ("10.71",),
    "patisserie": ("10.71",), "boucherie": ("10.13", "47.22"), "boucher": ("10.13", "47.22"),
    "restaurant": ("56.10",), "restauration": ("56.10",), "coiffeur": ("96.02",),
    "coiffure": ("96.02",), "plombier": ("43.22",), "plomberie": ("43.22",),
    "electricien": ("43.21",), "menuisier": ("16.23", "43.32"), "macon": ("43.99",),
    "avocat": ("69.10",), "notaire": ("69.10",), "expert-comptable": ("69.20",),
    "comptable": ("69.20",), "immobilier": ("68.31",), "agence immobiliere": ("68.31",),
}


def _plat(texte):
    """Minuscules sans accents (comparaisons tolérantes)."""
    return "".join(c for c in unicodedata.normalize("NFD", (texte or "").lower())
                   if unicodedata.category(c) != "Mn").strip()


def _singulier(mot):
    mot = _plat(mot)
    return mot[:-1] if len(mot) > 3 and mot.endswith(("s", "x")) else mot


def _vide(v):
    return v is None or str(v).strip().lower() in ("", "null", "none", "n/a", "...", "aucun", "aucune")


# ---------------------------------------------------------------------------
# Routage
# ---------------------------------------------------------------------------
# Domaine ou URL (« josyei.com », « https://www.exemple.fr/contact ») ; une adresse email n'en est pas un.
DOMAINE_RE = re.compile(
    r"(?<![@\w.-])(?:https?://)?(?:www\.)?((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:fr|com|net|org|eu|io|info|biz|be|ch|lu|ca|bzh|paris|shop|store|pro|co|app|dev|online|site|tech|"
    r"immo|bio|restaurant|garage|art|studio|agency|business|club|cafe|bar|hotel))\b(?![@-])(/\S*)?", re.I)
SIREN_RE = re.compile(r"\bSIRE[NT]\b\D{0,40}?(\d{3})\s?(\d{3})\s?(\d{3})(?:\s?\d{5})?\b", re.I)
# « scan le site web », « analyse son site », « audite le domaine »… sans domaine : on reprend le dernier
SUITE_SITE_RE = re.compile(r"\b(scan\w*|analys\w*|audit\w*|v[ée]rifi\w*|regard\w*|check\w*|teste?r?|examin\w*)\b"
                           r".{0,30}\b(site|domaine|page|web|url)\b", re.I)
# Fiche d'entreprise par son URL d'annuaire (societe.com, pappers…) : le SIREN est dans l'adresse
REGISTRE_URL_RE = re.compile(r"(?:societe\.com|pappers\.fr|annuaire-entreprises\.data\.gouv\.fr|infogreffe\.fr|"
                             r"verif\.com|manageo\.fr|societe\.ninja|entreprises\.lefigaro\.fr)/\S*?(\d{9})(?:\d{5})?\b",
                             re.I)
# « à quoi sert ce module », « le module OSINT », « c'est quoi l'OSINT »
EXPLICATION_OSINT_RE = re.compile(r"\bosint\b|(?:a|à) quoi sert (?:ce|se|le|ton) module|c'?est quoi (?:ce|se|le) module",
                                  re.I)
# « va chercher à la source sur le web », « cherche sur internet » : reprendre le dernier sujet
SOURCE_RE = re.compile(r"\b(cherch\w*|fouill\w*|recherch\w*|trouv\w*)\b.{0,40}\b(source|web|internet|en ligne|net)\b"
                       r"|\b(a|à) la source\b", re.I)
DERNIER_SUJET_CLE = "conversation_dernier_sujet"
# Questions sur une action du Cortex : « c'est quoi l'action en attente », « pourquoi tu leur envoies »,
# « qui a envoyé », « Envoyé à Sermeta (…) », « donne-moi des infos sur chaque action »
EXPLICATION_ACTION_RE = re.compile(
    r"(pourquoi|c'?est quoi|qu'?est[- ]ce que|explique|qui a envoy|d[ée]tail|infos?|consiste|ce que j'ai valid|"
    r"d'o[uù] sort|depuis quel)\b.{0,60}\b(action|email|e-mail|mail|envoi|envoy|relance|valid|identifiant|leur)"
    r"|\benvoy[ée] [àa] \S|\baction en attente\b|\bce que j'ai valid", re.I)
ID_ACTION_RE = re.compile(r"\b([0-9a-f]{8})(?:-[0-9a-f]{4}){0,4}\b", re.I)
FRUSTRATION_RE = re.compile(r"\b(tu ne comprends? rien|tu comprends rien|t'es nul|tu es nul|"
                            r"c'est nul|ca marche pas|ça marche pas|tu sers a rien|tu sers à rien)\b", re.I)
DERNIER_DOMAINE_CLE = "conversation_dernier_domaine"
DERNIER_DOMAINE_S = 2 * 3600  # « scan le site » reprend le domaine cité dans les 2 dernières heures


def extraire_domaine(texte):
    m = DOMAINE_RE.search(texte or "")
    return m.group(1).lower().rstrip(".") if m else None


def niveau1(message_text):
    """Classement sans modèle. Renvoie un dict ou None (=> niveau 2)."""
    texte = (message_text or "").strip()
    plat = _plat(texte)
    if texte.startswith("/"):
        cmd = texte.split()[0].split("@")[0].lower()
        return {"intent": "command", "command": COMMANDS.get(cmd, cmd)}
    if AGENT_RE.search(texte):
        return {"intent": "identity"}
    mots = re.findall(r"[\w'-]+", plat)
    if not mots:
        return {"intent": "unknown"}
    # question sur une action (envoi, relance, validation, identifiant) : réponse tirée du journal
    if EXPLICATION_ACTION_RE.search(texte):
        ident = ID_ACTION_RE.search(texte)
        return {"intent": "explication_action", **({"action_id": ident.group(1).lower()}
                                                    if ident and re.search(r"[a-f]", ident.group(1), re.I) else {})}
    # URL d'annuaire (societe.com…) : fiche officielle par le SIREN de l'adresse, jamais l'audit de l'annuaire
    registre = REGISTRE_URL_RE.search(texte)
    if registre:
        return {"intent": "company_lookup", "siren": registre.group(1)}
    # fiche d'entreprise collée (societe.com, annuaire…) : le SIREN suffit, le reste du texte est ignoré
    siren = SIREN_RE.search(texte)
    if siren and (len(mots) > 12 or not extraire_domaine(texte)):
        return {"intent": "company_lookup", "siren": "".join(siren.groups())}
    # domaine ou URL dans un message court : audit du site, sans exiger secteur ni ville
    domaine = extraire_domaine(texte)
    if domaine and len(mots) <= 15:
        return {"intent": "site_audit", "domain": domaine}
    if SUITE_SITE_RE.search(texte) and len(mots) <= 12:
        return {"intent": "site_audit"}  # domaine repris de la conversation par le handler
    if EXPLICATION_OSINT_RE.search(texte) and len(mots) <= 15:
        return {"intent": "explain_osint"}
    if SOURCE_RE.search(texte) and len(mots) <= 20:
        return {"intent": "follow_up_source"}  # dernier sujet (site ou entreprise) repris par le handler
    if FRUSTRATION_RE.search(texte):
        return {"intent": "frustration"}
    # salutation seule (« Bonjour », « Salut Cortex ! ») : on répond par l'état réel
    if mots[0] in GREETINGS and len(mots) <= 3:
        return {"intent": "status"}
    # demande d'état courte (« état ? », « quoi de neuf », « bilan ») ; une phrase longue va au niveau 2
    if len(mots) <= 6 and any(re.search(r"(^|\W)" + re.escape(_plat(k)) + r"($|\W)", plat)
                              for k in STATUS_KEYWORDS):
        return {"intent": "status"}
    return None


def niveau2(cx_module, store, message_text):
    """Classement par le modèle léger. None si aucun modèle n'a répondu."""
    if not cx_module.llm_configured():
        return None
    prompt = INTENT_CLASSIFICATION_PROMPT.format(message=message_text[:1000].replace('"', "'"))
    res = cx_module.llm_chat("Tu réponds uniquement par un objet JSON.", prompt, store,
                             json_mode=True, max_tokens=300, prefer=CLASSIFIER_MODEL)
    if not isinstance(res, dict):
        return None
    intent = str(res.get("intent", "")).strip().lower()
    out = {"intent": intent if intent in INTENTS else "unknown"}
    for champ in ("sector", "company_name", "location"):
        if not _vide(res.get(champ)):
            out[champ] = str(res[champ]).strip()[:80]
    return out


def router_intent(message_text, cx_module=None, store=None):
    """Niveau 1 puis, si besoin, niveau 2. Renvoie toujours un dict avec « intent »."""
    r = niveau1(message_text)
    if r is not None:
        r["niveau"] = 1
        return r
    r = niveau2(cx_module, store, message_text) if cx_module is not None else None
    if r is None:  # aucun modèle disponible : on ne devine pas (I1), la conversation prendra le relais
        return {"intent": "general_question", "niveau": 2, "classifieur": "indisponible"}
    r["niveau"] = 2
    return r


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
def osint_installe(cx_module):
    return (Path(cx_module.BASE_DIR) / "osint_tools.py").exists()


def handle_status(cx_module, cx):
    """État réel lu dans cortex.db : jamais un message figé."""
    db = cx.s.db
    lignes = [cx.status_text()]
    try:
        dernier = db.execute("SELECT MAX(date) FROM audits").fetchone()[0]
        nb = db.execute("SELECT COUNT(*) FROM audits").fetchone()[0]
        lignes.append(f"Audits enregistrés : {nb}" + (
            f" · dernier : {cx_module.paris(cx_module.parse_iso(dernier))}" if dernier else ""))
    except Exception:
        pass
    try:
        nb_e = db.execute("SELECT COUNT(*) FROM entreprises").fetchone()[0]
        lignes.append(f"Entreprises dans l'annuaire : {nb_e}")
    except Exception:
        pass
    lignes.append("Module OSINT : " + ("installé" if osint_installe(cx_module)
                                        else "pas encore en service (attend ton feu vert)"))
    return "\n".join(lignes)


def _filtre_secteur(secteur):
    """Clause SQL et paramètres pour retrouver un secteur dans entreprises."""
    s = _singulier(secteur)
    clauses, params = ["lower(secteur_memoire) LIKE ?", "lower(denomination) LIKE ?"], [f"%{s}%", f"%{s}%"]
    for metier, prefixes in METIERS_NAF.items():
        if metier == s or metier in s or s in metier and len(s) >= 5:
            for p in prefixes:
                clauses.append("naf LIKE ?")
                params.append(p + "%")
    return "(" + " OR ".join(clauses) + ")", params


def donnees_secteur(db, secteur, lieu=None):
    """Compte réel des entreprises et candidats connus pour ce secteur (et ce lieu)."""
    where, params = _filtre_secteur(secteur)
    if lieu:
        where += " AND (lower(commune) LIKE ? OR departement LIKE ?)"
        params += [f"%{_plat(lieu)}%", f"%{_plat(lieu)}%"]
    q = f"SELECT COUNT(*), SUM(email_contact IS NOT NULL AND email_contact<>''), " \
        f"SUM(statut='a_contacter') FROM entreprises WHERE {where}"
    total, emails, a_contacter = db.execute(q, params).fetchone()
    villes = db.execute(f"SELECT commune, COUNT(*) n FROM entreprises WHERE {where} "
                        f"GROUP BY commune ORDER BY n DESC LIMIT 3", params).fetchall()
    s = _singulier(secteur)
    cand = db.execute("SELECT COUNT(*) FROM candidates WHERE lower(secteur) LIKE ? OR lower(nom) LIKE ?",
                      (f"%{s}%", f"%{s}%")).fetchone()[0]
    return {"total": total or 0, "emails": emails or 0, "a_contacter": a_contacter or 0,
            "villes": [(v[0], v[1]) for v in villes if v[0]], "candidats": cand or 0}


def handle_business_query(cx_module, cx, intent_data):
    """Secteur, audit ou OSINT : faits tirés de la base, puis proposition à confirmer.
    Rien n'est lancé ici (I3, I8)."""
    import html
    intent = intent_data["intent"]
    secteur = intent_data.get("sector")
    entreprise = intent_data.get("company_name")
    lieu = intent_data.get("location")
    # un domaine cité comme « entreprise », ou une demande d'audit sans cible après un domaine : audit du site
    dom = extraire_domaine(entreprise or "")
    if dom or (not secteur and not entreprise and dernier_domaine(cx_module, cx.s)):
        return handle_site_audit(cx_module, cx, {"domain": dom} if dom else {})
    if entreprise:
        memoriser_sujet(cx_module, cx.s, "nom", entreprise)
    osint = osint_installe(cx_module)
    parties = []
    if secteur:
        d = donnees_secteur(cx.s.db, secteur, lieu)
        zone = f" à {lieu}" if lieu else ""
        if d["total"] or d["candidats"]:
            villes = ", ".join(f"{v.title()} ({n})" for v, n in d["villes"])
            parties.append(f"{secteur.capitalize()}{zone} : {d['total']} entreprise(s) dans mon annuaire"
                           + (f", dont {d['emails']} avec email public et {d['a_contacter']} à contacter" if d["total"] else "")
                           + (f" ; principales communes : {villes}" if villes else "")
                           + (f" ; {d['candidats']} candidat(s) de prospection" if d["candidats"] else "") + ".")
        else:
            parties.append(f"Je n'ai encore aucune donnée sur les {secteur}{zone} dans ma base.")
    if entreprise:
        parties.append(f"Entreprise citée : {entreprise}" + (f" ({lieu})" if lieu and not secteur else "")
                       + ". Je n'ai pas encore d'audit enregistré à ce nom.")
    if not secteur and not entreprise:
        parties.append("Je n'ai pas identifié de secteur ni d'entreprise précis dans ta demande.")
        return html.escape(" ".join(parties) + " Précise le secteur ou le nom de l'entreprise, et la ville.", quote=False)

    cible = entreprise or f"les {secteur}"
    zone = lieu or "Nouvelle-Aquitaine"
    action = "un audit" if intent == "audit_query" and entreprise else "une analyse OSINT"
    if not osint:
        parties.append("Le module OSINT n'est pas encore en service : il attend ton « oui, mets en service ».")
    parties.append(f"Veux-tu que je prépare {action} sur {cible} dans la zone {zone} ? (oui/non)")
    EtatConversation(cx_module, cx.s).passer(
        EtatConversation.ATTENTE_CONFIRMATION, motif="analyse_proposee",
        donnees={"intent": intent, "action": action, "sector": secteur, "company_name": entreprise,
                 "location": zone})
    return html.escape(" ".join(parties), quote=False)


# ---------------------------------------------------------------------------
# Machine à états de la conversation
# ---------------------------------------------------------------------------
class EtatConversation:
    """État de la conversation Telegram, gardé dans kv (clé conversation_etat).

    LIBRE                --(proposition d'analyse)-->  ATTENTE_CONFIRMATION
    ATTENTE_CONFIRMATION --(oui / non)-------------->  LIBRE  (le « oui » crée une proposition R2)
    ATTENTE_CONFIRMATION --(autre message)---------->  LIBRE  (proposition abandonnée, message traité)
    ATTENTE_CONFIRMATION --(10 min sans réponse)---->  LIBRE  (expirée)

    Toute autre transition est refusée. Chaque transition est journalisée (INTERFACE, I7).
    Aucun état n'exécute d'action : le plus loin qu'on aille est une proposition notée.
    """
    LIBRE = "libre"
    ATTENTE_CONFIRMATION = "attente_confirmation"
    CLE = "conversation_etat"
    TRANSITIONS = {LIBRE: {ATTENTE_CONFIRMATION, LIBRE}, ATTENTE_CONFIRMATION: {LIBRE, ATTENTE_CONFIRMATION}}
    DUREE_S = {ATTENTE_CONFIRMATION: CONFIRMATION_S}

    def __init__(self, cx_module, store):
        self.m, self.s = cx_module, store

    def lire(self):
        """(état, données). Un état expiré redevient LIBRE (transition journalisée)."""
        try:
            e = json.loads(self.s.get(self.CLE) or "{}")
        except ValueError:
            e = {}
        etat = e.get("etat", self.LIBRE)
        if etat not in self.TRANSITIONS:
            etat = self.LIBRE
        duree = self.DUREE_S.get(etat)
        if duree and e.get("ts"):
            try:
                if (self.m.now() - self.m.parse_iso(e["ts"])).total_seconds() > duree:
                    self.passer(self.LIBRE, motif="expiree")
                    return self.LIBRE, {}
            except (ValueError, TypeError):
                pass
        return etat, e.get("donnees") or {}

    def passer(self, nouvel, donnees=None, motif=""):
        try:
            ancien = json.loads(self.s.get(self.CLE) or "{}").get("etat", self.LIBRE)
        except ValueError:
            ancien = self.LIBRE
        if ancien not in self.TRANSITIONS:
            ancien = self.LIBRE
        if nouvel not in self.TRANSITIONS[ancien]:
            self.s.log("INTERFACE", "etat_transition_refusee", details={"de": ancien, "vers": nouvel})
            return False
        self.s.set(self.CLE, json.dumps({"etat": nouvel, "ts": self.m.iso(self.m.now()),
                                         "donnees": donnees or {}}, ensure_ascii=False))
        self.s.log("INTERFACE", "etat_conversation", details={"de": ancien, "vers": nouvel, "motif": motif})
        return True


def confirmation_en_attente(cx_module, store):
    etat, donnees = EtatConversation(cx_module, store).lire()
    return donnees if etat == EtatConversation.ATTENTE_CONFIRMATION else None


def traiter_confirmation(cx_module, cx, text):
    """« oui » / « non » à une proposition d'analyse. Le « oui » crée une proposition notée
    R2, à valider : il ne lance rien. Renvoie la réponse, ou None si ce n'est pas une confirmation
    (le message est alors traité normalement et la proposition abandonnée)."""
    machine = EtatConversation(cx_module, cx.s)
    p = confirmation_en_attente(cx_module, cx.s)
    if not p:
        return None
    reponse = _plat(text).strip(" .!?")
    if reponse not in ("oui", "non", "ok", "vas-y", "non merci", "annule"):
        machine.passer(EtatConversation.LIBRE, motif="abandonnee_autre_message")
        return None
    machine.passer(EtatConversation.LIBRE, motif="confirmee" if reponse in ("oui", "ok", "vas-y") else "refusee")
    if reponse in ("non", "non merci", "annule"):
        cx.s.log("INTERFACE", "proposition_analyse_refusee", details={"intent": p.get("intent")})
        return "❌ Noté, rien ne sera fait."
    db = cx.s.db
    db.execute("CREATE TABLE IF NOT EXISTS missions_demandees (id INTEGER PRIMARY KEY "
               "AUTOINCREMENT, ts TEXT, texte TEXT, statut TEXT DEFAULT 'notee')")
    libelle = (f"{p['action']} · cible : {p.get('company_name') or p.get('sector')} · "
               f"zone : {p.get('location')} · risque R2 (validation JOSY requise)")
    cur = db.execute("INSERT INTO missions_demandees(ts, texte, statut) VALUES(?, ?, 'proposee_r2')",
                     (cx_module.iso(cx_module.now()), libelle[:1000]))
    db.commit()
    cx.s.log("INTERFACE", "proposition_analyse_creee",
             details={"mission_id": cur.lastrowid, "risque": "R2", "intent": p.get("intent"),
                      "secteur": p.get("sector"), "entreprise": p.get("company_name"),
                      "zone": p.get("location"), "executee": False})
    import html
    return html.escape(f"📌 Proposition n°{cur.lastrowid} enregistrée (R2). Rien n'est lancé : "
                       "elle reste soumise à ta validation et au contrôle judiciaire"
                       + ("" if osint_installe(cx_module) else ", et le module OSINT attend ta mise en service")
                       + ".", quote=False)


def reponse_identite():
    return ("Je suis le Cortex, un agent automatisé (intelligence artificielle) de JOSY EI. "
            "Je ne suis pas un humain.")


# ---------------------------------------------------------------------------
# Audit d'un site et fiche d'entreprise (OSINT autorisé, lecture publique seulement)
# ---------------------------------------------------------------------------
def memoriser_domaine(cx_module, store, domaine):
    store.set(DERNIER_DOMAINE_CLE, json.dumps({"domaine": domaine, "ts": cx_module.iso(cx_module.now())}))
    memoriser_sujet(cx_module, store, "domaine", domaine)


def memoriser_sujet(cx_module, store, sorte, valeur):
    """Dernier sujet de la conversation (domaine, siren ou nom d'entreprise), repris par « cherche à la source »."""
    store.set(DERNIER_SUJET_CLE, json.dumps({"sorte": sorte, "valeur": valeur, "ts": cx_module.iso(cx_module.now())},
                                            ensure_ascii=False))


def dernier_sujet(cx_module, store):
    try:
        d = json.loads(store.get(DERNIER_SUJET_CLE) or "{}")
        if d.get("valeur") and (cx_module.now() - cx_module.parse_iso(d["ts"])).total_seconds() <= DERNIER_DOMAINE_S:
            return d["sorte"], d["valeur"]
    except (ValueError, TypeError, KeyError):
        pass
    return None, None


def handle_follow_up_source(cx_module, cx, analyseurs=None):
    """« Va chercher à la source » : lecture publique du dernier sujet, sans redemander secteur ni ville."""
    sorte, valeur = dernier_sujet(cx_module, cx.s)
    if sorte == "domaine":
        return handle_site_audit(cx_module, cx, {"domain": valeur}, analyseurs)
    if sorte == "siren":
        return handle_company_lookup(cx_module, cx, {"siren": valeur}, analyseurs)
    if sorte == "nom":
        return handle_company_lookup(cx_module, cx, {"siren": valeur, "par_nom": True}, analyseurs)
    return ("Sur quoi veux-tu que je cherche ? Envoie l'adresse du site (ex. exemple.fr), le SIREN ou le lien "
            "de la fiche (societe.com, pappers…), et je lis la source publique directement.")


def explication_osint(cx_module):
    etat = ("installé dans la version de test, en service après ton « oui, mets en service »"
            if osint_installe(cx_module) else "pas encore installé dans le Cortex en service")
    return ("Le module OSINT (renseignement en sources ouvertes) lit seulement des informations publiques sur "
            "une entreprise : sa fiche dans l'annuaire officiel (SIREN, activité, adresse du siège, dirigeants "
            "déclarés), les technologies visibles de son site, ses emails génériques (contact@, info@…) en "
            "respectant robots.txt, et les réseaux où sa marque existe. Il sert à trouver un problème vérifié "
            "(ex. pas de HTTPS, pas de mentions légales) sur lequel fonder l'email d'audit gratuit. Il ne fait "
            "aucun scan de failles, ne garde aucune adresse nominative, ne contacte personne, et les données "
            f"brutes sont effacées après 90 jours. État : {etat}. Pour l'essayer : envoie l'adresse d'un site.")


def dernier_domaine(cx_module, store):
    try:
        d = json.loads(store.get(DERNIER_DOMAINE_CLE) or "{}")
        if d.get("domaine") and (cx_module.now() - cx_module.parse_iso(d["ts"])).total_seconds() <= DERNIER_DOMAINE_S:
            return d["domaine"]
    except (ValueError, TypeError, KeyError):
        pass
    return None


def _analyseurs_reels():
    import audit
    import osint_tools
    return {"site": audit.analyse_site, "technologies": osint_tools.scan_technologies,
            "emails": osint_tools.scrape_website_emails, "legal": osint_tools.get_legal_data}


def handle_site_audit(cx_module, cx, intent_data, analyseurs=None):
    """Lecture publique du site : faits de la page d'accueil, technologies visibles, emails génériques
    (robots.txt respecté). Aucun scan de vulnérabilité (art. 323-1 du Code pénal), aucun envoi. R0."""
    import html
    domaine = intent_data.get("domain") or dernier_domaine(cx_module, cx.s)
    if not domaine:
        return ("Quel site veux-tu que j'analyse ? Envoie simplement son adresse, par exemple "
                "<code>exemple.fr</code>.")
    memoriser_domaine(cx_module, cx.s, domaine)
    a = analyseurs or _analyseurs_reels()
    url = f"https://{domaine}"
    cx.s.log("EXECUTIF", "audit_site_lance", details={"domaine": domaine, "risque": "R0"})
    try:
        f = a["site"](url) or {}
    except Exception as exc:  # noqa: BLE001
        f = {"joignable": False, "erreur": type(exc).__name__}
    if not f.get("joignable"):
        cx.s.log("EXECUTIF", "audit_site_injoignable", details={"domaine": domaine})
        return html.escape(f"{domaine} ne répond pas (ni en HTTPS ni en HTTP). Vérifie l'adresse ou réessaie plus tard.",
                           quote=False)
    oui = lambda v: "oui" if v else "non"  # noqa: E731
    lignes = [f"🔎 Analyse de {domaine} (lecture publique, {cx_module.paris(cx_module.now())})",
              f"Titre : {f.get('titre') or '—'}",
              f"HTTPS : {oui(f.get('https'))} · temps de réponse : {f.get('temps_reponse_s', '?')} s"
              f" · adapté au mobile : {oui(f.get('mobile'))}",
              f"Meta description : {oui(f.get('meta_description'))} · page contact : {oui(f.get('page_contact'))}"
              f" · formulaire : {oui(f.get('formulaire'))}",
              f"Mentions légales : {oui(f.get('mentions_legales'))} · confidentialité/RGPD : {oui(f.get('confidentialite'))}"
              f" · carte Google : {oui(f.get('carte_google'))}"]
    if f.get("annee_copyright"):
        lignes.append(f"Année du copyright : {f['annee_copyright']}")
    try:
        t = a["technologies"](url) or {}
    except Exception as exc:  # noqa: BLE001
        t = {"status": "erreur", "detail": type(exc).__name__}
    if t.get("status") == "ok":
        noms = ", ".join(x["nom"] for x in t.get("technologies", [])[:8]) or "aucune détectée"
        lignes.append(f"Technologies : {noms}")
    else:
        lignes.append("Technologies : " + ("WordPress (repéré dans le code)" if f.get("wordpress") else
                                           "non analysées") + f" ({t.get('detail', 'module absent')})")
    try:
        e = a["emails"](url) or {}
    except Exception as exc:  # noqa: BLE001
        e = {"status": "erreur", "detail": type(exc).__name__}
    if e.get("status") == "robots_txt_interdit":
        lignes.append("Emails : non lus, robots.txt l'interdit.")
    elif e.get("status") == "ok":
        lignes.append("Emails génériques publiés : " + (", ".join(e.get("emails", [])) or "aucun")
                      + f" ({e.get('pages_lues', 0)} page(s) lue(s), robots.txt respecté)")
    else:
        lignes.append(f"Emails : non lus ({e.get('detail', 'erreur')})")
    manques = [lib for cle, lib in (("https", "pas de HTTPS"), ("mobile", "pas adapté au mobile"),
                                    ("meta_description", "pas de meta description"),
                                    ("mentions_legales", "mentions légales absentes"),
                                    ("page_contact", "pas de page contact")) if not f.get(cle)]
    lignes.append("Points à corriger : " + (", ".join(manques) if manques else "aucun sur ces critères") + ".")
    lignes.append("Aucun scan de sécurité n'est fait sans l'accord écrit du propriétaire du site.")
    cx.s.log("EXECUTIF", "audit_site_termine", details={"domaine": domaine, "manques": manques,
                                                        "technologies": t.get("status"), "emails": e.get("status")})
    return html.escape("\n".join(lignes), quote=False)[:4000]


def handle_company_lookup(cx_module, cx, intent_data, analyseurs=None):
    """Fiche de l'annuaire officiel (recherche-entreprises.api.gouv.fr) à partir du SIREN trouvé."""
    import html
    siren = intent_data["siren"]
    memoriser_sujet(cx_module, cx.s, "nom" if intent_data.get("par_nom") else "siren", siren)
    a = analyseurs or _analyseurs_reels()
    try:
        d = a["legal"](siren) or {}
    except Exception as exc:  # noqa: BLE001
        d = {"status": "erreur", "detail": type(exc).__name__}
    cx.s.log("EXECUTIF", "fiche_entreprise_lue", details={"siren": siren, "statut": d.get("status")})
    if d.get("status") != "ok":
        return html.escape(f"{'Entreprise' if intent_data.get('par_nom') else 'SIREN'} {siren} : l'annuaire officiel ne répond pas "
                           f"({d.get('detail', d.get('status', 'erreur'))}). Réessaie dans quelques minutes.", quote=False)
    lignes = [f"🏢 {d.get('raison_sociale')} · SIREN {d.get('siren')}",
              f"Activité : {d.get('activite') or '—'} · créée le {d.get('date_creation') or '—'}",
              f"Siège : {d.get('adresse') or '—'}",
              f"Source : {d.get('source')}"]
    lignes.append("Envoie l'adresse de son site (ex. exemple.fr) et j'en fais l'analyse.")
    return html.escape("\n".join(lignes), quote=False)


def reponse_frustration(cx_module, cx):
    dom = dernier_domaine(cx_module, cx.s)
    return ("Désolé, je n'ai pas su répondre. Ce que je sais faire tout de suite : analyser un site "
            "(envoie son adresse, ex. exemple.fr), lire la fiche officielle d'une entreprise (envoie son SIREN), "
            "chercher dans mon annuaire par secteur et ville (ex. « garages à Poitiers »), ou donner mon /etat."
            + (f" Je peux aussi relancer l'analyse de {dom} : écris « scan le site »." if dom else ""))


# ---------------------------------------------------------------------------
# Explication d'une action (lecture du journal, aucune déduction du modèle)
# ---------------------------------------------------------------------------
LIBELLES_STATUT = {"en_attente_humain": "en attente de ta décision", "valide_en_file": "validée, mise en file d'envoi",
                   "refuse": "refusée", "refuse_timeout": "refusée automatiquement (délai dépassé)",
                   "execute_remis": "validée, contenu remis à toi", "valide": "validée"}
LIBELLES_TYPE = {"cold_email": "premier email de prospection", "premier_contact": "premier contact",
                 "relance": "relance par email", "reponse": "réponse à un prospect", "google_post": "publication Google",
                 "amelioration_regle": "amélioration d'une règle", "diagnostic": "diagnostic"}


def decrire_action(cx_module, db, p):
    """Fiche factuelle d'une proposition : quoi, pour qui, quand, verdict du judiciaire, décision, envois."""
    try:
        payload = json.loads(p["payload"] or "{}")
    except ValueError:
        payload = {}
    h = lambda ts: cx_module.paris(cx_module.parse_iso(ts)) if ts else "—"  # noqa: E731
    items = payload.get("items") or ([{"company": (payload.get("target") or {}).get("company"),
                                       "to": (payload.get("target") or {}).get("email")}]
                                     if (payload.get("target") or {}).get("company") else [])
    cibles = ", ".join(f"{i.get('company')}" + (f" ({i.get('to')})" if i.get("to") else "") for i in items[:5]) or "—"
    verdict = db.execute("SELECT event, details FROM journal WHERE action_id=? AND power='JUDICIAIRE' "
                         "AND event LIKE 'proposition_%' ORDER BY id LIMIT 1", (p["action_id"],)).fetchone()
    if verdict:
        try:
            notes = ", ".join(json.loads(verdict["details"] or "{}").get("notes") or [])
        except ValueError:
            notes = ""
        juge = ("admise" if verdict["event"] == "proposition_admise" else "rejetée") + (f" ({notes})" if notes else "")
    else:
        juge = "aucun verdict enregistré (proposition générée par le code, sans passage par le contrôle des missions)"
    envois = db.execute("SELECT company, to_email, sent_at, simule FROM envois WHERE action_id=? ORDER BY id",
                        (p["action_id"],)).fetchall()
    lignes = [f"{p['action_id'][:8]} · {LIBELLES_TYPE.get(p['action_type'], p['action_type'])}"
              f" · risque {p['risk_level']} · mission {p['mission']}",
              f"Pour : {cibles}",
              f"Proposée le {h(p['created_at'])} · contrôle judiciaire : {juge}",
              f"Statut : {LIBELLES_STATUT.get(p['status'], p['status'])}"
              + (f" · décision le {h(p['decided_at'])} par {p['decision_source']}" if p["decided_at"] else "")]
    if payload.get("justification"):
        lignes.append("Raison : " + str(payload["justification"])[:200])
    if envois:
        lignes.append("Envois : " + "; ".join(
            f"{e['company']} ({e['to_email']}) le {h(e['sent_at'])}" + (" [simulé]" if e["simule"] else " [réel, SMTP]")
            for e in envois))
    elif p["status"] == "valide_en_file":
        lignes.append("Envois : en file, pas encore partis.")
    return "\n".join(lignes)


def handle_explication_action(cx_module, cx, intent_data, texte=""):
    import html
    db = cx.s.db
    if intent_data.get("action_id"):
        rows = db.execute("SELECT * FROM proposals WHERE action_id LIKE ?", (intent_data["action_id"] + "%",)).fetchall()
        if not rows:
            return f"Aucune action ne porte l'identifiant {html.escape(intent_data['action_id'])}."
    else:
        # entreprise citée (« Envoyé à Sermeta… ») : ses actions ; sinon en attente + 3 dernières décisions
        cites = [r[0] for r in db.execute("SELECT DISTINCT action_id FROM envois").fetchall()
                 if any(_plat(c or "")[:12] in _plat(texte) for (c,) in
                        db.execute("SELECT company FROM envois WHERE action_id=?", (r[0],)).fetchall())]
        rows = ([db.execute("SELECT * FROM proposals WHERE action_id=?", (a,)).fetchone() for a in cites]
                if cites else
                db.execute("SELECT * FROM proposals WHERE status=? ORDER BY created_at", (cx_module.PENDING,)).fetchall()
                + db.execute("SELECT * FROM proposals WHERE status!=? AND decided_at IS NOT NULL "
                             "ORDER BY decided_at DESC LIMIT 3", (cx_module.PENDING,)).fetchall())
        rows = [r for r in rows if r]
        if not rows:
            return "Aucune action enregistrée pour l'instant."
    cx.s.log("INTERFACE", "explication_action", details={"actions": [r["action_id"][:8] for r in rows]})
    entete = "📋 Ce que dit le journal :" if len(rows) > 1 else "📋 Fiche de l'action :"
    return html.escape(entete + "\n\n" + "\n\n".join(decrire_action(cx_module, db, r) for r in rows),
                       quote=False)[:4000]


def message_repli(cx_module, cx, raison):
    """Réponse quand aucun modèle ne peut répondre : la raison, l'état réel et ce qui marche sans
    modèle. Jamais de silence, jamais de réponse inventée (I1)."""
    try:
        attente = cx.s.db.execute("SELECT COUNT(*) FROM proposals WHERE status=?",
                                  (cx_module.PENDING,)).fetchone()[0]
        etat = f"{attente} action(s) attendent ta décision."
    except Exception:
        etat = "état indisponible."
    import html
    return html.escape(f"Je ne peux pas formuler de réponse maintenant : {raison}. {etat} "
                       "Sans modèle, ces commandes marchent : /etat, /attente, /valider ID, /refuser ID, "
                       "/stop. Renvoie ta question dans quelques minutes.", quote=False)


def reponse_inconnue():
    return ("Je n'ai pas bien compris votre demande. Tapez /etat pour voir mon état, ou posez-moi "
            "une question sur un secteur d'activité ou un audit d'entreprise.")
