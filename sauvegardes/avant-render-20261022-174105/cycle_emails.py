"""Cycle quotidien des emails d'audit : un lot par jour, validé en entier par JOSY sur Telegram.

PRÉPARÉ, NON ACTIVÉ. Rien ne part tant que :
  1. la variable CYCLE_EMAILS_ACTIF=1 n'est pas posée dans .env (absente : simulation, aucun SMTP) ;
  2. le cycle n'est pas branché (cortex.run ne l'appelle pas ; tâche Windows non créée) ;
  3. JOSY n'a pas appuyé sur « Valider le lot » (bouton InlineKeyboard, jamais une commande automatique).

Déroulé :
  07:00 (Europe/Paris)  preparer_lot : jusqu'à TAILLE_LOT dossiers d'audit admis (email_valide=1), chaque email
                        repassé au veto du judiciaire (ReglesAbsolues.motifs), puis veto du lot lui-même ;
                        soumission sur Telegram avec trois boutons : Valider le lot / Refuser / Détail.
  Bouton « Valider »    decision_bouton -> statut valide -> envoyer_lot, sous coupe-circuits.
  Sans décision 24 h    le lot expire (refus automatique, matrice R2).

Coupe-circuits (le premier qui saute arrête l'envoi, le reste du lot reste non envoyé) :
  - /stop (system_status = arrete, I9) ;
  - fichier STOP_EMAILS présent dans le dossier du Cortex (arrêt manuel sans Telegram) ;
  - plafond du jour atteint : DAILY_EMAIL_LIMIT = 30 (et plafond d'AGENTS.md), compté sur tous les envois
    réels du jour (lots + vente.py) ; le reste est reporté au lendemain avec l'alerte MESSAGE_PLAFOND ;
  - hors plage d'envoi 07:00-19:00 Europe/Paris ;
  - 3 erreurs SMTP consécutives ;
  - liste d'opposition ou exclusion rencontrée au dernier moment (l'email est sauté, pas envoyé) ;
  - nouveau veto du judiciaire juste avant l'envoi (l'email est sauté).

Plafond : 30 emails/jour (Option B, décision JOSY du 19/10/2026 à 10:29), en constante DAILY_EMAIL_LIMIT et
dans AGENTS.md ; le plus bas des deux s'applique. Au-delà de 30 prospects, les 30 meilleurs (score de l'annuaire)
forment le lot, les autres sont reportés au lendemain.

Planification préparée, non créée :
  schtasks /Create /TN "JOSY EI Cortex Lot emails" /SC DAILY /ST 07:00 ^
    /TR "\"C:\\Users\\JOSY EI\\AppData\\Local\\Programs\\Python\\Python312\\pythonw.exe\" \"C:\\Users\\JOSY EI\\cortex\\cycle_emails.py\""
"""

import json
import os
import re
import sys
import uuid
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Décision JOSY 19/10/2026 (10:29) : Option B, plafond verrouillé à 30 emails/jour (remplace 10/jour de 10:01).
DAILY_EMAIL_LIMIT = 30
TAILLE_LOT = DAILY_EMAIL_LIMIT  # le lot soumis sur Telegram ne dépasse jamais le plafond
MESSAGE_PLAFOND = f"⚠️ Plafond de {DAILY_EMAIL_LIMIT} emails/jour atteint. Les emails restants seront reportés à demain."
HEURE_LOT = (7, 0)            # 07:00 Europe/Paris
PLAGE_ENVOI = (7, 19)         # envoi autorisé de 07:00 à 19:00
EXPIRATION_H = 24             # matrice R2 : refus automatique après 24 h
ERREURS_MAX = 3               # erreurs SMTP consécutives avant arrêt
BASE_DIR = Path(__file__).resolve().parent
STOP_FICHIER = BASE_DIR / "STOP_EMAILS"

SCHEMA = """
CREATE TABLE IF NOT EXISTS lots_emails (
    id TEXT PRIMARY KEY, jour TEXT, statut TEXT, cree_le TEXT, decide_le TEXT, decision_source TEXT,
    tg_message_id INTEGER, nb INTEGER, envoyes INTEGER DEFAULT 0, motifs_veto TEXT);
CREATE TABLE IF NOT EXISTS lots_emails_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT, lot_id TEXT, dossier_id TEXT, destinataire TEXT, objet TEXT,
    corps TEXT, statut TEXT, motifs TEXT, envoye_le TEXT, message_id TEXT, erreur TEXT);
"""
# Statuts du lot : attente_validation, valide, refuse, expire, rejete_veto, envoi_en_cours, envoye, interrompu
# Statuts d'un email : pret, exclu_veto, envoye, simule, saute_veto, saute_opposition, erreur, non_envoye


def actif():
    return os.environ.get("CYCLE_EMAILS_ACTIF", "").strip() == "1"


def plafond_legislatif(agents_path=None):
    """« N premiers emails par jour » dans AGENTS.md ; 10 si introuvable (valeur la plus prudente connue)."""
    try:
        texte = Path(agents_path or BASE_DIR / "AGENTS.md").read_text(encoding="utf-8")
        m = re.search(r"(\d+)\s+premiers emails par jour", texte)
        return int(m.group(1)) if m else 10
    except OSError:
        return 10


def plafond_du_jour():
    """Le plus bas de : constante DAILY_EMAIL_LIMIT, taille du lot, plafond d'AGENTS.md."""
    return min(DAILY_EMAIL_LIMIT, TAILLE_LOT, plafond_legislatif())


def preparer_schema(store):
    store.db.executescript(SCHEMA)
    store.db.commit()


def _paris(m, dt=None):
    return (dt or m.now()).astimezone(m.PARIS)


def jour(m, dt=None):
    return _paris(m, dt).date().isoformat()


def doit_lancer(m, store, dt=None):
    """Vrai à partir de 07:00 Paris s'il n'existe encore aucun lot pour ce jour."""
    p = _paris(m, dt)
    if (p.hour, p.minute) < HEURE_LOT:
        return False
    preparer_schema(store)
    return not store.db.execute("SELECT 1 FROM lots_emails WHERE jour=?", (jour(m, dt),)).fetchone()


def _objet_corps(email):
    lignes = (email or "").strip().splitlines()
    if lignes and re.match(r"\s*Objet\s*:", lignes[0], re.I):
        return lignes[0].split(":", 1)[1].strip(), "\n".join(lignes[1:]).strip()
    return "Votre visibilité en ligne", (email or "").strip()  # jamais « gratuit » dans l'objet (anti-spam)


def _oppose(m, store, email):
    return bool(store.db.execute("SELECT 1 FROM liste_opposition WHERE email_hash=?",
                                 (m.email_hash(email),)).fetchone())


def deja_envoyes_aujourdhui(m, store, dt=None):
    """Emails réellement envoyés depuis minuit (Paris), tous chemins confondus : lots du cycle et
    file d'envoi de vente.py (premiers contacts non simulés). C'est le compteur bloquant (I11)."""
    preparer_schema(store)
    debut = m.iso(_paris(m, dt).replace(hour=0, minute=0, second=0, microsecond=0))
    n = store.db.execute("SELECT COUNT(*) FROM lots_emails_items WHERE statut='envoye' AND envoye_le>=?",
                         (debut,)).fetchone()[0]
    try:
        n += store.db.execute("SELECT COUNT(*) FROM envois WHERE sent_at>=? AND kind='premier' "
                              "AND COALESCE(simule,0)=0", (debut,)).fetchone()[0]
    except Exception:  # table envois absente : pas encore d'envoi par vente.py
        pass
    return n


def can_send_email_today(m, store, dt=None):
    """Compteur bloquant : faux dès que DAILY_EMAIL_LIMIT (et le plafond d'AGENTS.md) est atteint."""
    return deja_envoyes_aujourdhui(m, store, dt) < plafond_du_jour()


def _score(store, email):
    """Score du prospect dans l'annuaire (entreprises.score) ; 0 s'il est inconnu."""
    try:
        r = store.db.execute("SELECT MAX(COALESCE(score,0)) FROM entreprises WHERE lower(email_contact)=?",
                             (email.lower(),)).fetchone()
        return float(r[0] or 0)
    except Exception:
        return 0.0


def veto_lot(items, plafond):
    """Veto du judiciaire sur le lot entier (en plus du veto de chaque email)."""
    motifs = []
    admis = [i for i in items if i["statut"] == "pret"]
    if not admis:
        motifs.append("VETO LOT: aucun email admis")
    if len(admis) > plafond:
        motifs.append(f"VETO LOT: {len(admis)} emails pour un plafond de {plafond}")
    vus = [i["destinataire"].lower() for i in admis]
    if len(vus) != len(set(vus)):
        motifs.append("VETO LOT: destinataire en double")
    domaines = [d.split("@")[-1] for d in vus]
    if any(domaines.count(d) > 1 for d in set(domaines)):
        motifs.append("VETO LOT: plusieurs emails vers le même domaine")
    return motifs


def preparer_lot(m, store, dam, dt=None):
    """Construit le lot du jour. Renvoie son identifiant, ou None si rien n'est à soumettre."""
    import regles_absolues
    preparer_schema(store)
    plafond = max(0, plafond_du_jour() - deja_envoyes_aujourdhui(m, store, dt))
    rows = dam.db.execute(
        "SELECT id, prospect_email FROM dossiers_audit WHERE email_valide=1 AND email_envoye=0 "
        "AND COALESCE(email_genere,'')<>'' AND COALESCE(prospect_email,'')<>'' "
        "AND statut IN ('en_cours','attente_validation') ORDER BY created_at").fetchall()
    # les meilleurs d'abord (score de l'annuaire, puis ancienneté) ; au-delà du plafond, reportés au lendemain
    rows = sorted(rows, key=lambda r: -_score(store, r["prospect_email"]))
    items, admis_n, reportes = [], 0, 0
    for r in rows:
        if admis_n >= plafond:
            reportes += 1
            continue
        d = dam.obtenir(r["id"])
        dest = d["prospect_email"].strip()
        motifs = regles_absolues.ReglesAbsolues.motifs(d["email_genere"], dam.contexte_validation(d["id"]))
        if _oppose(m, store, dest) or dam.est_exclu(email=dest, site=d.get("prospect_site_web")):
            motifs.append("VETO: opposition ou exclusion")
        objet, corps = _objet_corps(d["email_genere"])
        items.append({"dossier_id": d["id"], "destinataire": dest, "objet": objet, "corps": corps,
                      "statut": "exclu_veto" if motifs else "pret", "motifs": motifs})
        admis_n += not motifs
    if reportes:
        store.log("EXECUTIF", "emails_reportes_lendemain", details={"nombre": reportes, "plafond": plafond})
    if not items:
        store.log("JUDICIAIRE", "lot_emails_vide", details={"plafond": plafond})
        return None
    lot_id = uuid.uuid4().hex[:12]
    motifs_lot = veto_lot(items, plafond)
    statut = "rejete_veto" if motifs_lot else "attente_validation"
    admis = sum(i["statut"] == "pret" for i in items)
    store.db.execute("INSERT INTO lots_emails(id, jour, statut, cree_le, nb, motifs_veto) VALUES(?,?,?,?,?,?)",
                     (lot_id, jour(m, dt), statut, m.iso(m.now()), admis, json.dumps(motifs_lot, ensure_ascii=False)))
    store.db.executemany(
        "INSERT INTO lots_emails_items(lot_id, dossier_id, destinataire, objet, corps, statut, motifs) "
        "VALUES(?,?,?,?,?,?,?)",
        [(lot_id, i["dossier_id"], i["destinataire"], i["objet"], i["corps"], i["statut"],
          json.dumps(i["motifs"], ensure_ascii=False)) for i in items])
    store.db.commit()
    store.log("JUDICIAIRE", "lot_emails_prepare", details={"lot": lot_id, "admis": admis,
                                                          "exclus": len(items) - admis, "veto_lot": motifs_lot})
    return lot_id


def boutons(lot_id):
    return [{"text": "✅ Valider le lot", "callback_data": f"lot_v:{lot_id}"},
            {"text": "❌ Refuser", "callback_data": f"lot_r:{lot_id}"},
            {"text": "👁 Détail", "callback_data": f"lot_d:{lot_id}"}]


def resume_lot(m, store, lot_id, detail=False):
    import html
    lot = store.db.execute("SELECT * FROM lots_emails WHERE id=?", (lot_id,)).fetchone()
    if not lot:
        return "Lot introuvable."
    items = store.db.execute("SELECT * FROM lots_emails_items WHERE lot_id=? ORDER BY id", (lot_id,)).fetchall()
    admis = [i for i in items if i["statut"] in ("pret", "envoye", "simule", "non_envoye")]
    lignes = [f"📬 <b>Lot d'emails du {lot['jour']}</b> · {len(admis)} email(s) admis"
              f" · {len(items) - len(admis)} écarté(s) par le judiciaire · statut : {lot['statut']}"]
    for i in admis[:(30 if detail else 5)]:
        lignes.append(f"• {html.escape(i['destinataire'].split('@')[-1])} : {html.escape(i['objet'][:70])}")
    if not detail and len(admis) > 5:
        lignes.append(f"… et {len(admis) - 5} autre(s). « Détail » pour tout voir.")
    if lot["statut"] == "attente_validation":
        lignes.append(f"Sans décision : refus automatique dans {EXPIRATION_H} h."
                      + ("" if actif() else " Mode simulation : aucun email ne partira."))
    return "\n".join(lignes)[:4000]


def soumettre(m, cx, lot_id):
    """Envoie le résumé du lot à JOSY avec les boutons. Ne valide rien."""
    msg_id = cx.tg.send(resume_lot(m, cx.s, lot_id), buttons=boutons(lot_id))
    cx.s.db.execute("UPDATE lots_emails SET tg_message_id=? WHERE id=?", (msg_id, lot_id))
    cx.s.db.commit()
    cx.s.log("EXECUTIF", "lot_emails_soumis", details={"lot": lot_id})


def expirer(m, store):
    preparer_schema(store)
    limite = m.iso(m.now() - timedelta(hours=EXPIRATION_H))
    n = store.db.execute("UPDATE lots_emails SET statut='expire', decide_le=?, decision_source='timeout' "
                         "WHERE statut='attente_validation' AND cree_le<?", (m.iso(m.now()), limite)).rowcount
    store.db.commit()
    if n:
        store.log("SYSTEME", "lot_emails_expire", details={"nombre": n})
    return n


def decision_bouton(m, cx, verbe, lot_id, smtp=None, dam=None):
    """Bouton Telegram de JOSY (le chat est déjà vérifié par Cortex.handle_update)."""
    preparer_schema(cx.s)
    lot = cx.s.db.execute("SELECT * FROM lots_emails WHERE id=?", (lot_id,)).fetchone()
    if not lot:
        cx.tg.send("Lot introuvable.")
        return
    if verbe == "lot_d":
        cx.tg.send(resume_lot(m, cx.s, lot_id, detail=True))
        return
    if lot["statut"] != "attente_validation":
        cx.tg.send(f"Ce lot est déjà au statut « {lot['statut']} ».")
        return
    expirer(m, cx.s)
    if cx.s.db.execute("SELECT statut FROM lots_emails WHERE id=?", (lot_id,)).fetchone()[0] == "expire":
        cx.tg.send("⌛ Ce lot avait expiré : refus automatique maintenu.")
        return
    statut = "valide" if verbe == "lot_v" else "refuse"
    cx.s.db.execute("UPDATE lots_emails SET statut=?, decide_le=?, decision_source='bouton' WHERE id=?",
                    (statut, m.iso(m.now()), lot_id))
    cx.s.db.commit()
    cx.s.log("HUMAIN", "lot_emails_" + statut, details={"lot": lot_id})
    if lot["tg_message_id"]:
        cx.tg.clear_buttons(lot["tg_message_id"])
    if statut == "refuse":
        cx.tg.send("❌ Lot refusé : aucun email ne partira.")
        return
    bilan = envoyer_lot(m, cx.s, lot_id, smtp=smtp, dam=dam)
    cx.tg.send(bilan["message"])


def coupe_circuit(m, store, dt=None):
    """Motif d'arrêt, ou None si l'envoi peut continuer."""
    if store.get("system_status", "actif") == "arrete":
        return "Cortex arrêté (/stop)"
    if STOP_FICHIER.exists():
        return "fichier STOP_EMAILS présent"
    h = _paris(m, dt).hour
    if not (PLAGE_ENVOI[0] <= h < PLAGE_ENVOI[1]):
        return "hors plage d'envoi 07:00-19:00"
    if not can_send_email_today(m, store, dt):
        return f"plafond du jour atteint ({plafond_du_jour()})"
    return None


def envoyer_lot(m, store, lot_id, smtp=None, dam=None, dt=None):
    """Envoie un lot validé par bouton. SMTP seulement si CYCLE_EMAILS_ACTIF=1 ; sinon simulation."""
    import regles_absolues
    lot = store.db.execute("SELECT * FROM lots_emails WHERE id=?", (lot_id,)).fetchone()
    if not lot or lot["statut"] != "valide" or lot["decision_source"] != "bouton":
        store.log("JUDICIAIRE", "lot_emails_envoi_refuse", details={"lot": lot_id, "raison": "non valide par JOSY"})
        return {"envoyes": 0, "message": "Envoi refusé : le lot n'a pas été validé par toi."}
    reel = actif()
    if reel and smtp is None:
        import email_sender
        smtp = email_sender.send_email
    if dam is None:
        import dossier_audit_manager
        dam = dossier_audit_manager.DossierAuditManager()
    store.db.execute("UPDATE lots_emails SET statut='envoi_en_cours' WHERE id=?", (lot_id,))
    store.db.commit()
    envoyes, erreurs_suite, arret = 0, 0, None
    for it in store.db.execute("SELECT * FROM lots_emails_items WHERE lot_id=? AND statut='pret' ORDER BY id",
                               (lot_id,)).fetchall():
        arret = coupe_circuit(m, store, dt)
        if arret:
            break
        dest = it["destinataire"]
        if _oppose(m, store, dest) or dam.est_exclu(email=dest):
            store.db.execute("UPDATE lots_emails_items SET statut='saute_opposition' WHERE id=?", (it["id"],))
            continue
        email = f"Objet : {it['objet']}\n\n{it['corps']}"
        motifs = (regles_absolues.ReglesAbsolues.motifs(email, dam.contexte_validation(it["dossier_id"]))
                  if dam.obtenir(it["dossier_id"]) else ["VETO: dossier d'audit introuvable"])
        if motifs:  # le dossier a pu changer depuis la préparation : nouveau veto, email sauté
            store.db.execute("UPDATE lots_emails_items SET statut='saute_veto', motifs=? WHERE id=?",
                             (json.dumps(motifs, ensure_ascii=False), it["id"]))
            continue
        if not reel:
            store.db.execute("UPDATE lots_emails_items SET statut='simule', envoye_le=? WHERE id=?",
                             (m.iso(m.now()), it["id"]))
            store.log("EXECUTIF", "email_lot_simule", details={"lot": lot_id, "item": it["id"]})
            continue
        try:
            mid = smtp(dest, it["objet"], it["corps"])
        except Exception as exc:  # email_sender.EmailError : message sans secret
            erreurs_suite += 1
            store.db.execute("UPDATE lots_emails_items SET statut='erreur', erreur=? WHERE id=?",
                             (str(exc)[:200], it["id"]))
            store.log("EXECUTIF", "email_lot_erreur", details={"lot": lot_id, "item": it["id"], "erreur": str(exc)[:200]})
            if erreurs_suite >= ERREURS_MAX:
                arret = f"{ERREURS_MAX} erreurs SMTP consécutives"
                break
            continue
        erreurs_suite = 0
        envoyes += 1
        store.db.execute("UPDATE lots_emails_items SET statut='envoye', envoye_le=?, message_id=? WHERE id=?",
                         (m.iso(m.now()), mid, it["id"]))
        dam.maj_statut(it["dossier_id"], "envoye", email_envoye=1, date_envoi=m.iso(m.now()))
        store.log("EXECUTIF", "email_lot_envoye", details={"lot": lot_id, "item": it["id"]})
        store.db.commit()
    plafond_atteint = bool(arret and arret.startswith("plafond"))
    # plafond : le reste est reporté (dossier toujours éligible demain) ; autre arrêt : non envoyé
    store.db.execute("UPDATE lots_emails_items SET statut=? WHERE lot_id=? AND statut='pret'",
                     ("reporte" if plafond_atteint else "non_envoye", lot_id))
    if plafond_atteint:
        store.log("EXECUTIF", "plafond_emails_atteint", details={"lot": lot_id, "plafond": plafond_du_jour()})
    final = "interrompu" if arret else "envoye"
    store.db.execute("UPDATE lots_emails SET statut=?, envoyes=? WHERE id=?", (final, envoyes, lot_id))
    store.db.commit()
    store.log("EXECUTIF", "lot_emails_" + final, details={"lot": lot_id, "envoyes": envoyes, "arret": arret,
                                                          "simulation": not reel})
    simules = store.db.execute("SELECT COUNT(*) FROM lots_emails_items WHERE lot_id=? AND statut='simule'",
                               (lot_id,)).fetchone()[0]
    msg = (f"📤 Lot {lot_id} : {envoyes} envoyé(s)" if reel else f"🧪 Simulation : {simules} email(s) auraient été envoyés")
    if plafond_atteint:
        msg += ".\n" + MESSAGE_PLAFOND
    elif arret:
        msg += f". Arrêt : {arret}. Le reste du lot n'est pas parti."
    return {"envoyes": envoyes, "simules": simules, "arret": arret, "message": msg}


def etat_lot(m, store):
    preparer_schema(store)
    lot = store.db.execute("SELECT id FROM lots_emails ORDER BY cree_le DESC LIMIT 1").fetchone()
    entete = (f"Cycle des emails : {'ACTIF' if actif() else 'simulation (CYCLE_EMAILS_ACTIF absent)'} · "
              f"plafond du jour {plafond_du_jour()}\n")
    return entete + (resume_lot(m, store, lot["id"]) if lot else "Aucun lot préparé.")


def cycle(m, cx, dam=None, dt=None):
    """Passage planifié : expire les lots, prépare et soumet le lot du jour s'il est 07:00 passé."""
    expirer(m, cx.s)
    if cx.s.get("system_status", "actif") == "arrete" or not doit_lancer(m, cx.s, dt):
        return None
    if dam is None:
        import dossier_audit_manager
        dam = dossier_audit_manager.DossierAuditManager()
    lot_id = preparer_lot(m, cx.s, dam, dt)
    if lot_id and cx.s.db.execute("SELECT statut FROM lots_emails WHERE id=?", (lot_id,)).fetchone()[0] \
            == "attente_validation":
        soumettre(m, cx, lot_id)
    return lot_id


if __name__ == "__main__":  # lancement planifié (tâche Windows, non créée)
    import cortex
    store = cortex.Store(cortex.DB_PATH)
    tg = cortex.Telegram(cortex.TG_TOKEN, cortex.TG_CHAT, store)
    cycle(cortex, cortex.Cortex(store, tg))
