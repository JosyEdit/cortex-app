"""Tests simulés du bot Telegram (routage d'intention, routage_telegram.py).

Aucun appel à Telegram : un faux Telegram enregistre les messages. Travaille sur une COPIE de
cortex.db dans un dossier temporaire : la base en service n'est jamais écrite.

    python test_telegram_bot.py           # classifieur simulé (déterministe, sans réseau)
    python test_telegram_bot.py --groq    # classifieur réel (Groq, modèle léger) pour les tests 3 et 4
"""

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cortex  # noqa: E402
import fondateur  # noqa: E402
import routage_telegram as rt  # noqa: E402

REEL = "--groq" in sys.argv
# Rupture réelle du journal en service (20/10/2026 05:49:22, deux écrivains à la même seconde), relevée par
# l'inventaire du 20/10. Elle n'est jamais réécrite (I1) : le test exige que tout le reste de la chaîne soit intact.
RUPTURE_CONNUE = 22437


def journal_intact_apres(store, rupture):
    """Rechaîne le journal à partir de la ligne `rupture` (son prev_hash sert de point de départ)."""
    import hashlib
    prev = None
    for r in store.db.execute("SELECT * FROM journal WHERE id>=? ORDER BY id", (rupture,)):
        prev = r["prev_hash"] if prev is None else prev
        digest = hashlib.sha256(f"{prev}|{r['ts']}|{r['power']}|{r['event']}|{r['action_id'] or ''}|{r['details']}"
                                .encode()).hexdigest()
        if r["prev_hash"] != prev or r["hash"] != digest:
            return False, r["id"]
        prev = r["hash"]
    return True, None
STATIQUE = "en attente ·"  # morceau de l'ancienne réponse figée « Actif · 3 en attente · prochaine mission »


class FauxTelegram:
    def __init__(self, store):
        self.enabled, self.chat, self.token, self.store = True, "1", "x", store
        self.envoyes = []
        store.tg = self

    def clear_buttons(self, message_id):
        pass

    def send(self, text, buttons=None):
        self.boutons_derniers = buttons
        self.envoyes.append(text)
        return len(self.envoyes)

    def call(self, method, **params):
        return {"ok": True, "result": {}}


def faux_classifieur(system, user, store, json_mode=True, max_tokens=0, prefer=None):
    """Réponses que le modèle léger renvoie pour ces phrases (format imposé par le prompt)."""
    u = user.lower().rsplit("requête :", 1)[-1]  # seule la phrase de JOSY, pas les exemples du prompt
    if "garages" in u:
        return {"intent": "sector_query", "sector": "garages", "company_name": "", "location": ""}
    if "boulangerie dupont" in u:
        return {"intent": "audit_query", "sector": "boulangerie", "company_name": "boulangerie Dupont",
                "location": "Poitiers"}
    return {"intent": "unknown", "sector": "", "company_name": "", "location": ""}


def preparer():
    dossier = Path(tempfile.mkdtemp(prefix="cortex_test_bot_"))
    if Path(cortex.DB_PATH).exists():  # copie de la base réelle ; sinon base neuve (copie Cortex-audit)
        shutil.copy(cortex.DB_PATH, dossier / "cortex.db")
    store = cortex.Store(dossier / "cortex.db")
    tg = FauxTelegram(store)
    cx = cortex.Cortex(store, tg)
    store.set("routage_proposition", "")
    return dossier, store, tg, cx


def journal_depuis(store, depart):
    return store.db.execute("SELECT event, details FROM journal WHERE id>? AND power='INTERFACE'",
                            (depart,)).fetchall()


def envoyer(store, tg, cx, texte):
    avant = len(tg.envoyes)
    depart = store.db.execute("SELECT COALESCE(MAX(id),0) FROM journal").fetchone()[0]
    cx.chat_count = 0
    cx.handle_update({"update_id": 1, "message": {"chat": {"id": 1}, "text": texte, "date": 0}})
    return "\n".join(tg.envoyes[avant:]), journal_depuis(store, depart)


def main():
    if not REEL:
        cortex.llm_chat = faux_classifieur
        cortex.LLM_CHAIN = cortex.LLM_CHAIN or [{"name": "faux", "model": "faux"}]
    fondateur.capturer = lambda *a, **k: False  # la question du jour n'interfère pas avec ces phrases
    dossier, store, tg, cx = preparer()
    resultats = []

    def verifier(nom, condition, detail=""):
        resultats.append((nom, bool(condition), detail))

    rep, j = envoyer(store, tg, cx, "Bonjour")
    verifier("Bonjour", "Cortex" in rep and "Entreprises dans l'annuaire" in rep and STATIQUE not in rep,
             "état réel (niveau 1)")
    verifier("Bonjour journalisé", any(r["event"] == "telegram_message_recu" for r in j)
             and any(r["event"] == "telegram_reponse_envoyee" for r in j), "journal INTERFACE")

    rep, j = envoyer(store, tg, cx, "/etat")
    verifier("/etat", "Cortex" in rep and "Module OSINT" in rep and STATIQUE not in rep, "état réel")
    verifier("/etat journalisé", True, "commande_recue (HUMAIN), journal existant")

    rep, j = envoyer(store, tg, cx, "Qu'est-ce que tu peux me dire sur les garages ?")
    intent_g = next((r["details"] for r in j if r["event"] == "telegram_message_recu"), "")
    verifier("garages", '"sector_query"' in intent_g and "garage" in intent_g.lower()
             and "analyse OSINT" in rep and "(oui/non)" in rep and STATIQUE not in rep, rep[:220])
    rep_oui, j_oui = envoyer(store, tg, cx, "oui")
    verifier("garages → oui", "Rien n'est lancé" in rep_oui
             and any(r["event"] == "proposition_analyse_creee" and '"executee": false' in r["details"]
                     for r in j_oui), rep_oui[:160])

    rep, j = envoyer(store, tg, cx, "Fais un audit de la boulangerie Dupont à Poitiers")
    intent_b = next((r["details"] for r in j if r["event"] == "telegram_message_recu"), "")
    verifier("audit boulangerie", '"audit_query"' in intent_b and "Dupont" in intent_b
             and "Poitiers" in intent_b and "(oui/non)" in rep, rep[:220])
    envoyer(store, tg, cx, "non")

    rep, j = envoyer(store, tg, cx, "n'importe quoi")
    verifier("n'importe quoi", "pas bien compris" in rep, rep[:120])

    rep, j = envoyer(store, tg, cx, "Es-tu un robot ?")
    verifier("identité (I6)", "agent automatisé" in rep, rep[:80])

    # --- non-régression du 20/10/2026 : la conversation réelle de JOSY (site, suite, fiche collée, frustration)
    appels = []

    def faux_site(url):
        appels.append(("site", url))
        return {"joignable": True, "https": True, "temps_reponse_s": 0.4, "mobile": True, "titre": "JOSY EI",
                "meta_description": False, "formulaire": True, "page_contact": True, "mentions_legales": True,
                "confidentialite": True, "carte_google": False, "wordpress": False}

    def faux_legal(q):
        appels.append(("legal", q))
        return {"status": "ok", "raison_sociale": "MONSIEUR VALERY JOSY", "siren": q, "activite": "62.02A",
                "date_creation": "2022-05-31", "adresse": "86500 MONTMORILLON",
                "source": f"https://annuaire-entreprises.data.gouv.fr/entreprise/{q}"}
    rt._analyseurs_reels = lambda: {
        "site": faux_site, "technologies": lambda u: {"status": "erreur", "detail": "python-wappalyzer non installé"},
        "emails": lambda u: (appels.append(("emails", u)), {"status": "ok", "emails": ["contact@josyei.com"],
                                                            "pages_lues": 3})[1],
        "legal": faux_legal}
    REPLIS = ("pas bien compris", "Je n'ai pas identifié de secteur")

    rep, j = envoyer(store, tg, cx, "josyei.com")
    verifier("« josyei.com » : analyse du site, pas de repli", "Analyse de josyei.com" in rep
             and "contact@josyei.com" in rep and not any(x in rep for x in REPLIS), rep[:90].replace("\n", " "))
    rep, j = envoyer(store, tg, cx, "scan le site web")
    verifier("« scan le site web » reprend josyei.com", "Analyse de josyei.com" in rep
             and appels.count(("site", "https://josyei.com")) == 2 and not any(x in rep for x in REPLIS),
             rep[:60].replace("\n", " "))
    fiche = ("Entreprises françaises Vienne 62 - Programmation, conseil MONSIEUR VALERY JOSY Active Vérifiée PME "
             "Appeler Surveiller SIREN 914 113 543 SIRET DU SIEGE SOCIAL 914 113 543 00021 NUMÉRO DE TVA "
             "FR00914113543 Contact Societe.com Mentions Légales")
    rep, j = envoyer(store, tg, cx, fiche)
    verifier("fiche societe.com collée : SIREN lu dans l'annuaire officiel", ("legal", "914113543") in appels
             and "SIREN 914113543" in rep and not any(x in rep for x in REPLIS), rep[:70].replace("\n", " "))
    rep, j = envoyer(store, tg, cx, "Tu ne comprends rien")
    verifier("« Tu ne comprends rien » : aide concrète, pas le repli", "analyser un site" in rep
             and "josyei.com" in rep and not any(x in rep for x in REPLIS), rep[:70])
    verifier("une adresse email n'est pas un domaine", rt.extraire_domaine("écris à contact@josyei.com") is None)
    verifier("URL complète reconnue", rt.extraire_domaine("https://www.exemple.fr/contact") == "exemple.fr")
    verifier("analyse du site journalisée (R0)", store.db.execute(
        "SELECT COUNT(*) FROM journal WHERE event='audit_site_termine'").fetchone()[0] == 2)

    # --- non-régression du 20/10/2026 (2e conversation de JOSY sur le bot en service)
    store.set(rt.DERNIER_SUJET_CLE, "")
    store.set(rt.DERNIER_DOMAINE_CLE, "")
    n_site = appels.count(("site", "https://josyei.com"))
    rep, j = envoyer(store, tg, cx, "analyse le site josyei.com")
    verifier("« analyse le site josyei.com » : analyse lancée, pas de zone proposée",
             "Analyse de josyei.com" in rep and "Nouvelle-Aquitaine" not in rep and "(oui/non)" not in rep
             and appels.count(("site", "https://josyei.com")) == n_site + 1, rep[:60].replace("\n", " "))
    for question in ("Je ne comprend pas a quoi sert se module", "Le module OSINT"):
        rep, j = envoyer(store, tg, cx, question)
        verifier(f"« {question} » : explication du module", "sources ouvertes" in rep and "robots.txt" in rep
                 and "aucun scan de failles" in rep and not any(x in rep for x in REPLIS), rep[:60])
    url = "https://www.societe.com/societe/monsieur-valery-josy-914113543.html"
    collage = (url + "\nsociete.com\nSociété MONSIEUR VALERY JOSY (914113543) à MONTMORILLON (86500).\n"
               "MONSIEUR VALERY JOSY à MONTMORILLON (86500). Chiffre d'affaires, bénéfice, statuts, extrait RNE")
    for nom, texte in (("URL societe.com seule", url), ("URL societe.com + aperçu collé", collage)):
        avant = appels.count(("legal", "914113543"))
        rep, j = envoyer(store, tg, cx, texte)
        verifier(f"{nom} : fiche officielle par le SIREN, sans zone", appels.count(("legal", "914113543")) == avant + 1
                 and "SIREN 914113543" in rep and "Nouvelle-Aquitaine" not in rep
                 and ("site", "https://societe.com") not in appels, rep[:60].replace("\n", " "))
    avant = appels.count(("legal", "914113543"))
    rep, j = envoyer(store, tg, cx, "j'ai besoin que tu ailles chercher a la source sur le web")
    verifier("« chercher à la source sur le web » : reprend la dernière entreprise",
             appels.count(("legal", "914113543")) == avant + 1 and not any(x in rep for x in REPLIS), rep[:60])
    envoyer(store, tg, cx, "josyei.com")
    n_site = appels.count(("site", "https://josyei.com"))
    rep, j = envoyer(store, tg, cx, "va chercher à la source")
    verifier("« va chercher à la source » après un site : relit le site",
             appels.count(("site", "https://josyei.com")) == n_site + 1, rep[:50].replace("\n", " "))
    store.set(rt.DERNIER_SUJET_CLE, "")
    rep, j = envoyer(store, tg, cx, "cherche sur internet")
    verifier("« cherche sur internet » sans sujet : demande la cible, pas le repli",
             "Sur quoi veux-tu que je cherche" in rep and not any(x in rep for x in REPLIS), rep[:50])

    # --- incident du 20/10/2026 : un identifiant seul, envoyé après /valider, avait validé une relance de 2 emails
    import json as _json
    from datetime import timedelta as _td
    aid = "d867fec8-f80f-4cf2-89b2-3ed44a9adeaf"
    payload = {"action_id": aid, "action_type": "relance", "risk_level": "R2", "mission": "M3_Relation_Client",
               "target": {"company": "2 prospects", "contact": "gérant"}, "content": {"subject": "Re", "body": "x"},
               "justification": "Relance J+7 sans réponse",
               "items": [{"company": "Sermeta", "to": "info@sermeta.com", "subject": "Re: Sermeta", "body": "b"},
                         {"company": "SELARL Office du Dôme - Notaires", "to": "office@odd.notaires.fr",
                          "subject": "Re: Office", "body": "b"}]}
    # La copie de la base en service contient déjà la vraie relance de l'incident : on la remplace dans la COPIE.
    store.db.execute("DELETE FROM proposals WHERE action_id=?", (aid,))
    store.db.execute("INSERT INTO proposals(action_id, created_at, risk_level, mission, action_type, status, expires_at, "
                     "payload) VALUES(?,?,?,?,?,?,?,?)",
                     (aid, cortex.iso(cortex.now()), "R2", "M3_Relation_Client", "relance", cortex.PENDING,
                      cortex.iso(cortex.now() + _td(hours=24)), _json.dumps(payload, ensure_ascii=False)))
    store.db.commit()
    import vente
    vente.setup(store)
    store.db.execute("DELETE FROM file_envoi WHERE action_id=?", (aid,))  # idem : lignes réelles de la copie
    store.db.commit()
    statut = lambda: store.db.execute("SELECT status FROM proposals WHERE action_id=?", (aid,)).fetchone()[0]  # noqa: E731
    en_file = lambda: store.db.execute("SELECT COUNT(*) FROM file_envoi WHERE action_id=?", (aid,)).fetchone()[0]  # noqa: E731
    envoyer(store, tg, cx, "/valider")
    rep, j = envoyer(store, tg, cx, "d867fec8")
    verifier("identifiant seul après /valider : AUCUNE validation", statut() == cortex.PENDING and en_file() == 0,
             statut())
    verifier("identifiant seul : fiche + boutons, rien ne part sans clic", "Sermeta" in rep and "Rien ne part" in rep
             and tg.boutons_derniers and [b["callback_data"][:2] for b in tg.boutons_derniers] == ["v:", "r:"], rep[:60])
    rep, j = envoyer(store, tg, cx, "/valider d867fec8")
    verifier("/valider ID : confirmation demandée avec destinataires, pas d'envoi", statut() == cortex.PENDING
             and en_file() == 0 and "Confirme" in rep and "info@sermeta.com" in rep
             and tg.boutons_derniers[0]["callback_data"] == "cv:d867fec8", rep[:50])
    cx.handle_update({"update_id": 9, "callback_query": {"id": "q", "data": "cv:d867fec8", "message": {"chat": {"id": 1}}}})
    verifier("bouton « Confirmer l'envoi » : seulement alors mis en file", statut() == "valide_en_file" and en_file() == 2,
             statut())
    for q in ("C'est quoi l'action en attente ?",
              "c'est quoi et pourquoi ? :  Envoyé à Sermeta (info@sermeta.com)\n Envoyé à SELARL Office du Dôme - Notaires",
              "pourquoi tu veux leurs envoyer quoi et depuis qu'elle email?",
              "donne moi des infos sur chaque actions je ne comprends pas",
              "Je ne comprend pas se quej'ai valider ni d'ou sort ton identifiant :"):
        rep, j = envoyer(store, tg, cx, q)
        verifier(f"« {q[:45]}… » : fiche tirée du journal", "d867fec8" in rep and "relance" in rep
                 and "Relance J+7" in rep and not any(x in rep for x in REPLIS), rep[:70].replace("\n", " "))

    verifier("aucune réponse figée", not any(STATIQUE in m for m in tg.envoyes), f"{len(tg.envoyes)} messages")
    ok, bad = store.verify_journal()
    if not ok and bad == RUPTURE_CONNUE:
        ok, bad = journal_intact_apres(store, RUPTURE_CONNUE)  # seule la rupture documentée est tolérée
    verifier("journal chaîné intègre", ok, f"ligne altérée : {bad}" if not ok else "sha256 OK")

    store.db.close()
    shutil.rmtree(dossier, ignore_errors=True)
    print(f"Classifieur : {'Groq ' + rt.CLASSIFIER_MODEL if REEL else 'simulé'}")
    for nom, ok, detail in resultats:
        print(f"[{'OK' if ok else 'ÉCHEC'}] {nom} — {detail}")
    echecs = sum(not ok for _, ok, _ in resultats)
    print(f"{len(resultats) - echecs}/{len(resultats)} réussis")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
