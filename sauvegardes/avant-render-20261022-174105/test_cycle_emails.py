"""Tests du cycle quotidien des emails, de la machine à états, du repli et de la synchro du schéma.

Aucun réseau : Telegram, SMTP et modèle simulés. Bases temporaires : rien n'est écrit dans cortex.db
ni dans audit.db de production.   Lancement : python test_cycle_emails.py
"""

import json
import os
import sqlite3
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="cortex_cycle_"))
os.environ["CORTEX_AUDIT_DB"] = str(TMP / "audit_test.db")
os.environ.pop("CYCLE_EMAILS_ACTIF", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))

import cortex as c  # noqa: E402
import cycle_emails as ce  # noqa: E402
import dossier_audit_manager as dam_mod  # noqa: E402
import routage_telegram as rt  # noqa: E402
import schema_sync  # noqa: E402
from test_moteur_audit import CORPS_OK, analyse_fictive, email_complet  # noqa: E402

HUIT_HEURES = datetime(2026, 10, 19, 6, 0, tzinfo=timezone.utc)  # 08:00 à Paris
HORLOGE = [HUIT_HEURES]
c.now = lambda: HORLOGE[0]


class FauxTelegram:
    def __init__(self, store):
        self.enabled, self.chat, self.token, self.store = True, "1", "x", store
        self.envoyes, self.boutons = [], []
        store.tg = self

    def send(self, text, buttons=None):
        self.envoyes.append(text)
        self.boutons.append(buttons)
        return len(self.envoyes)

    def call(self, method, **params):
        return {"ok": True, "result": {}}

    def clear_buttons(self, message_id):
        pass


class FauxSMTP:
    def __init__(self, echecs=0):
        self.envoyes, self.echecs = [], echecs

    def __call__(self, to, subject, body):
        if self.echecs:
            self.echecs -= 1
            raise RuntimeError("envoi impossible (simulé)")
        self.envoyes.append(to)
        return f"<{uuid.uuid4().hex}@josyei.com>"


def environnement(n=12, prix_sur=None, oppose=None):
    store = c.Store(TMP / f"cortex_{uuid.uuid4().hex[:6]}.db")
    tg = FauxTelegram(store)
    cx = c.Cortex(store, tg)
    dam_mod.AUDIT_DB = TMP / f"audit_{uuid.uuid4().hex[:6]}.db"  # base par défaut du chemin bouton réel
    dam = dam_mod.DossierAuditManager(str(dam_mod.AUDIT_DB))
    tid = dam.assurer_tenant("JOSY EI", email_contact="contact@josyei.com", signature=c.SIGNATURE)
    preuves = json.dumps(dam_mod.preuves_depuis_audit(analyse_fictive()), ensure_ascii=False)
    for k in range(n):
        dest = f"contact@prospect{k}.fr"
        did = dam.creer_dossier_audit(tid, {"nom": f"Prospect {k}", "email": dest, "ville": "Montmorillon"})
        corps = CORPS_OK + ("\n\nL'audit complet coûte 49 € par mois." if k == prix_sur else "")
        dam.maj_statut(did, "en_cours", email_valide=1, email_genere=email_complet(corps), preuves_verifiables=preuves)
        if k == oppose:
            store.db.execute("INSERT INTO liste_opposition(siren, email_hash, date_opposition) VALUES('',?,?)",
                             (c.email_hash(dest), c.iso(c.now())))
    store.db.commit()
    return store, tg, cx, dam


RESULTATS = []
L = ce.DAILY_EMAIL_LIMIT  # plafond en vigueur : les tests suivent la décision de JOSY


def verifier(nom, condition, detail=""):
    RESULTATS.append((nom, bool(condition), detail))


def tests_cycle():
    store, tg, cx, dam = environnement(n=L + 22, prix_sur=3, oppose=5)
    verifier(f"plafond lu dans AGENTS.md : {L}", ce.plafond_legislatif() == L == 30, f"{ce.plafond_legislatif()}")
    verifier(f"plafond du jour = DAILY_EMAIL_LIMIT = {L}", ce.plafond_du_jour() == L)
    verifier("pas de lot avant 07:00", not ce.doit_lancer(c, store, datetime(2026, 10, 19, 4, 59, tzinfo=timezone.utc)))
    verifier("lot à partir de 07:00", ce.doit_lancer(c, store, datetime(2026, 10, 19, 5, 1, tzinfo=timezone.utc)))

    lot = ce.cycle(c, cx, dam=dam)
    items = store.db.execute("SELECT statut, motifs FROM lots_emails_items WHERE lot_id=?", (lot,)).fetchall()
    admis = [i for i in items if i["statut"] == "pret"]
    verifier(f"lot : {L} emails admis au plus, 2 écartés, 20 reportés", len(admis) == L and len(items) == L + 2, f"{len(items)} lus")
    verifier("veto zéro prix écarte l'email n°3", any("prix" in (i["motifs"] or "").lower() or "€" in (i["motifs"] or "")
                                                       or "VETO" in (i["motifs"] or "") for i in items
                                                       if i["statut"] == "exclu_veto"), f"{len(items) - len(admis)} écartés")
    verifier("opposition écarte l'email n°5", sum(i["statut"] == "exclu_veto" for i in items) == 2)
    verifier("lot soumis avec 3 boutons InlineKeyboard",
             tg.boutons[-1] and [b["callback_data"].split(":")[0] for b in tg.boutons[-1]] == ["lot_v", "lot_r", "lot_d"])
    detail = ce.resume_lot(c, store, lot, detail=True)
    verifier(f"bouton Détail : le lot de {L} tient dans un message Telegram",
             detail.count("\n• ") == len(admis) == L and len(detail) < 4096, f"{len(detail)} caractères")
    verifier("un seul lot par jour", ce.cycle(c, cx, dam=dam) is None)

    smtp = FauxSMTP()
    r = ce.envoyer_lot(c, store, lot, smtp=smtp, dam=dam)
    verifier("aucun envoi sans validation humaine", r["envoyes"] == 0 and not smtp.envoyes, r["message"])

    # bouton Valider, mode simulation (CYCLE_EMAILS_ACTIF absent) : aucun SMTP
    cx.handle_update({"update_id": 1, "callback_query": {"id": "q", "data": f"lot_v:{lot}",
                                                         "message": {"chat": {"id": 1}}}})
    s = store.db.execute("SELECT COUNT(*) FROM lots_emails_items WHERE lot_id=? AND statut='simule'", (lot,)).fetchone()[0]
    verifier("bouton Valider : simulation, 0 SMTP", s == len(admis) and not smtp.envoyes, tg.envoyes[-1][:90])
    verifier("validation journalisée (HUMAIN)", store.db.execute(
        "SELECT 1 FROM journal WHERE event='lot_emails_valide'").fetchone() is not None)


def tests_actif():
    os.environ["CYCLE_EMAILS_ACTIF"] = "1"
    try:
        store, tg, cx, dam = environnement(n=L + 22)
        lot = ce.cycle(c, cx, dam=dam)
        smtp = FauxSMTP()
        ce.decision_bouton(c, cx, "lot_v", lot, smtp=smtp, dam=dam)
        verifier(f"actif + validé : envoi plafonné à {L}", len(smtp.envoyes) == L, tg.envoyes[-1][:80])
        verifier("dossiers marqués envoyés", dam.db.execute(
            "SELECT COUNT(*) FROM dossiers_audit WHERE email_envoye=1").fetchone()[0] == L)
        verifier("plafond atteint : coupe-circuit", ce.coupe_circuit(c, store) and "plafond" in ce.coupe_circuit(c, store))
        verifier(f"compteur bloquant : can_send_email_today faux après {L}", not ce.can_send_email_today(c, store))
        rep = store.db.execute("SELECT details FROM journal WHERE event='emails_reportes_lendemain'").fetchone()
        verifier("22 emails reportés au lendemain (journal)", rep and json.loads(rep[0]).get("nombre") == 22,
                 rep[0] if rep else "absent")

        # email n° L+1 du jour : 1 premier contact déjà parti par vente.py après la préparation du lot de L
        store, tg, cx, dam = environnement(n=L)
        lot = ce.cycle(c, cx, dam=dam)
        import vente
        store.db.executescript(vente.SCHEMA)
        store.db.execute("INSERT INTO envois(action_id, kind, company, to_email, subject, message_id, sent_at, simule) "
                         "VALUES('x','premier','Autre','contact@autre.fr','s','<m>',?,0)", (c.iso(c.now()),))
        store.db.commit()
        smtp = FauxSMTP()
        ce.decision_bouton(c, cx, "lot_v", lot, smtp=smtp, dam=dam)
        rep = store.db.execute("SELECT COUNT(*) FROM lots_emails_items WHERE lot_id=? AND statut='reporte'",
                               (lot,)).fetchone()[0]
        verifier(f"{L + 1}e email du jour bloqué et reporté", len(smtp.envoyes) == L - 1 and rep == 1, f"{len(smtp.envoyes)} envoyés")
        verifier("alerte Telegram du plafond", ce.MESSAGE_PLAFOND in tg.envoyes[-1], tg.envoyes[-1][-90:])
        verifier("dossier reporté encore éligible demain", dam.db.execute(
            "SELECT COUNT(*) FROM dossiers_audit WHERE email_envoye=0").fetchone()[0] == 1)

        # au-delà de L prospects, les meilleurs scores passent en premier
        store, tg, cx, dam = environnement(n=L + 4)
        store.db.execute("INSERT INTO entreprises(siren, email_contact, score) VALUES('1', ?, 99)",
                         (f"contact@prospect{L + 3}.fr",))
        store.db.commit()
        lot = ce.cycle(c, cx, dam=dam)
        dests = [r[0] for r in store.db.execute("SELECT destinataire FROM lots_emails_items WHERE lot_id=?", (lot,))]
        verifier("meilleur score retenu en tête, autres reportés", dests and dests[0] == f"contact@prospect{L + 3}.fr"
                 and len(dests) == L, f"{dests[:1]}")

        store, tg, cx, dam = environnement(n=4)
        lot = ce.cycle(c, cx, dam=dam)
        store.set("system_status", "arrete")
        smtp = FauxSMTP()
        r = ce.decision_bouton(c, cx, "lot_v", lot, smtp=smtp, dam=dam)
        verifier("coupe-circuit /stop : 0 envoi", not smtp.envoyes and "arrêté" in tg.envoyes[-1], tg.envoyes[-1][:90])

        store, tg, cx, dam = environnement(n=6)
        lot = ce.cycle(c, cx, dam=dam)
        smtp = FauxSMTP(echecs=3)
        ce.decision_bouton(c, cx, "lot_v", lot, smtp=smtp, dam=dam)
        st = store.db.execute("SELECT statut FROM lots_emails WHERE id=?", (lot,)).fetchone()[0]
        verifier("3 erreurs SMTP : lot interrompu", st == "interrompu" and not smtp.envoyes, tg.envoyes[-1][:90])

        store, tg, cx, dam = environnement(n=3)
        lot = ce.cycle(c, cx, dam=dam)
        HORLOGE[0] = datetime(2026, 10, 19, 18, 30, tzinfo=timezone.utc)  # 20:30 à Paris
        smtp = FauxSMTP()
        ce.decision_bouton(c, cx, "lot_v", lot, smtp=smtp, dam=dam)
        verifier("hors plage 07:00-19:00 : 0 envoi", not smtp.envoyes, tg.envoyes[-1][:90])
        HORLOGE[0] = HUIT_HEURES

        store, tg, cx, dam = environnement(n=3)
        lot = ce.cycle(c, cx, dam=dam)
        ce.decision_bouton(c, cx, "lot_r", lot, smtp=smtp, dam=dam)
        verifier("bouton Refuser : rien ne part", not smtp.envoyes and "refusé" in tg.envoyes[-1])

        store, tg, cx, dam = environnement(n=3)
        lot = ce.cycle(c, cx, dam=dam)
        HORLOGE[0] = HUIT_HEURES + timedelta(hours=25)
        smtp = FauxSMTP()
        ce.decision_bouton(c, cx, "lot_v", lot, smtp=smtp, dam=dam)
        verifier("lot expiré après 24 h : refus maintenu", not smtp.envoyes and "expiré" in tg.envoyes[-1])
        HORLOGE[0] = HUIT_HEURES
    finally:
        os.environ.pop("CYCLE_EMAILS_ACTIF", None)


def tests_etats_et_repli():
    store = c.Store(TMP / "etats.db")
    tg = FauxTelegram(store)
    cx = c.Cortex(store, tg)
    machine = rt.EtatConversation(c, store)
    verifier("état initial LIBRE", machine.lire()[0] == "libre")
    machine.passer(machine.ATTENTE_CONFIRMATION, {"intent": "sector_query", "action": "une analyse OSINT",
                                                  "sector": "garages", "location": "Poitiers"}, "test")
    verifier("LIBRE -> ATTENTE_CONFIRMATION", machine.lire()[0] == "attente_confirmation")
    verifier("autre message : proposition abandonnée",
             rt.traiter_confirmation(c, cx, "parle-moi d'autre chose") is None and machine.lire()[0] == "libre")
    machine.passer(machine.ATTENTE_CONFIRMATION, {"intent": "sector_query", "action": "x"}, "test")
    HORLOGE[0] = HUIT_HEURES + timedelta(minutes=11)
    verifier("expiration après 10 min", machine.lire()[0] == "libre")
    HORLOGE[0] = HUIT_HEURES
    machine.CLE_SAUVE = None
    machine.TRANSITIONS = {"libre": {"libre"}, "attente_confirmation": {"libre"}}
    verifier("transition non prévue refusée", machine.passer("attente_confirmation") is False)
    verifier("transitions journalisées", store.db.execute(
        "SELECT COUNT(*) FROM journal WHERE event='etat_conversation'").fetchone()[0] >= 3)

    c.llm_chat = lambda *a, **k: None  # tous les modèles muets (quota, réseau)
    c.LLM_CHAIN = c.LLM_CHAIN or [{"name": "faux", "model": "faux"}]
    import fondateur
    fondateur.capturer = lambda *a, **k: False
    cx.chat_count = 0
    cx.handle_update({"update_id": 2, "message": {"chat": {"id": 1}, "text": "Que penses-tu de l'IA cette année ?",
                                                  "date": 0}})
    verifier("repli quand le modèle échoue", "Je ne peux pas formuler" in tg.envoyes[-1] and "/etat" in tg.envoyes[-1],
             tg.envoyes[-1][:100])


def tests_schema():
    chemin = TMP / "ancienne.db"
    db = sqlite3.connect(chemin)
    db.execute("CREATE TABLE lots_emails (id TEXT PRIMARY KEY, jour TEXT)")
    db.execute("INSERT INTO lots_emails VALUES('a', '2026-10-18')")
    db.commit()
    db.close()
    sim = schema_sync.synchroniser(chemin, scripts=[ce.SCHEMA])
    cols = [r[1] for r in sqlite3.connect(chemin).execute("PRAGMA table_info(lots_emails)")]
    verifier("synchro en simulation : rien d'écrit", sim["ajoutees"] and cols == ["id", "jour"], f"{len(sim['ajoutees'])} à ajouter")
    app = schema_sync.synchroniser(chemin, appliquer=True, scripts=[ce.SCHEMA])
    con = sqlite3.connect(chemin)
    cols = [r[1] for r in con.execute("PRAGMA table_info(lots_emails)")]
    verifier("synchro : ALTER TABLE ADD COLUMN uniquement", all(o.startswith("ALTER TABLE") and "DROP" not in o
                                                                 for o in app["ajoutees"]) and "statut" in cols)
    verifier("synchro : données conservées", con.execute("SELECT jour FROM lots_emails WHERE id='a'").fetchone()[0]
             == "2026-10-18")
    verifier("synchro : table absente signalée, pas créée", "lots_emails_items" in app["tables_absentes"]
             and not con.execute("SELECT 1 FROM sqlite_master WHERE name='lots_emails_items'").fetchone())


def main():
    for t in (tests_cycle, tests_actif, tests_etats_et_repli, tests_schema):
        try:
            t()
        except Exception as exc:
            import traceback
            traceback.print_exc()
            RESULTATS.append((t.__name__, False, f"exception {type(exc).__name__}: {exc}"))
    for nom, ok, detail in RESULTATS:
        print(f"[{'OK' if ok else 'ÉCHEC'}] {nom}" + (f" — {detail}" if detail else ""))
    echecs = sum(not ok for _, ok, _ in RESULTATS)
    print(f"{len(RESULTATS) - echecs}/{len(RESULTATS)} réussis")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
