#!/usr/bin/env python3
"""La vie du fondateur — priorité n°1 du Cortex (I14).

Trois responsabilités, aucune ne touche à l'extérieur :

  1. un **profil de vie** construit par les réponses de JOSY, une question à la
     fois, jamais deviné (clé `profil_vie` dans cortex.db, miroir lisible dans
     vie-fondateur.md) ;
  2. un **plan de journée** paramétré, envoyé le matin, réajusté quand la
     journée change, constaté le soir sans reproche ;
  3. les commandes Telegram de la journée : /jour /ajuste /fait /reporte
     /profil /vie /bilan.

Convention d'appel, comme vente.py : le premier argument est le module `cortex`,
le second l'instance `Cortex` (`cx.s` = base, `cx.tg` = Telegram).

**Module autonome** : il n'a besoin d'aucun autre fichier du projet pour
fonctionner. Les classes `Environnement`, `StoreLocal`, `CanalTelegram` /
`CanalConsole` et `ModeleLLM` (section « RUNTIME AUTONOME ») fournissent le même
hôte et le même canal que cortex.py, avec la seule bibliothèque standard :

    python -m fondateur --etat          # ce que le module sait de lui-même
    python -m fondateur --profil        # le profil de vie connu
    python -m fondateur --plan          # le plan du jour (exige un modèle)
    python -m fondateur --boucle        # tourne seul, un cycle toutes les 5 min

Le plan et les questions sont R0 (journalisés, envoyés, sans validation à
donner). Les données de vie ne sortent **jamais** dans un contenu destiné à
l'extérieur (I4 et I14) ; elles restent dans la base et dans vie-fondateur.md.

Le module ne décide rien seul : il rend la vie de JOSY visible au modèle, et il
refuse d'envoyer un plan qu'il ne comprend pas (I6 : rien d'inventé, rien de
malformé, rien qui viole sa capacité ou ses plages de silence).
"""

import argparse
import hashlib
import html
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# --------------------------------------------------------------------------
# Ce que le Cortex doit apprendre, et dans quel ordre il le demande
# --------------------------------------------------------------------------
# (clé, question, pourquoi elle change une décision du jour)
CHAMPS = [
    ("preferences.plan_heure", "À quelle heure veux-tu recevoir ton plan du jour ?",
     "pour l'envoyer au bon moment, pas au mien"),
    ("objectifs.30j", "Qu'est-ce qui doit absolument être fait dans les 30 jours ?",
     "sans objectif connu, je ne peux pas te donner de vraie priorité"),
    ("rythme.lever", "À quelle heure te lèves-tu en ce moment ?",
     "pour placer la première tâche après ton réveil réel"),
    ("rythme.coucher", "Et à quelle heure te couches-tu ?",
     "pour ne rien te proposer quand tu devrais dormir"),
    ("travail.heures", "Quelles sont tes vraies heures de travail, du lundi au vendredi ?",
     "pour ne pas remplir des heures qui n'existent pas"),
    ("travail.charge_max", "Combien d'heures de travail productif tiens-tu dans une journée sans te cramer ?",
     "pour plafonner la charge au lieu de la deviner"),
    ("rythme.pics", "Sur quels créneaux es-tu le plus efficace ?",
     "pour y mettre le travail difficile plutôt que l'administratif"),
    ("rythme.creux", "Et sur quels créneaux tu es à plat ?",
     "pour y mettre le léger, ou du repos"),
    ("off.jours", "Quels jours sont off pour toi, sans rien de professionnel ?",
     "pour ne rien te demander ces jours-là"),
    ("preferences.silence", "Quelles plages horaires veux-tu que je laisse totalement tranquilles ?",
     "pour ne jamais t'écrire pendant"),
    ("perso.contraintes", "Quelles contraintes reviennent chaque semaine (enfants, proches, rendez-vous fixes) ?",
     "pour les protéger et construire autour"),
    ("sante.etat", "Comment vont ton énergie et ton sommeil en ce moment ?",
     "pour alléger les jours difficiles au lieu de faire comme si"),
    ("perso.famille", "Quelle est ta situation familiale, en une phrase ?",
     "pour que je protège ces moments sans que tu aies à le redire"),
    ("travail.lieu", "Où travailles-tu le plus souvent (bureau, maison, déplacements) ?",
     "pour adapter les créneaux de travail profond"),
    ("argent.objectif", "De quel revenu mensuel as-tu besoin pour être tranquille ?",
     "pour te dire si ton offre suffit, au lieu de pousser au volume"),
    ("argent.seuil", "À partir de quelle trésorerie veux-tu que je tire l'alarme ?",
     "pour t'alerter avant que ce soit grave, pas après"),
    ("objectifs.90j", "Et à 90 jours, qu'est-ce qui compte le plus ?",
     "pour ne pas optimiser un mois contre le trimestre"),
    ("gouts.aime", "Qu'est-ce que tu aimes vraiment faire dans ton travail ?",
     "pour te mettre en avant ce que tu fais bien"),
    ("gouts.deteste", "Et qu'est-ce que tu repousses toujours ?",
     "pour le prendre en charge ou le découper"),
    ("preferences.messages", "Combien de messages par jour veux-tu de moi au maximum ?",
     "pour ne jamais te submerger"),
]

CHAMPS_DICT = {cle: (q, p) for cle, q, p in CHAMPS}

PROFIL_KEY = "profil_vie"
TYPES = {"perso", "deep", "admin", "business", "sante", "repos"}
TYPES_TRAVAIL = {"deep", "admin", "business"}
ENERGIES = {"haute", "moyenne", "basse"}
MAX_CRENEAUX = 7
MAX_CRENEAUX_PROFIL_VIDE = 4   # tant que l'objectif de JOSY est inconnu : court et honnête
DEFAUT_PLAN_HEURE = "07:30"
DEFAUT_SILENCE = "22:00-07:00"
DEFAUT_CAPACITE_H = 5.0
MAX_ESSAIS_PLAN = 3
CHECK_MIDI = (12, 30)
BILAN_SOIR = (20, 30)
AGE_QUESTION_H = 48
MAX_QUESTIONS_IGNOREES = 3

JOURS_FR = {"lundi": 0, "mardi": 1, "mercredi": 2, "jeudi": 3, "vendredi": 4,
            "samedi": 5, "dimanche": 6}
JOURS_NOMS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"]
HEURE_RE = re.compile(r"(\d{1,2})\s*[:hH]\s*(\d{2})|(\d{1,2})\s*(?:h|heures?)\b")
ORDRE_RE = re.compile(r"^\s*(fais|lance|envoie|publie|cr[ée]e|trouve|cherche|pr[ée]pare|r[ée]dige)\b",
                      re.IGNORECASE)
# Vie privée que le Cortex n'a pas le droit de supposer : si JOSY ne l'a pas dite, elle n'existe pas.
VIE_SENSIBLE_RE = re.compile(
    r"m[ée]dicaments?|ordonnances?|pharmacie|antid[ée]presseurs?|anxiolytiques?|psychologues?|"
    r"psychoth[ée]rapie|prise de sang|analyses? sanguines?|kin[ée]sith[ée]rapie|m[ée]decins?|"
    r"alcool|sevrage|garde des enfants|pension alimentaire", re.IGNORECASE)


# --------------------------------------------------------------------------
# Accès à l'instance Cortex (convention vente.py)
# --------------------------------------------------------------------------
def _store(cx):
    """La base : `cx.s` pour une instance Cortex, `cx` si on passe un Store."""
    return getattr(cx, "s", cx)


def _tg(cx):
    """L'objet Telegram, quel que soit le mode de passage."""
    retour = getattr(cx, "tg", None)
    if retour is None:
        retour = getattr(_store(cx), "tg", None)
    return retour


def _envoyer(tg, texte):
    if tg is not None:
        tg.send(texte)


# --------------------------------------------------------------------------
# Petits outils (tous tolérants : une donnée illisible n'arrête rien)
# --------------------------------------------------------------------------
def _minutes(texte):
    """« 9h30 », « 09:30 », « 7 h », « 8 heures » -> minutes depuis minuit."""
    if texte is None:
        return None
    m = HEURE_RE.search(str(texte))
    if not m:
        return None
    if m.group(1) is not None:
        h, mn = int(m.group(1)), int(m.group(2))
    else:
        h, mn = int(m.group(3)), 0
    return h * 60 + mn if h <= 23 and mn <= 59 else None


def _hhmm(mn):
    return f"{mn // 60:02d}:{mn % 60:02d}"


def _charge_minutes(texte, defaut=None):
    """« 6h », « 5 h 30 », « 300 min » -> minutes de travail productif par jour."""
    if not texte:
        return defaut
    t = str(texte).lower()
    m = re.search(r"(\d{1,2})\s*h\s*(\d{1,2})\b", t)          # 5 h 30
    if m and int(m.group(2)) < 60:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(heures?|h\b|min)", t)
    if not m:
        return defaut
    v = float(m.group(1).replace(",", "."))
    minutes = int(v * 60) if not m.group(2).startswith("min") else int(v)
    return minutes if 30 <= minutes <= 16 * 60 else defaut


def plages_silence(profil):
    """Plages à ne jamais occuper. Défaut prudent tant que JOSY n'a rien dit."""
    valeurs = [_minutes(m.group(0)) for m in HEURE_RE.finditer(str(profil.get("preferences.silence") or ""))]
    valeurs = [v for v in valeurs if v is not None]
    if len(valeurs) >= 2:
        return [(valeurs[0], valeurs[1])]
    return [(_minutes("22:00"), _minutes("07:00"))]


def jours_off(profil):
    t = str(profil.get("off.jours") or "").lower()
    return {i for nom, i in JOURS_FR.items() if nom in t}


def capacite_minutes(profil):
    return _charge_minutes(profil.get("travail.charge_max"), int(DEFAUT_CAPACITE_H * 60))


def heure_plan(profil):
    return _minutes(profil.get("preferences.plan_heure")) or _minutes(DEFAUT_PLAN_HEURE)


def dans_plage(mn, debut, fin):
    """Vrai si mn tombe dans [debut, fin), plage qui peut passer minuit."""
    if debut is None or fin is None:
        return False
    if debut <= fin:
        return debut <= mn < fin
    return mn >= debut or mn < fin


def dans_silence(profil, mn):
    return any(dans_plage(mn, a, b) for a, b in plages_silence(profil))


def plafond_messages(profil):
    """Nombre de messages par jour que JOSY accepte. Défaut : 4 (plan, recadrage, question, bilan)."""
    m = re.search(r"\b(\d{1,2})\b", str(profil.get("preferences.messages") or ""))
    if not m:
        return 4
    return max(1, min(20, int(m.group(1))))


def messages_du_jour(store, jour):
    """Messages déjà envoyés par le pôle « vie du fondateur » aujourd'hui (garde-fou souple)."""
    try:
        return store.db.execute(
            "SELECT COUNT(*) FROM journal WHERE power='FONDATEUR' AND ts>=? AND event IN "
            "('plan_journee','check_milieu_journee','bilan_journee','question_du_jour_envoyee',"
            "'journee_off')", (jour + "T00:00:00",)).fetchone()[0]
    except Exception:
        return 0


# --------------------------------------------------------------------------
# Profil de vie
# --------------------------------------------------------------------------
def profil(store):
    try:
        p = json.loads(store.get(PROFIL_KEY) or "{}")
        return p if isinstance(p, dict) else {}
    except ValueError:
        return {}


def sauver_profil(store, p):
    store.set(PROFIL_KEY, json.dumps(p, ensure_ascii=False, sort_keys=True))


def apprendre(c, store, texte, cle=None):
    """Enregistre une réponse de JOSY. Rien n'est perdu : tout va aussi dans `appris`."""
    texte = (texte or "").strip()
    if not texte:
        return None
    p = profil(store)
    appris = p.get("appris")
    if not isinstance(appris, list):
        appris = []
    appris.append({"date": c.now().astimezone(c.PARIS).date().isoformat(), "texte": texte[:500]})
    p["appris"] = appris[-60:]
    if cle and cle in CHAMPS_DICT:
        p[cle] = texte[:300]
    sauver_profil(store, p)
    store.log("FONDATEUR", "profil_vie_maj", details={"champ": cle or "libre", "longueur": len(texte)})
    ecrire_miroir(c, store, p)
    return cle


def question_en_attente(c, store, p=None):
    """La question posée il y a moins de 48 h et restée sans réponse, s'il y en a une."""
    p = p if p is not None else profil(store)
    limite = c.now().astimezone(c.PARIS).date() - timedelta(hours=AGE_QUESTION_H)
    for cle, _q, _pourquoi in CHAMPS:
        pose = store.get(f"question_posee.{cle}")
        if pose and not p.get(cle) and pose[:10] >= limite.isoformat():
            return cle
    return None


def question_du_jour(c, store, p=None):
    """La prochaine chose utile à apprendre. Une question trop ignorée passe au second plan."""
    p = p if p is not None else profil(store)
    aujourdhui = c.now().astimezone(c.PARIS).date()
    for cle, q, pourquoi in CHAMPS:
        if p.get(cle):
            continue
        pose = store.get(f"question_posee.{cle}")
        if pose:
            try:
                age = aujourdhui - date.fromisoformat(pose[:10])
            except ValueError:
                age = timedelta(0)
            if age.days >= 2:  # posée, jamais répondue : on ne harcèle pas
                rate = int(store.get(f"question_ignoree.{cle}", "0") or 0) + 1
                store.set(f"question_ignoree.{cle}", rate)
                store.set(f"question_posee.{cle}", "")
                if rate >= MAX_QUESTIONS_IGNOREES:
                    store.log("FONDATEUR", "question_abandonnee", details={"champ": cle})
                    continue
            else:
                continue  # laissée en attente : on attend sa réponse
        return {"champ": cle, "question": q, "pourquoi": pourquoi}
    return None


def poser_question(c, store, question):
    if not question:
        return
    store.set(f"question_posee.{question['champ']}", c.iso(c.now()))
    store.set("derniere_question", c.now().astimezone(c.PARIS).date().isoformat())
    store.log("FONDATEUR", "question_fondateur", details={"champ": question["champ"]})


def _question_a_poser(c, store, p):
    """Une seule question par jour, jamais deux fois, jamais pendant le silence."""
    if store.get("derniere_question") == c.now().astimezone(c.PARIS).date().isoformat():
        return None
    if question_en_attente(c, store, p):
        return None
    return question_du_jour(c, store, p)


# --------------------------------------------------------------------------
# Miroir lisible (vie-fondateur.md)
# --------------------------------------------------------------------------
SECTIONS = [("preferences.", "Préférences et rythme de travail"),
            ("rythme.", "Rythme biologique"),
            ("travail.", "Travail"),
            ("perso.", "Vie personnelle"),
            ("sante.", "Santé et énergie"),
            ("argent.", "Argent"),
            ("objectifs.", "Objectifs"),
            ("gouts.", "Ce qu'il aime, ce qu'il repousse"),
            ("off.", "Jours off")]


def ecrire_miroir(c, store, p=None):
    """Écrit vie-fondateur.md : le profil tel que JOSY peut le relire."""
    p = p if p is not None else profil(store)
    lignes = ["# Vie de JOSY — profil connu du Cortex", "",
              "> Fichier **généré** par le Cortex à partir des réponses de JOSY.",
              "> Il ne se modifie pas à la main : tout passe par Telegram",
              "> (`/vie ta réponse`, ou en répondant à la question du jour).",
              "> Ces données sont internes : elles ne sortent jamais dans un email,",
              "> une publication ou un devis (I4, I14).", ""]
    for prefixe, titre in SECTIONS:
        entrees = [(k, v) for k, v in sorted(p.items())
                   if k.startswith(prefixe) and isinstance(v, str)]
        lignes.append(f"## {titre}")
        lignes += [f"- **{k.split('.', 1)[-1]}** : {v}" for k, v in entrees] or ["- _(non renseigné)_"]
        lignes.append("")
    restant = [cle for cle, _q, _p in CHAMPS if not p.get(cle)]
    lignes += ["## Ce que le Cortex ne sait pas encore", "",
               ("- " + ", ".join(restant)) if restant else "- rien : profil complet", ""]
    if p.get("appris"):
        lignes += ["## Ce que JOSY a dit (brut, jamais perdu)", ""]
        lignes += [f"- {a.get('date', '')} : {a.get('texte', '')}"
                   for a in p["appris"] if isinstance(a, dict)]
        lignes.append("")
    try:
        (c.BASE_DIR / "vie-fondateur.md").write_text("\n".join(lignes), encoding="utf-8")
    except OSError as exc:
        store.log("EXECUTIF", "vie_miroir_echec", details={"erreur": c.safe_error(exc)})


# --------------------------------------------------------------------------
# Plan de la journée
# --------------------------------------------------------------------------
def _cle_plan(jour):
    return f"plan_{jour}"


def _veille(jour):
    try:
        return (date.fromisoformat(jour) - timedelta(days=1)).isoformat()
    except ValueError:
        return jour


def plan_du_jour(store, jour):
    try:
        p = json.loads(store.get(_cle_plan(jour)) or "null")
        return p if isinstance(p, dict) else None
    except ValueError:
        return None


def sauver_plan(store, jour, plan):
    store.set(_cle_plan(jour), json.dumps(plan, ensure_ascii=False))


def contexte_systeme(store, jour):
    """Ce que le Cortex fait lui-même aujourd'hui (lu dans la base, sans invention)."""
    q = store.db.execute
    info = {"en_attente_de_toi": 0, "propositions_du_jour": 0, "emails_envoyes": 0}
    try:
        info["en_attente_de_toi"] = q("SELECT COUNT(*) FROM proposals "
                                      "WHERE status='en_attente_humain'").fetchone()[0]
        info["propositions_du_jour"] = q("SELECT COUNT(*) FROM proposals WHERE created_at>=?",
                                         (jour + "T00:00:00+00:00",)).fetchone()[0]
        if q("SELECT name FROM sqlite_master WHERE type='table' AND name='envois'").fetchone():
            info["emails_envoyes"] = q("SELECT COUNT(*) FROM envois WHERE sent_at>=?",
                                       (jour + "T00:00:00+00:00",)).fetchone()[0]
    except Exception as exc:
        store.log("EXECUTIF", "fondateur_contexte_echec", details={"erreur": type(exc).__name__})
    return info


def _contexte(c, store, jour, ajustement=None):
    p = profil(store)
    d = c.now().astimezone(c.PARIS)
    hier = plan_du_jour(store, _veille(jour))
    cap = capacite_minutes(p)
    morceaux = [
        "MISSION FONDATEUR : paramètre la journée de JOSY, puis réponds UNIQUEMENT avec l'objet "
        "JSON décrit dans « La journée de JOSY » (mission M6_Fondateur). Aucun texte autour du JSON.",
        f"Date : {JOURS_NOMS[d.weekday()]} {d.day} {MOIS_FR[d.month - 1]} {d.year} ; "
        f"il est {d.strftime('%H:%M')} (heure de Paris).",
        "PROFIL DE VIE CONNU (réponses de JOSY ; ce qui n'y est pas n'est PAS supposé) :\n"
        + (json.dumps(p, ensure_ascii=False, indent=1) if p else
           "aucune donnée : reste prudent, demande ce qui manque, mets profil_incomplet = true"),
        f"Plages de silence à ne jamais occuper : {p.get('preferences.silence') or DEFAUT_SILENCE}. "
        f"Capacité maximale : {cap // 60} h {cap % 60:02d} de travail productif. "
        "3 à 7 créneaux. Une seule priorité absolue.",
        "COMPTEURS INTERNES DU CORTEX (contexte seulement) : "
        + json.dumps(contexte_systeme(store, jour), ensure_ascii=False)
        + ". Ce sont des compteurs de MON activité, pas des tâches de JOSY : ne les transforme "
          "JAMAIS en priorité, en créneau ni en justification. La priorité absolue doit venir d'un "
          "objectif que JOSY a énoncé, ou d'un engagement réel déjà pris envers un client.",
        "INTERDIT : n'écris aucune donnée de vie que JOSY n'a pas dite lui-même (santé, "
        "médicament, traitement, médecin, famille, argent). Aucun créneau de type « sante » tant "
        "qu'il n'a rien dit de sa santé. Aucun remplissage générique pour faire du volume "
        "(routine, pauses, « au cas où »).",
        ("Son profil est presque vide : fais un plan COURT (3 à 4 créneaux), uniquement sur ce qui "
         "est certain, et dis honnêtement que la priorité est provisoire en attendant son objectif. "
         "Si tu n'as rien de solide à mettre, mets moins de créneaux — pas de faux travail."
         if not (p.get("objectifs.30j") or p.get("objectifs.90j")) else
         "Appuie la priorité sur l'objectif qu'il a énoncé, pas sur autre chose."),
    ]
    if hier:
        faits = [cr.get("titre") for cr in hier.get("creneaux", []) if cr.get("statut") == "fait"]
        rates = [cr.get("titre") for cr in hier.get("creneaux", []) if cr.get("statut") != "fait"]
        morceaux.append("HIER — fait : " + (json.dumps(faits, ensure_ascii=False) if faits else "rien")
                        + " ; non fait : " + (json.dumps(rates, ensure_ascii=False) if rates else "rien")
                        + ". Si la veille a dérapé, allège aujourd'hui et ne reproche rien.")
    if ajustement:
        morceaux.append("JOSY VIENT DE DIRE, en pleine journée : « " + str(ajustement)[:500]
                        + " ». Reconstruis la journée à partir de maintenant et de cette réalité : "
                          "garde ce qui reste utile, enlève ce qui ne tient plus.")
    return "\n\n".join(morceaux)


def _nettoyer(plan, p):
    """Rend un plan utilisable. Renvoie (plan, notes). Rien n'est inventé ni ajouté."""
    notes = []
    if not isinstance(plan, dict):
        return None, ["plan non exploitable"]
    creneaux = []
    for brut in (plan.get("creneaux") or [])[:MAX_CRENEAUX]:
        if not isinstance(brut, dict):
            continue
        debut, fin = _minutes(brut.get("debut")), _minutes(brut.get("fin"))
        if debut is None or fin is None or fin <= debut:
            notes.append(f"créneau ignoré, horaires illisibles : {str(brut.get('titre'))[:40]}")
            continue
        creneaux.append({
            "debut": _hhmm(debut), "fin": _hhmm(fin),
            "type": brut.get("type") if brut.get("type") in TYPES else "business",
            "titre": str(brut.get("titre") or "")[:120],
            "details": str(brut.get("details") or "")[:400],
            "energie": brut.get("energie") if brut.get("energie") in ENERGIES else "moyenne",
            "obligatoire": bool(brut.get("obligatoire")),
            "statut": "prevu",
        })
    # I6 appliqué à la vie de JOSY : aucune donnée de santé ou de vie privée qu'il n'a pas dite.
    sante_connue = bool(p.get("sante.etat"))
    # Sans objectif énoncé par JOSY, il n'y a pas de vraie priorité et pas de quoi remplir une journée.
    objectifs_connus = bool(p.get("objectifs.30j") or p.get("objectifs.90j"))

    def invente(texte):
        return bool(VIE_SENSIBLE_RE.search(str(texte or ""))) and not sante_connue

    propres, inventees = [], []
    for cr in creneaux:
        if (cr["type"] == "sante" and not sante_connue) or invente(cr["titre"] + " " + cr["details"]):
            inventees.append(cr)  # jamais recopiées ensuite : rien de la donnée inventée ne ressort
            continue
        propres.append(cr)
    creneaux = propres
    if inventees:
        # On ne réécrit jamais la donnée inventée, même pour l'expliquer.
        notes.append(f"retiré {len(inventees)} créneau(x) que je n'avais pas le droit d'inventer "
                     "(santé ou vie privée que tu ne m'as pas confiée)")

    silences = plages_silence(p)
    gardes, ecartes = [], []
    for cr in creneaux:
        d, f = _minutes(cr["debut"]), _minutes(cr["fin"])
        if cr["type"] in ("repos", "sante") or cr["obligatoire"]:
            gardes.append(cr)
            continue
        if any(dans_plage(d, a, b) or dans_plage(f - 1, a, b) for a, b in silences):
            ecartes.append(cr["titre"])
            continue
        gardes.append(cr)
    if ecartes:
        notes.append("écarté de tes plages de silence : " + " ; ".join(ecartes[:3]))

    def charge_travail(liste):
        return sum(_minutes(cr["fin"]) - _minutes(cr["debut"])
                   for cr in liste if cr["type"] in TYPES_TRAVAIL)

    cap = capacite_minutes(p)
    retires = []
    while charge_travail(gardes) > cap:
        cible = next((cr for cr in reversed(gardes)
                      if cr["type"] in TYPES_TRAVAIL and not cr["obligatoire"]), None)
        if cible is None:
            break
        gardes.remove(cible)
        retires.append(cible["titre"])
    if retires:
        notes.append(f"retiré pour tenir dans ta capacité ({cap // 60} h {cap % 60:02d}) : "
                     + " ; ".join(retires[:3]))
    if charge_travail(gardes) > cap:
        obligatoires = [cr["titre"] for cr in gardes
                        if cr["type"] in TYPES_TRAVAIL and cr["obligatoire"]]
        notes.append(f"ce qui est obligatoire dépasse ta capacité ({cap // 60} h {cap % 60:02d}) : "
                     + " ; ".join(obligatoires[:2]) + " — dis-moi ce qu'on enlève")
    # Profil vide : le prompt suffit rarement à empêcher le remplissage générique, on l'impose ici.
    if not objectifs_connus and len(gardes) > MAX_CRENEAUX_PROFIL_VIDE:
        vides = []
        while len(gardes) > MAX_CRENEAUX_PROFIL_VIDE:
            cible = next((cr for cr in reversed(gardes) if not cr["obligatoire"]), None)
            if cible is None:
                break
            gardes.remove(cible)
            vides.append(cible["titre"])
        if vides:
            notes.append("plan court tant que je ne connais pas ton objectif (le reste revient dès "
                         "que tu me le dis) : " + " ; ".join(vides[:3]))
    if not gardes:
        return None, notes + ["aucun créneau exploitable"]

    prio = plan.get("priorite_absolue") if isinstance(plan.get("priorite_absolue"), dict) else {}
    if invente(prio.get("titre")) or invente(prio.get("pourquoi")):
        notes.append("priorité retirée : elle s'appuyait sur une donnée de vie que tu ne m'as pas donnée")
    # Sans objectif énoncé par JOSY, il n'y a pas de vraie priorité : on le dit au lieu de l'inventer.
    if not objectifs_connus:
        notes.append("priorité provisoire, en attendant ton objectif du moment "
                     "(<code>/vie objectifs.30j : …</code>)")
    return {
        "date": str(plan.get("date") or "")[:10],
        "resume": "" if invente(plan.get("resume")) else str(plan.get("resume") or "")[:200],
        "priorite_absolue": {
            "titre": "" if invente(prio.get("titre")) else str(prio.get("titre") or "")[:150],
            "pourquoi": "" if invente(prio.get("pourquoi")) else str(prio.get("pourquoi") or "")[:300],
            "creneau": str(prio.get("creneau") or "")[:20],
            "duree_min": prio.get("duree_min") if isinstance(prio.get("duree_min"), int) else None,
        },
        "priorite_provisoire": not objectifs_connus,
        "creneaux": gardes,
        "charge_min": charge_travail(gardes),
        "ce_que_je_prends_en_charge": [str(x)[:200] for x in
                                       (plan.get("ce_que_je_prends_en_charge") or [])][:5],
        "ce_que_je_laisse_de_cote": [str(x)[:200] for x in
                                     (plan.get("ce_que_je_laisse_de_cote") or [])][:5],
        "alertes": [str(x)[:200] for x in (plan.get("alertes") or []) if not invente(x)][:4] + notes,
        "profil_incomplet": bool(plan.get("profil_incomplet", True)),
    }, notes


def generer(c, store, tg, jour, ajustement=None, motif="matin"):
    """Demande un plan au modèle. None s'il ne répond pas ou mal : jamais de plan inventé."""
    if not c.llm_configured():
        store.log("SYSTEME", "fondateur_sans_modele")
        return None
    p = profil(store)
    try:
        system = c.AGENTS_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        store.log("EXECUTIF", "fondateur_agents_illisible", details={"erreur": c.safe_error(exc)})
        return None
    # I3 : JOSY sait que sa vie part chez le fournisseur du modèle quand celui-ci est hébergé.
    local = all(f.get("name") == "ollama" for f in c.LLM_CHAIN)
    if p and not local:
        store.log("EXECUTIF", "profil_vie_envoye_fournisseur", details={"fournisseur": c.LLM_PROVIDER})
        if store.get("note_vie_fournisseur") != "1":
            store.set("note_vie_fournisseur", "1")
            _envoyer(tg, "ℹ️ Pour construire une journée sur mesure, j'envoie ton profil de vie au modèle "
                         "que tu utilises (" + c.html.escape(str(c.LLM_PROVIDER))
                         + "). Pour que rien ne quitte ton PC : <code>LLM_PROVIDER=ollama</code>.")
    resultat = c.llm_chat(system, _contexte(c, store, jour, ajustement), store,
                          json_mode=True, max_tokens=2400)
    if resultat is None:
        store.log("EXECUTIF", "fondateur_plan_sans_reponse", details={"motif": motif})
        return None
    plan, notes = _nettoyer(resultat if isinstance(resultat, dict) else {}, p)
    if plan is None:
        store.log("JUDICIAIRE", "fondateur_plan_rejete", details={"motifs": notes[:4]})
        return None
    plan["date"] = jour
    plan["motif"] = motif
    if ajustement:
        plan["ajustement"] = str(ajustement)[:300]
    return plan


# --------------------------------------------------------------------------
# Rendu Telegram (court, lisible, sans reproche)
# --------------------------------------------------------------------------
def _joli_jour(jour):
    try:
        d = date.fromisoformat(jour)
        return f"{JOURS_NOMS[d.weekday()]} {d.day} {MOIS_FR[d.month - 1]}"
    except (ValueError, TypeError):
        return str(jour)


def rendu(c, plan, question=None, titre=None):
    e = c.html.escape
    lignes = [(titre or "🗓 <b>Ta journée</b>") + f" · {e(_joli_jour(plan.get('date', '')))}"]
    if plan.get("resume"):
        lignes.append(f"<i>{e(plan['resume'])}</i>")
    prio = plan.get("priorite_absolue") or {}
    if prio.get("titre"):
        creneau = f" · {e(prio['creneau'])}" if prio.get("creneau") else ""
        etiquette = "Priorité provisoire" if plan.get("priorite_provisoire") else "Priorité"
        lignes += ["", f"⭐ <b>{etiquette} : {e(prio['titre'])}</b>{creneau}"]
        if prio.get("pourquoi"):
            lignes.append(f"   {e(prio['pourquoi'])}")
    lignes.append("")
    for i, cr in enumerate(plan.get("creneaux", []), 1):
        marque = {"fait": "✅ ", "reporte": "↪️ "}.get(cr.get("statut"), "")
        lignes.append(f"{marque}{i}. <b>{e(cr['debut'])}–{e(cr['fin'])}</b> "
                      f"[{e(cr['type'])}] {e(cr['titre'])}"
                      + ("" if cr.get("obligatoire") else " · facultatif"))
        if cr.get("details"):
            lignes.append(f"     {e(cr['details'])}")
    if plan.get("charge_min"):
        lignes += ["", f"⏱ Charge de travail : {plan['charge_min'] // 60} h {plan['charge_min'] % 60:02d}"]
    for titre_bloc, cle in (("🤝 Je prends en charge : ", "ce_que_je_prends_en_charge"),
                            ("🚫 Je laisse de côté : ", "ce_que_je_laisse_de_cote")):
        valeurs = plan.get(cle) or []
        if valeurs:
            lignes.append(titre_bloc + " · ".join(e(v) for v in valeurs[:4]))
    for alerte in plan.get("alertes") or []:
        lignes.append(f"⚠️ {e(alerte)}")
    if question:
        lignes += ["", f"❓ <b>{e(question['question'])}</b>",
                   f"   <i>{e(question['pourquoi'])}</i> — réponds simplement, ou "
                   f"<code>/vie {e(question['champ'])} : ta réponse</code>"]
    lignes += ["", "<code>/fait 1</code> · <code>/reporte 2</code> · <code>/ajuste …</code> · "
                   "<code>/jour</code> · <code>/jour off</code>"]
    return "\n".join(lignes)[:4000]


def envoyer_plan(c, store, tg, plan, question=None, titre=None):
    _envoyer(tg, rendu(c, plan, question, titre))
    sauver_plan(store, plan["date"], plan)
    store.log("FONDATEUR", "plan_journee", details={
        "date": plan["date"], "motif": plan.get("motif", "matin"),
        "creneaux": len(plan.get("creneaux", [])), "charge_min": plan.get("charge_min"),
        "priorite": (plan.get("priorite_absolue") or {}).get("titre", "")[:120],
        "profil_incomplet": plan.get("profil_incomplet")})
    if question:
        poser_question(c, store, question)


def texte_bilan(plan):
    faits = [cr for cr in plan.get("creneaux", []) if cr.get("statut") == "fait"]
    restants = [cr for cr in plan.get("creneaux", []) if cr.get("statut") != "fait"]
    lignes = ["🌙 <b>Ta journée, sans jugement</b>"]
    if faits:
        lignes.append("✅ Fait : " + " · ".join(cr["titre"] for cr in faits[:4]))
    if restants:
        lignes.append("↪️ Reste : " + " · ".join(cr["titre"] for cr in restants[:4]))
        lignes.append("Je peux le remettre demain, ou le laisser tomber : dis-moi.")
    elif faits:
        lignes.append("Journée tenue. Repose-toi.")
    else:
        lignes.append("Rien de noté aujourd'hui. Demain est un autre jour.")
    return "\n".join(lignes)[:1500]


# --------------------------------------------------------------------------
# Cycle (appelé à chaque exécution de cortex.py)
# --------------------------------------------------------------------------
def cycle(c, cx):
    store, tg = _store(cx), _tg(cx)
    d = c.now().astimezone(c.PARIS)
    jour = d.date().isoformat()
    maintenant = d.hour * 60 + d.minute
    p = profil(store)

    if store.get("fondateur_accueil") != "1":
        store.set("fondateur_accueil", "1")
        _envoyer(tg, "🧠 Je change d'ordre de priorité : <b>toi d'abord</b>, l'entreprise ensuite.\n"
                     "Chaque matin, une journée paramétrée (créneaux, une seule priorité, charge "
                     "réaliste) ; je la recale quand ça bouge ; et je te pose une question à la fois "
                     "pour apprendre ta vie réelle.\n"
                     "Rien ne t'est imposé : <code>/jour</code>, <code>/ajuste …</code>, "
                     "<code>/jour off</code>, <code>/profil</code>.")
        store.log("FONDATEUR", "priorite_fondateur_activee")

    plan = plan_du_jour(store, jour)

    # Jour off : un message, puis silence — je ne relance pas (I14).
    if store.get("off_force") == jour or d.weekday() in jours_off(p):
        if store.get("off_le") != jour:
            store.set("off_le", jour)
            _envoyer(tg, "🌿 Jour off : je ne te propose rien aujourd'hui et je ne relance pas. "
                         "Si tu veux travailler quand même : <code>/jour</code>.")
            store.log("FONDATEUR", "journee_off")
        return

    # 1. Le matin : le plan du jour (une fois ; quelques essais au plus si le modèle échoue).
    if plan is None:
        if maintenant < heure_plan(p) or dans_silence(p, maintenant):
            return  # trop tôt, ou dans une plage qu'il a demandé de laisser tranquille
        essais = int(store.get(f"plan_essais_{jour}", "0") or 0)
        if essais >= MAX_ESSAIS_PLAN:
            return
        store.set(f"plan_essais_{jour}", essais + 1)
        question = _question_a_poser(c, store, p)
        plan = generer(c, store, tg, jour, motif="matin")
        if plan:
            envoyer_plan(c, store, tg, plan, question)
        return

    plafond_atteint = messages_du_jour(store, jour) >= plafond_messages(p)

    # 2. Mi-journée : une relance courte pour recaler, jamais pendant le silence.
    if (maintenant >= CHECK_MIDI[0] * 60 + CHECK_MIDI[1] and store.get(f"check_{jour}") != "1"
            and not plafond_atteint):
        store.set(f"check_{jour}", "1")
        restants = [cr for cr in plan.get("creneaux", []) if cr.get("statut") != "fait"]
        if restants and not dans_silence(p, maintenant):
            _envoyer(tg, f"🕐 Où en es-tu ? Il reste {len(restants)} créneau(x), dont "
                         f"« {c.html.escape(restants[0]['titre'])} » à {restants[0]['debut']}.\n"
                         "Dis-moi ce qui a changé et je recale : <code>/ajuste …</code> — "
                         "ou <code>/fait 1</code>, <code>/reporte 1</code>.")
            store.log("FONDATEUR", "check_milieu_journee")

    # 3. Le soir : un constat, sans reproche.
    if maintenant >= BILAN_SOIR[0] * 60 + BILAN_SOIR[1] and store.get(f"bilan_{jour}") != "1":
        store.set(f"bilan_{jour}", "1")
        if not dans_silence(p, maintenant):
            _envoyer(tg, texte_bilan(plan))
            store.log("FONDATEUR", "bilan_journee")

    # 4. Une question de vie par jour, si le plan n'a pas déjà permis de la poser.
    question = _question_a_poser(c, store, p) if not plafond_atteint else None
    if question and not dans_silence(p, maintenant):
        _envoyer(tg, f"❓ {c.html.escape(question['question'])}\n"
                     f"<i>{c.html.escape(question['pourquoi'])}</i> — réponds simplement, ou "
                     f"<code>/vie {c.html.escape(question['champ'])} : ta réponse</code>")
        poser_question(c, store, question)
        store.log("FONDATEUR", "question_du_jour_envoyee")


# --------------------------------------------------------------------------
# Réponses libres de JOSY : « je me lève vers 7h » doit être retenu
# --------------------------------------------------------------------------
def capturer(c, cx, texte):
    """Retient un message libre comme réponse à la question en attente. Vrai si retenu."""
    store, tg = _store(cx), _tg(cx)
    cle = question_en_attente(c, store)
    if not cle:
        return False
    t = (texte or "").strip()
    if len(t) < 3 or len(t) > 400 or "?" in t or ORDRE_RE.search(t):
        return False  # une question ou un ordre de mission n'est pas une donnée de vie
    apprendre(c, store, t, cle)
    store.set("derniere_question", c.now().astimezone(c.PARIS).date().isoformat())
    _envoyer(tg, "📝 Noté : <i>" + c.html.escape(t[:200]) + "</i> — je m'en sers pour tes prochaines "
                  "journées. Pour corriger : <code>/vie " + c.html.escape(cle) + " : …</code>")
    store.log("HUMAIN", "reponse_vie_capturee", details={"champ": cle})
    return True


# --------------------------------------------------------------------------
# Commandes Telegram
# --------------------------------------------------------------------------
def _trouver_creneau(plan, arg):
    try:
        i = int(str(arg).strip())
    except (TypeError, ValueError):
        return None
    creneaux = plan.get("creneaux", [])
    return creneaux[i - 1] if 1 <= i <= len(creneaux) else None


def _reporter_statuts(ancien, nouveaux):
    """Un créneau refait garde le statut du créneau équivalent (même titre)."""
    etat = {cr.get("titre"): cr.get("statut") for cr in ancien.get("creneaux", [])}
    for cr in nouveaux:
        if etat.get(cr.get("titre")) == "fait":
            cr["statut"] = "fait"
    return nouveaux


def commande(c, cx, cmd, args, texte):
    """Traite une commande de la vie du fondateur. Renvoie True si elle est prise en charge."""
    store, tg = _store(cx), _tg(cx)
    if cmd in ("/jour", "/ajuste", "/bilan") and store.get("system_status", "actif") == "arrete":
        _envoyer(tg, "🛑 Cortex arrêté (I9). <code>/reprise</code> pour relancer.")
        return True
    aujourdhui = c.now().astimezone(c.PARIS).date().isoformat()
    p = profil(store)

    if cmd == "/profil":
        remplies = [(k, v) for k, v in sorted(p.items()) if k in CHAMPS_DICT and isinstance(v, str)]
        lignes = ["👤 <b>Ce que je sais de ta vie</b>"]
        lignes += [f"• <b>{c.html.escape(k)}</b> : {c.html.escape(v)}" for k, v in remplies] or \
                  ["• rien encore : réponds à mes questions, ou écris <code>/vie …</code>"]
        restants = [cle for cle, _q, _p in CHAMPS if not p.get(cle)]
        lignes.append(f"Manquant : {len(restants)} champ(s).")
        q = question_du_jour(c, store, p)
        if q:
            lignes.append(f"❓ Prochaine question : <b>{c.html.escape(q['question'])}</b>")
        lignes.append("Miroir lisible du profil : <code>vie-fondateur.md</code> "
                      "(dans le dossier de travail).")
        _envoyer(tg, "\n".join(lignes)[:3800])
        return True

    if cmd == "/vie":
        suite = " ".join(args).strip()
        cle = None
        if ":" in suite:
            tete, _, reste = suite.partition(":")
            if tete.strip() in CHAMPS_DICT:
                cle, suite = tete.strip(), reste.strip()
        if not suite:
            _envoyer(tg, "Usage : <code>/vie ta réponse</code> — ou "
                         "<code>/vie rythme.lever : 7h</code> pour un champ précis.")
            return True
        apprendre(c, store, suite, cle or question_en_attente(c, store))
        store.set("derniere_question", aujourdhui)
        _envoyer(tg, "✅ Enregistré" + (f" dans <b>{c.html.escape(cle)}</b>" if cle else "")
                     + ". Je m'en sers dès le prochain plan (<code>/jour</code> pour le refaire).")
        return True

    if cmd == "/jour":
        if args and args[0].lower() in ("off", "repos", "stop"):
            store.set("off_force", aujourdhui)
            store.set("off_le", aujourdhui)
            _envoyer(tg, "🌿 Journée off enregistrée. Je ne propose rien et je ne relance pas. "
                         "<code>/jour</code> si tu changes d'avis.")
            store.log("HUMAIN", "journee_off_demandee")
            return True
        store.set("off_force", "")
        plan = generer(c, store, tg, aujourdhui, motif="demande")
        if not plan:
            _envoyer(tg, "Je n'ai pas réussi à construire la journée (modèle indisponible ou réponse "
                         "inexploitable). Rien n'a été inventé : réessaie dans un moment.")
            return True
        envoyer_plan(c, store, tg, plan, _question_a_poser(c, store, p),
                     titre="🗓 <b>Ta journée (refaite)</b>")
        return True

    if cmd == "/ajuste":
        suite = " ".join(args).strip()
        if not suite:
            _envoyer(tg, "Dis-moi ce qui a changé : <code>/ajuste 2 h de retard, je suis crevé</code>")
            return True
        plan = generer(c, store, tg, aujourdhui, ajustement=suite, motif="ajustement")
        if not plan:
            _envoyer(tg, "Je n'ai pas pu recaler la journée. Redis-le au prochain cycle, ou "
                         "<code>/reporte n</code> pour décaler un créneau précis.")
            return True
        ancien = plan_du_jour(store, aujourdhui)
        if ancien:
            plan["creneaux"] = _reporter_statuts(ancien, plan["creneaux"])
        envoyer_plan(c, store, tg, plan, None, titre="🔁 <b>Journée recalée</b>")
        store.log("HUMAIN", "journee_ajustee", details={"longueur": len(suite)})
        return True

    if cmd in ("/fait", "/reporte"):
        plan = plan_du_jour(store, aujourdhui)
        if not plan:
            _envoyer(tg, "Pas de plan aujourd'hui. <code>/jour</code> pour le construire.")
            return True
        cr = _trouver_creneau(plan, args[0] if args else "")
        if cr is None:
            _envoyer(tg, f"Donne le numéro du créneau (1 à {len(plan.get('creneaux', []))}) : "
                         f"<code>{cmd} 1</code>")
            return True
        cr["statut"] = "fait" if cmd == "/fait" else "reporte"
        if cmd == "/reporte" and len(args) > 1:
            cr["details"] = (cr.get("details", "") + " — reporté : " + " ".join(args[1:]))[:400]
        sauver_plan(store, aujourdhui, plan)
        store.log("HUMAIN", "creneau_" + cr["statut"], details={"titre": cr["titre"][:80]})
        if cmd == "/fait":
            restants = [x for x in plan.get("creneaux", []) if x.get("statut") != "fait"]
            _envoyer(tg, f"✅ « {c.html.escape(cr['titre'])} » fait. "
                         + (f"Reste {len(restants)} créneau(x)." if restants else "Journée tenue. 🌿"))
        else:
            _envoyer(tg, f"↪️ « {c.html.escape(cr['titre'])} » reporté. Dis-moi où le remettre : "
                         "<code>/ajuste …</code>")
        return True

    if cmd == "/bilan":
        plan = plan_du_jour(store, aujourdhui)
        _envoyer(tg, texte_bilan(plan) if plan else "Rien à constater : pas de plan aujourd'hui.")
        return True

    return False


# ==========================================================================
# RUNTIME AUTONOME — de quoi tourner seul, sans cortex.py
# ==========================================================================
# Le noyau ci-dessus ne connaît que deux objets :
#   * un « hôte » (c) : l'heure, le fuseau, l'échappement HTML, les chemins, le
#     modèle de langage. Cortex.py joue ce rôle quand le module est branché
#     dedans ; `Environnement` joue exactement le même rôle en autonome.
#   * un « canal » (cx) : une base (.s) et une sortie (.tg). L'instance Cortex
#     joue ce rôle branché ; `Autonome` le joue en autonome.
# Aucun autre fichier du projet n'est nécessaire : ni cortex.py, ni .env
# obligatoire, ni dépendance externe (urllib et sqlite3 suffisent).

VERSION = "1.0"
INTERVALLE_DEFAUT_MIN = 5


def _dossier_module():
    return Path(__file__).resolve().parent


def _fuseau_paris():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Europe/Paris")
    except Exception:  # tzdata absent : on reste honnêtement en UTC
        return timezone.utc


PARIS_LOCAL = _fuseau_paris()


def _maintenant():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


DERNIERE_ERREUR = ""   # raison du dernier appel modèle raté (transparence, I3)


def _post_json(url, corps, entetes=None, timeout=30):
    """POST JSON minimal, sans dépendance : urllib suffit.

    Un en-tête User-Agent est indispensable : sans lui, Cloudflare (devant les
    API hébergées comme Groq) répond 403 « error code: 1010 ».
    """
    global DERNIERE_ERREUR
    donnees = json.dumps(corps).encode("utf-8")
    entete = {"Content-Type": "application/json",
              "User-Agent": f"JOSY-EI-Fondateur/{VERSION} (+https://josyei.com)"}
    entete.update(entetes or {})
    requete = urllib.request.Request(url, data=donnees, headers=entete)
    try:
        with urllib.request.urlopen(requete, timeout=timeout) as reponse:
            return json.loads(reponse.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        DERNIERE_ERREUR = f"HTTP {exc.code} {detail}".strip()
        return None
    except (urllib.error.URLError, ValueError, OSError) as exc:
        DERNIERE_ERREUR = f"{type(exc).__name__}"
        return None


class StoreLocal:
    """Base SQLite autonome : mêmes tables utiles et même journal chaîné (I1)."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE IF NOT EXISTS proposals (
        action_id TEXT PRIMARY KEY, created_at TEXT, risk_level TEXT, mission TEXT,
        action_type TEXT, status TEXT, expires_at TEXT, decided_at TEXT,
        decision_source TEXT, tg_message_id INTEGER, payload TEXT);
    CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, power TEXT, event TEXT,
        action_id TEXT, details TEXT, prev_hash TEXT, hash TEXT);
    """

    def __init__(self, chemin):
        self.chemin = str(chemin)
        self.db = sqlite3.connect(self.chemin, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(self.SCHEMA)
        self.db.commit()

    def get(self, key, default=None):
        ligne = self.db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return ligne["value"] if ligne else default

    def set(self, key, value):
        self.db.execute("INSERT INTO kv(key, value) VALUES(?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
        self.db.commit()

    def log(self, power, event, action_id=None, details=None):
        """Journal append-only chaîné par empreinte, comme cortex.py : vérifiable de la même façon."""
        ts = _iso(_maintenant())
        ligne = self.db.execute("SELECT hash FROM journal ORDER BY id DESC LIMIT 1").fetchone()
        precedent = ligne["hash"] if ligne else "GENESIS"
        det = json.dumps(details or {}, ensure_ascii=False, sort_keys=True)
        empreinte = hashlib.sha256(
            f"{precedent}|{ts}|{power}|{event}|{action_id or ''}|{det}".encode()).hexdigest()
        self.db.execute("INSERT INTO journal(ts, power, event, action_id, details, prev_hash, hash) "
                        "VALUES(?,?,?,?,?,?,?)",
                        (ts, power, event, action_id, det, precedent, empreinte))
        self.db.commit()
        return empreinte

    def verify_journal(self):
        precedent = "GENESIS"
        for ligne in self.db.execute("SELECT * FROM journal ORDER BY id"):
            empreinte = hashlib.sha256(
                f"{precedent}|{ligne['ts']}|{ligne['power']}|{ligne['event']}|"
                f"{ligne['action_id'] or ''}|{ligne['details']}".encode()).hexdigest()
            if ligne["prev_hash"] != precedent or ligne["hash"] != empreinte:
                return False, ligne["id"]
            precedent = ligne["hash"]
        return True, None


def _sans_balises(texte):
    return re.sub(r"[ \t]+", " ", html.unescape(re.sub(r"<[^>]+>", "", texte or ""))).strip()


class CanalConsole:
    """Sortie de secours : rien ne part vers l'extérieur, tout s'affiche et s'archive."""

    nom = "console"

    def __init__(self, fichier=None):
        self.fichier = Path(fichier) if fichier else None

    def send(self, texte, buttons=None):
        propre = _sans_balises(texte)
        print(propre)
        if self.fichier:
            try:
                with self.fichier.open("a", encoding="utf-8") as f:
                    f.write(f"\n--- {_iso(_maintenant())} ---\n{propre}\n")
            except OSError:
                pass
        return None

    def alert(self, kind, message):
        print(f"[alerte {kind}] {_sans_balises(str(message))[:300]}")


class CanalTelegram:
    """Envoi Telegram direct, sans dépendance : seule la bibliothèque standard est utilisée."""

    nom = "telegram"

    def __init__(self, token, chat):
        self.token, self.chat = (token or "").strip(), (chat or "").strip()
        self.enabled = bool(self.token and self.chat)

    def send(self, texte, buttons=None):
        if not self.enabled:
            return None
        corps = {"chat_id": self.chat, "text": texte[:4096], "parse_mode": "HTML",
                 "disable_web_page_preview": True}
        if buttons:
            corps["reply_markup"] = {"inline_keyboard": [buttons]}
        reponse = _post_json(f"https://api.telegram.org/bot{self.token}/sendMessage", corps)
        return ((reponse or {}).get("result") or {}).get("message_id")

    def alert(self, kind, message):
        self.send(f"⚠️ Erreur {html.escape(str(kind))}. Détails : "
                  f"{html.escape(str(message)[:300])}.")


FOURNISSEURS = {
    "ollama": {"url": "http://localhost:11434/api/chat", "model": "qwen2.5:3b",
               "key_env": None, "timeout": 300},
    "groq": {"url": "https://api.groq.com/openai/v1/chat/completions",
             "model": "openai/gpt-oss-120b", "key_env": "GROQ_API_KEY", "timeout": 90},
    "mistral": {"url": "https://api.mistral.ai/v1/chat/completions",
                "model": "mistral-small-latest", "key_env": "MISTRAL_API_KEY", "timeout": 90},
}


def _fournisseur(nom, principal=False):
    nom = (nom or "").strip().lower()
    if nom not in FOURNISSEURS:
        return None
    cfg = dict(FOURNISSEURS[nom], name=nom)
    if principal:
        cfg["url"] = os.environ.get("LLM_URL", "").strip() or cfg["url"]
        cfg["model"] = os.environ.get("LLM_MODEL", "").strip() or cfg["model"]
    cfg["key"] = os.environ.get(cfg["key_env"], "").strip() if cfg["key_env"] else ""
    if cfg["key_env"] and not cfg["key"]:
        return None  # fournisseur hébergé sans clé : inutilisable, on ne fait pas semblant
    return cfg


def chaine_par_defaut():
    """Principal (LLM_PROVIDER, sinon Groq si la clé existe, sinon Ollama), puis replis.

    Même stratégie que cortex.py : entre modèles Groq (chaque modèle a son propre
    quota journalier, donc un quota épuisé sur gpt-oss-120b n'empêche pas le
    suivant), puis LLM_FALLBACK, puis Ollama local. Si tout échoue : aucune
    journée inventée, la raison est journalisée.
    """
    principal = os.environ.get("LLM_PROVIDER", "").strip()
    if principal.lower() in ("aucun", "none", "off", "non"):
        return []  # refus explicite de tout modèle : le module le dira, il n'inventera pas
    if not principal:
        principal = "groq" if os.environ.get("GROQ_API_KEY", "").strip() else "ollama"
    chaine = [p for p in (_fournisseur(principal, principal=True),
                          _fournisseur(os.environ.get("LLM_FALLBACK", ""))) if p]
    groq = next((p for p in chaine if p["name"] == "groq"), None)
    if groq:
        position = chaine.index(groq) + 1
        for modele in ("openai/gpt-oss-20b", "qwen/qwen3.8-27b"):
            if not any(p["name"] == "groq" and p["model"] == modele for p in chaine):
                chaine.insert(position, dict(groq, model=modele))
                position += 1
    if not any(p["name"] == "ollama" for p in chaine):
        local = _fournisseur("ollama")  # dernier recours : sur le PC, donc gratuit et privé
        if local:
            chaine.append(local)
    return chaine


class ModeleLLM:
    """Appel au modèle, compatible OpenAI et Ollama, sans dépendance externe."""

    def __init__(self, chaine=None):
        self.chaine = chaine if chaine is not None else chaine_par_defaut()

    def configure(self):
        return bool(self.chaine)

    def chat(self, system, user, store=None, json_mode=True, max_tokens=2000):
        for cfg in self.chaine:
            resultat = self._appel(cfg, system, user, json_mode, max_tokens)
            if resultat is not None:
                return resultat
            if store is not None:  # I3 : JOSY peut savoir pourquoi le modèle n'a pas répondu
                store.log("EXECUTIF", "modele_echec", details={"fournisseur": cfg["name"],
                                                              "raison": DERNIERE_ERREUR[:200]})
        return None

    def _appel(self, cfg, system, user, json_mode, max_tokens):
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        entetes, corps = {}, {}
        if cfg["name"] == "ollama":
            corps = {"model": cfg["model"], "messages": messages, "stream": False,
                     "options": {"temperature": 0.2, "num_ctx": 8192, "num_predict": max_tokens}}
            if json_mode:
                corps["format"] = "json"
        else:
            entetes = {"Authorization": f"Bearer {cfg['key']}"}
            corps = {"model": cfg["model"], "messages": messages,
                     "temperature": 0.2, "max_tokens": max_tokens}
            if json_mode:
                corps["response_format"] = {"type": "json_object"}
        donnees = _post_json(cfg["url"], corps, entetes, cfg["timeout"])
        if donnees is None and json_mode and cfg["name"] != "ollama":
            corps.pop("response_format", None)  # certains modèles refusent ce champ
            donnees = _post_json(cfg["url"], corps, entetes, cfg["timeout"])
        if donnees is None:
            return None
        try:
            contenu = (donnees["message"]["content"] if cfg["name"] == "ollama"
                       else donnees["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError):
            return None
        if not json_mode:
            return str(contenu).strip()
        trouve = re.search(r"\{.*\}", str(contenu), re.S)
        try:
            return json.loads(trouve.group(0) if trouve else contenu)
        except ValueError:
            return None  # I6 : réponse illisible = rien, jamais une invention


class Environnement:
    """L'hôte autonome : exactement les mêmes noms que ceux fournis par cortex.py."""

    def __init__(self, dossier=None, doctrine=None, modele=None):
        self.BASE_DIR = Path(dossier) if dossier else _dossier_module()
        self.AGENTS_PATH = Path(doctrine) if doctrine else self.BASE_DIR / "AGENTS.md"
        self.PARIS = PARIS_LOCAL
        self.VERSION = VERSION
        self.modele = modele if modele is not None else ModeleLLM()
        self.LLM_CHAIN = self.modele.chaine
        self.LLM_PROVIDER = self.LLM_CHAIN[0]["name"] if self.LLM_CHAIN else "aucun"

    def now(self):
        return _maintenant()

    def iso(self, dt):
        return _iso(dt)

    def safe_error(self, exc):
        return type(exc).__name__

    def llm_configured(self):
        return self.modele.configure()

    def llm_chat(self, system, user, store=None, json_mode=True, max_tokens=2000):
        return self.modele.chat(system, user, store, json_mode, max_tokens)


Environnement.html = html  # le noyau appelle c.html.escape(...)


class Autonome:
    """Le canal autonome : une base (.s) et une sortie (.tg), comme l'instance Cortex."""

    def __init__(self, store, canal):
        self.s, self.tg = store, canal


def charger_env(dossier=None):
    """Charge .env / .env.serper s'ils existent (python-dotenv facultatif)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False
    base = Path(dossier) if dossier else _dossier_module()
    for nom in (".env", ".env.serper"):
        chemin = base / nom
        if chemin.exists():
            load_dotenv(chemin)
    return True


def hote_autonome(dossier=None, base=None, doctrine=None, dry_run=False,
                  modele=None, journal_console=None):
    """Construit un hôte et un canal autonomes : c'est tout ce dont le noyau a besoin."""
    env = Environnement(dossier=dossier, doctrine=doctrine, modele=modele)
    store = StoreLocal(base or (env.BASE_DIR / "fondateur.db"))
    token, chat = os.environ.get("TG_TOKEN", ""), os.environ.get("TG_CHAT", "")
    if dry_run or not (token.strip() and chat.strip()):
        canal = CanalConsole(journal_console or (env.BASE_DIR / "journal-fondateur.log"))
    else:
        canal = CanalTelegram(token, chat)
    store.tg = canal
    return env, Autonome(store, canal)


def etat_autonome(env, auto):
    """Ce que le module autonome est capable de dire de lui-même, sans rien inventer."""
    store, canal = auto.s, auto.tg
    jour = env.now().astimezone(env.PARIS).date().isoformat()
    remplis = [cle for cle in CHAMPS_DICT if profil(store).get(cle)]
    plan = plan_du_jour(store, jour)
    integre, ligne = store.verify_journal()
    return "\n".join([
        f"fondateur {VERSION} — module autonome (aucun cortex.py requis)",
        f"  base        : {store.chemin}",
        f"  doctrine    : {env.AGENTS_PATH} "
        f"{'(présente)' if env.AGENTS_PATH.exists() else '(MANQUANTE — le plan sera refusé)'}",
        f"  fuseau      : {env.PARIS}",
        f"  modèle      : " + (" puis ".join(f"{f['name']}/{f['model']}" for f in env.LLM_CHAIN)
                              or "aucun (aucune clé ni Ollama)"),
        f"  sortie      : {canal.nom}" + (" (aucun envoi réel)" if canal.nom == "console" else ""),
        f"  profil      : {len(remplis)}/{len(CHAMPS_DICT)} champs connus",
        f"  plan du jour: {'oui' if plan else 'non'}",
        f"  journal     : " + ("intègre" if integre else f"ALTÉRÉ à la ligne {ligne}"),
    ])


def main(argv=None):
    """Point d'entrée autonome : python -m fondateur (ou python fondateur.py)."""
    # Une console Windows écrit en cp1252 par défaut : sans ça, un simple émoji
    # ferait planter la commande. On écrit en UTF-8 et on ne perd jamais une ligne.
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    analyseur = argparse.ArgumentParser(
        prog="fondateur",
        description="La vie du fondateur (I14) : profil de vie et plan du jour, "
                    "en module autonome, sans cortex.py.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exemples :\n"
               "  python -m fondateur --etat\n"
               "  python -m fondateur --profil\n"
               "  python -m fondateur --plan --dry-run\n"
               "  python -m fondateur --boucle --toutes-les-minutes 15\n"
               "  python -m fondateur --champ rythme.lever=7h --plan\n")
    analyseur.add_argument("--base", help="base SQLite (défaut : fondateur.db à côté du module)")
    analyseur.add_argument("--dossier", help="dossier de travail (défaut : celui du module)")
    analyseur.add_argument("--doctrine", help="chemin d'AGENTS.md (défaut : à côté du module)")
    analyseur.add_argument("--dry-run", action="store_true",
                           help="aucun envoi Telegram : tout s'affiche et s'archive")
    analyseur.add_argument("--etat", action="store_true", help="état du module autonome")
    analyseur.add_argument("--profil", action="store_true", help="affiche le profil de vie connu")
    analyseur.add_argument("--plan", action="store_true", help="construit et envoie le plan du jour")
    analyseur.add_argument("--bilan", action="store_true", help="bilan de la journée")
    analyseur.add_argument("--jour-off", action="store_true", help="journée off")
    analyseur.add_argument("--fait", metavar="N", help="marque un créneau comme fait")
    analyseur.add_argument("--reporte", metavar="N", help="reporte un créneau")
    analyseur.add_argument("--ajuste", metavar="TEXTE", help="recale la journée (ce qui a changé)")
    analyseur.add_argument("--vie", metavar="TEXTE", help="enregistre une réponse de vie")
    analyseur.add_argument("--champ", metavar="CLE=VALEUR",
                           help="enregistre une donnée précise (ex. rythme.lever=7h)")
    analyseur.add_argument("--boucle", action="store_true", help="tourne en continu")
    analyseur.add_argument("--toutes-les-minutes", type=int, default=INTERVALLE_DEFAUT_MIN,
                           help=f"intervalle de la boucle (défaut : {INTERVALLE_DEFAUT_MIN})")
    analyseur.add_argument("--version", action="version", version=f"fondateur {VERSION}")
    args = analyseur.parse_args(argv)

    charger_env(args.dossier)
    env, auto = hote_autonome(dossier=args.dossier, base=args.base, doctrine=args.doctrine,
                              dry_run=args.dry_run)
    store, canal = auto.s, auto.tg

    if args.etat:
        print(etat_autonome(env, auto))
        return 0

    if args.champ:
        cle, _, valeur = args.champ.partition("=")
        cle, valeur = cle.strip(), valeur.strip()
        if cle not in CHAMPS_DICT:
            print(f"Champ inconnu : {cle}\nChamps possibles : " + ", ".join(CHAMPS_DICT))
            return 2
        if not valeur:
            print("Valeur vide : rien n'a été enregistré.")
            return 2
        apprendre(env, store, valeur, cle)
        print(f"Enregistré : {cle} = {valeur}")
        return 0

    if args.vie:
        apprendre(env, store, args.vie, question_en_attente(env, store))
        print("Enregistré. /profil pour voir ce que je sais.")
        return 0

    # Tout ce qui produit un plan exige la doctrine et un modèle : sinon on le dit, on n'invente pas.
    besoin_modele = args.plan or args.boucle or args.ajuste or not (
        args.profil or args.bilan or args.jour_off or args.fait or args.reporte)
    if besoin_modele:
        if not env.AGENTS_PATH.exists():
            print(f"Doctrine introuvable : {env.AGENTS_PATH}")
            print("Copie AGENTS.md à côté du module, ou indique --doctrine CHEMIN.")
            return 2
        if not env.llm_configured():
            print("Aucun modèle configuré (GROQ_API_KEY, ou MISTRAL_API_KEY, ou Ollama local).")
            print("Rien ne sera inventé : je ne fabrique pas de journée sans modèle.")
            return 2

    if canal.nom == "console":
        print(f"— sortie « {canal.nom} » : aucun envoi réel, ce qui suit est ce que JOSY recevrait —")

    if args.jour_off:
        return 0 if commande(env, auto, "/jour", ["off"], "/jour off") else 1
    if args.profil:
        return 0 if commande(env, auto, "/profil", [], "/profil") else 1
    if args.bilan:
        return 0 if commande(env, auto, "/bilan", [], "/bilan") else 1
    if args.fait:
        return 0 if commande(env, auto, "/fait", [args.fait], f"/fait {args.fait}") else 1
    if args.reporte:
        return 0 if commande(env, auto, "/reporte", [args.reporte], f"/reporte {args.reporte}") else 1
    if args.ajuste:
        return 0 if commande(env, auto, "/ajuste", args.ajuste.split(), "/ajuste") else 1
    if args.plan:
        return 0 if commande(env, auto, "/jour", [], "/jour") else 1

    if args.boucle:
        print(f"boucle autonome : un cycle toutes les {max(1, args.toutes_les_minutes)} min "
              "(Ctrl+C pour arrêter).")
        if store.get("fondateur_autre_cortex") != "1":
            store.set("fondateur_autre_cortex", "1")
            print("Attention : si le Cortex (cortex.py) tourne aussi sur la même base ou le même "
                  "bot, tu recevras deux messages. Utilise --base et un bot distincts, ou /stop.")
        while True:
            try:
                cycle(env, auto)
            except KeyboardInterrupt:
                print("\narrêt demandé.")
                return 0
            except Exception as exc:  # un cycle raté ne doit pas tuer la boucle
                store.log("SYSTEME", "cycle_erreur", details={"erreur": env.safe_error(exc)})
                print(f"erreur de cycle : {env.safe_error(exc)}")
            try:
                time.sleep(max(1, args.toutes_les_minutes) * 60)
            except KeyboardInterrupt:
                print("\narrêt demandé.")
                return 0

    try:
        cycle(env, auto)
    except Exception as exc:
        store.log("SYSTEME", "cycle_erreur", details={"erreur": env.safe_error(exc)})
        print(f"erreur de cycle : {env.safe_error(exc)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
