"""Missions de vente du Cortex : envoi après clic, réponses, relances, leads chauds.

Émetteur unique : contact@josyei.com (Hostinger). Règles :
  - chaque email de prospection est soumis à JOSY sur Telegram (/valider ID) avant l'envoi ;
  - textes fixes (offre, prix, lien, signature), relus par le judiciaire avant envoi ;
  - 10 premiers emails par jour au plus, liste d'opposition respectée, « répondre STOP »
    et en-tête List-Unsubscribe dans chaque email ;
  - tant que HOSTINGER_EMAIL / HOSTINGER_PASSWORD manquent dans .env : SIMULATION
    (rien ne part, l'email est écrit dans envois_simules\\).
"""

import email
import email.policy
import imaplib
import json
import os
import re
import smtplib
import ssl
import uuid
from datetime import timedelta
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr

MAIL_USER = os.environ.get("HOSTINGER_EMAIL", "").strip()
MAIL_PASSWORD = os.environ.get("HOSTINGER_PASSWORD", "").strip()
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.hostinger.com")
IMAP_HOST = os.environ.get("IMAP_HOST", "imap.hostinger.com")

MAX_FIRST_EMAILS_PER_DAY = 10   # plafond fixé par JOSY (13/10/2026)
MAX_FOLLOWUPS_PER_DAY = 10
INBOX_EVERY_MIN = 15
RELANCE_DAYS = (3, 7)

SCHEMA = """
CREATE TABLE IF NOT EXISTS file_envoi (
  id INTEGER PRIMARY KEY AUTOINCREMENT, action_id TEXT, kind TEXT, company TEXT,
  to_email TEXT, subject TEXT, body TEXT, in_reply_to TEXT, parent_envoi INTEGER,
  statut TEXT DEFAULT 'en_file', cree_le TEXT);
CREATE TABLE IF NOT EXISTS envois (
  id INTEGER PRIMARY KEY AUTOINCREMENT, action_id TEXT, kind TEXT, company TEXT,
  to_email TEXT, subject TEXT, message_id TEXT, in_reply_to TEXT, parent_envoi INTEGER,
  sent_at TEXT, simule INTEGER, relance_n INTEGER DEFAULT 0, repondu INTEGER DEFAULT 0,
  classe TEXT);
CREATE TABLE IF NOT EXISTS reponses (
  message_id TEXT PRIMARY KEY, envoi_id INTEGER, from_hash TEXT, classe TEXT,
  resume TEXT, recu_le TEXT);
"""

# Zéro contact direct (règle de JOSY) : ni appel, ni visio, ni rendez-vous. Tout par email.
RELANCE_TEXTS = {
    1: ("Bonjour,\n\nJe me permets de revenir vers vous au sujet de mon message de la semaine "
        "dernière.\n\nSi vous souhaitez en savoir plus, répondez directement à cet email.\n\n{signature}"),
    2: ("Bonjour,\n\nDernier message de ma part sur ce sujet. Si cela vous intéresse plus tard, "
        "il suffit de répondre à cet email.\n\n{signature}"),
}
FORBIDDEN_CONTACT = re.compile(r"t[ée]l[ée]phon|appel|visio|rendez[- ]vous|\brdv\b|[ée]change de \d+|"
                               r"cr[ée]neau|rencontr|prenons contact|\d{2}[ .]?\d{2}[ .]?\d{2}[ .]?\d{2}",
                               re.IGNORECASE)
REPLY_PROMPT = (
    "Tu rédiges 3 réponses courtes possibles (4 à 6 lignes chacune, vouvoiement, ton sobre) "
    "à l'email d'un prospect qui a répondu à JOSY EI (conseil en visibilité en ligne, IA, RGPD, "
    "sauvegardes et automatisation pour TPE/PME ; produit : Le Cortex, employé IA pour site web, Google Business et boutique en ligne). Règles absolues : tout se fait par email ; "
    "ne propose JAMAIS d'appel, de visio, de rendez-vous ni de créneau ; aucun prix inventé "
    "(seuls prix possibles : formules du Cortex Gratuit 0 €, Découverte 9,99 €/mois, "
    "Starter 14,99 €/mois, Pro 19,99 €/mois HT avec essai gratuit de 3 jours sans paiement à l'inscription) ; "
    "n'invente aucun fait ; ne décris pas le contenu d'une prestation au-delà de son nom ; "
    "ne mentionne aucune pièce jointe ; pas de signature. Proposition 1 : réponse directe à sa question. "
    "Proposition 2 : demande des précisions par email. Proposition 3 : explique en deux phrases "
    "ce que Le Cortex ferait pour son site web, sa fiche Google Business ou sa boutique en ligne. Réponds en JSON : {\"propositions\": [\"...\", \"...\", \"...\"]}"
)
SIGN_REPLY = "\n\n{signature}"

STOP_RE = re.compile(r"\bstop\b|d[ée]sinscri|ne plus (me |nous )?(contacter|[ée]crire)|"
                     r"unsubscribe|retirez|supprimez", re.IGNORECASE)
AUTO_RE = re.compile(r"absen|out of office|r[ée]ponse automatique|auto[- ]?reply|"
                     r"cong[ée]s|delivery status|mail delivery|undeliverable", re.IGNORECASE)
NO_RE = re.compile(r"pas int[ée]ress|non merci|pas besoin|aucun besoin|pas le moment|"
                   r"d[ée]j[àa] un prestataire", re.IGNORECASE)
HOT_RE = re.compile(r"combien|tarif|\bprix\b|devis|rdv|rendez[- ]vous|rappel|appele[rz]|"
                    r"plus d'info|en savoir plus|int[ée]ress[ée]|disponibilit|cr[ée]neau",
                    re.IGNORECASE)


def setup(store):
    store.db.executescript(SCHEMA)
    store.db.commit()


def mail_mode():
    return "reel" if MAIL_USER and MAIL_PASSWORD else "simulation"


def _message(c, to, subject, body, in_reply_to=None):
    msg = EmailMessage()
    msg["From"] = f"JOSY EI <{c.SENDER_EMAIL}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="josyei.com")
    msg["List-Unsubscribe"] = f"<mailto:{c.SENDER_EMAIL}?subject=STOP>"
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    msg.set_content(body)
    return msg


def deliver(c, msg):
    if mail_mode() == "simulation":
        out = c.BASE_DIR / "envois_simules"
        out.mkdir(exist_ok=True)
        (out / f"{c.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}.eml").write_bytes(bytes(msg))
        return
    with smtplib.SMTP_SSL(SMTP_HOST, 465, context=ssl.create_default_context(), timeout=30) as s:
        s.login(MAIL_USER, MAIL_PASSWORD)
        s.send_message(msg)


def queue_from_proposal(c, cortex, p, quiet=False):
    """Validé (clic de JOSY, ou envoi automatique après son premier /valider) : en file d'envoi."""
    db = cortex.s.db
    items = p.get("items") or [{"to": p["target"]["email"], "subject": p["content"]["subject"],
                                "body": p["content"]["body"], "in_reply_to": p.get("in_reply_to"),
                                "parent": p.get("parent_envoi"), "company": p["target"]["company"]}]
    kind = {"cold_email": "premier", "relance": "relance", "proposition_rdv": "rdv",
            "reponse": "reponse", "diagnostic": "diagnostic"}[p["action_type"]]
    for it in items:
        db.execute("INSERT INTO file_envoi(action_id, kind, company, to_email, subject, body, "
                   "in_reply_to, parent_envoi, cree_le) VALUES(?,?,?,?,?,?,?,?,?)",
                   (p["action_id"], kind, it["company"], it["to"], it["subject"], it["body"],
                    it.get("in_reply_to"), it.get("parent"), c.iso(c.now())))
    db.execute("UPDATE proposals SET status='valide_en_file' WHERE action_id=?", (p["action_id"],))
    db.commit()
    cortex.s.log("EXECUTIF", "envoi_mis_en_file", p["action_id"], {"emails": len(items), "type": kind})


def process_queue(c, cortex):
    db, s = cortex.s.db, cortex.s
    opposed = {h for (h,) in db.execute("SELECT email_hash FROM liste_opposition")}
    sent = {"premier": s.count_today("SELECT COUNT(*) FROM envois WHERE sent_at>=? AND kind='premier'"),
            "suivi": s.count_today("SELECT COUNT(*) FROM envois WHERE sent_at>=? AND kind!='premier'")}
    for row in db.execute("SELECT * FROM file_envoi WHERE statut='en_file' ORDER BY id").fetchall():
        bucket = "premier" if row["kind"] == "premier" else "suivi"
        if sent[bucket] >= (MAX_FIRST_EMAILS_PER_DAY if bucket == "premier" else MAX_FOLLOWUPS_PER_DAY):
            continue  # reste en file pour demain
        reason = None
        if c.email_hash(row["to_email"]) in opposed:
            reason = "annule_opposition"
        elif (c.PERSONAL_RE.search(row["body"]) or "STOP" not in row["body"]
              or FORBIDDEN_CONTACT.search(row["body"].split("LE CORTEX par JOSY EI")[0])
              or (row["kind"] == "premier" and (_bad_price(c, row["body"])
                                                 or len(row["body"].splitlines()) > 15))):
            reason = "annule_judiciaire"  # données perso, pas de STOP, appel/RDV, prix ou email trop long
        if reason:
            db.execute("UPDATE file_envoi SET statut=? WHERE id=?", (reason, row["id"]))
            s.log("JUDICIAIRE", reason, row["action_id"])
            db.commit()
            continue
        msg = _message(c, row["to_email"], row["subject"], row["body"], row["in_reply_to"])
        try:
            deliver(c, msg)
        except Exception as exc:
            s.log("EXECUTIF", "envoi_erreur", row["action_id"], {"erreur": c.safe_error(exc)})
            c.alert(s, "envoi", c.safe_error(exc))
            break
        db.execute("INSERT INTO envois(action_id, kind, company, to_email, subject, message_id, "
                   "in_reply_to, parent_envoi, sent_at, simule) VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (row["action_id"], row["kind"], row["company"], row["to_email"], row["subject"],
                    msg["Message-ID"], row["in_reply_to"], row["parent_envoi"], c.iso(c.now()),
                    int(mail_mode() == "simulation")))
        db.execute("UPDATE file_envoi SET statut='envoye' WHERE id=?", (row["id"],))
        if row["kind"] == "relance" and row["parent_envoi"]:
            db.execute("UPDATE envois SET relance_n=relance_n+1 WHERE id=?", (row["parent_envoi"],))
        db.execute("UPDATE entreprises SET statut='contacte', dernier_contact=? "
                   "WHERE lower(email_contact)=?", (c.iso(c.now()), row["to_email"].lower()))
        db.commit()
        sent[bucket] += 1
        s.log("EXECUTIF", "email_envoye" if mail_mode() == "reel" else "email_simule",
              row["action_id"], {"type": row["kind"]})
        cortex.tg.send(f"📤 Envoyé à {c.html.escape(row['company'])} ({c.html.escape(row['to_email'])})")


def classify(c, store, text):
    if AUTO_RE.search(text[:400]):
        return "automatique", ""
    if STOP_RE.search(text[:600]):
        return "stop", ""
    if NO_RE.search(text):
        return "pas_interesse", ""
    if HOT_RE.search(text):
        return "interesse", ""
    raw = c.llm_chat("Classe la réponse d'un prospect à un email commercial. Réponds en JSON : "
                     "{\"classe\": \"interesse|pas_interesse|a_relancer\", \"resume\": \"10 mots\"}",
                     text[:1500], store, max_tokens=600)
    classe = str((raw or {}).get("classe", "a_relancer"))
    return (classe if classe in ("interesse", "pas_interesse", "a_relancer") else "a_relancer",
            str((raw or {}).get("resume", ""))[:120])


def _body_text(msg):
    for part in (msg.walk() if msg.is_multipart() else [msg]):
        if part.get_content_type() == "text/plain":
            try:
                txt = part.get_content()
            except Exception:
                txt = (part.get_payload(decode=True) or b"").decode("utf-8", "replace")
            return re.split(r"\n(Le .{5,80} a écrit|On .{5,80} wrote|-----Original)", txt)[0]
    return ""


def _traiter_compte(c, cortex, mid, subject, msg):
    """Email « [CORTEX-COMPTE] » envoyé par Make après un paiement : création du compte (livraison.py).
    Inactif sans LIVRAISON_SECRET (message Telegram une seule fois). N'envoie aucun email."""
    s = cortex.s
    if s.db.execute("SELECT 1 FROM reponses WHERE message_id=?", (mid,)).fetchone():
        return
    import livraison
    res = livraison.traiter_email(s.db, subject, _body_text(msg), os.environ.get("LIVRAISON_SECRET", ""), store=s)
    if res is None:
        return
    if res["statut"] == "inactif":
        if not s.get(f"paiement_inactif_{mid}"):
            s.set(f"paiement_inactif_{mid}", "1")
            cortex.tg.send("⚠️ Paiement reçu, livraison inactive\n\nVariable LIVRAISON_SECRET absente : aucun compte créé.")
        return  # sera retraité dès que la clé existera
    s.db.execute("INSERT OR IGNORE INTO reponses VALUES(?,?,?,?,?,?)",
                 (mid, None, c.email_hash(c.SENDER_EMAIL), "paiement", res["statut"], c.iso(c.now())))
    s.db.commit()
    if res["statut"] == "cree":
        cortex.tg.send(f"💳 Compte client créé : {res['client_id']}")
    elif res["statut"] in ("signature_invalide", "invalide"):
        cortex.tg.send("⚠️ Paiement refusé\n\nSignature ou contenu invalide : aucun compte créé.")


def check_inbox(c, cortex):
    s = cortex.s
    last = s.get("last_inbox")
    if mail_mode() == "simulation" or (last and c.now() - c.parse_iso(last) < timedelta(minutes=INBOX_EVERY_MIN)):
        return
    s.set("last_inbox", c.iso(c.now()))
    sent = {r["to_email"].lower(): r for r in s.db.execute("SELECT * FROM envois WHERE kind!='rdv' ORDER BY id")}
    by_msgid = {r["message_id"]: r for r in s.db.execute("SELECT * FROM envois")}
    try:
        imap = imaplib.IMAP4_SSL(IMAP_HOST, 993, timeout=30)
        imap.login(MAIL_USER, MAIL_PASSWORD)
        imap.select("INBOX", readonly=True)  # lecture seule : rien n'est marqué ni déplacé
        _, data = imap.search(None, "SINCE", (c.now() - timedelta(days=10)).strftime("%d-%b-%Y"))
        for num in data[0].split()[-200:]:
            _, parts = imap.fetch(num, "(BODY.PEEK[])")
            msg = email.message_from_bytes(parts[0][1], policy=email.policy.default)
            mid = (msg.get("Message-ID") or "").strip()
            sender = parseaddr(msg.get("From", ""))[1].lower()
            subject = str(msg.get("Subject", ""))
            if mid and subject.strip().startswith("[CORTEX-COMPTE]"):  # transfert de paiement signé (Make)
                _traiter_compte(c, cortex, mid, subject, msg)
                continue
            if not mid or sender == c.SENDER_EMAIL.lower() or s.db.execute(
                    "SELECT 1 FROM reponses WHERE message_id=?", (mid,)).fetchone():
                continue
            env = by_msgid.get((msg.get("In-Reply-To") or "").strip()) or sent.get(sender)
            text = _body_text(msg)
            if not env and any(k.lower() in subject.lower() for k in (c.REQUEST_SUBJECT, "Demande de diagnostic")):
                # Demande de diagnostic (formulaire ou bouton de la page) : diagnostic rédigé,
                # envoyé seulement après validation de JOSY.
                name = parseaddr(msg.get("From", ""))[0] or sender.split("@")[-1]
                s.db.execute("INSERT OR IGNORE INTO reponses VALUES(?,?,?,?,?,?)",
                             (mid, None, c.email_hash(sender), "demande_diagnostic", "", c.iso(c.now())))
                s.db.commit()
                propose_diagnostic(c, cortex, name[:80], sender, mid, subject, text)
                continue
            if not env:
                continue
            classe, resume = classify(c, s, text)
            handle_reply(c, cortex, env, mid, sender, classe, resume, subject, text)
        imap.logout()
    except Exception as exc:
        s.log("EXECUTIF", "imap_erreur", details={"erreur": c.safe_error(exc)})
        c.alert(s, "imap", c.safe_error(exc))


def handle_reply(c, cortex, env, mid, sender, classe, resume, subject, text=""):
    s, db = cortex.s, cortex.s.db
    db.execute("INSERT OR IGNORE INTO reponses VALUES(?,?,?,?,?,?)",
               (mid, env["id"], c.email_hash(sender), classe, resume, c.iso(c.now())))
    if classe != "automatique":
        db.execute("UPDATE envois SET repondu=1, classe=? WHERE id=? OR parent_envoi=?",
                   (classe, env["id"], env["id"]))
    statut = {"stop": "opposition", "pas_interesse": "perdu", "interesse": "chaud",
              "a_relancer": "a_relancer"}.get(classe)
    if statut:
        db.execute("UPDATE entreprises SET statut=?, reponse_resume=?, maj_le=? WHERE lower(email_contact)=?",
                   (statut, resume, c.iso(c.now()), sender))
    db.commit()
    s.log("EXECUTIF", "reponse_recue", env["action_id"], {"classe": classe})
    company = c.html.escape(env["company"])
    if classe == "stop":
        db.execute("INSERT OR IGNORE INTO liste_opposition(siren, email_hash, date_opposition) VALUES('', ?, ?)",
                   (c.email_hash(sender), c.iso(c.now())))
        db.execute("UPDATE file_envoi SET statut='annule_opposition' WHERE lower(to_email)=? AND statut='en_file'",
                   (sender,))
        db.commit()
        cortex.tg.send(f"🛑 {company} a répondu STOP : ajouté à la liste d'opposition.")
    elif classe == "interesse":
        propose_hot_lead(c, cortex, env, mid, sender, subject, text)
    elif classe in ("a_relancer", "pas_interesse"):
        propose_replies(c, cortex, env, mid, sender, subject, text)


# ----------------------------------------------------------------- réponses aux prospects
def _draft_replies(c, cortex, env, text):
    raw = c.llm_chat(REPLY_PROMPT, f"Entreprise : {env['company']}\nMessage du prospect :\n{text[:1500]}",
                     cortex.s, max_tokens=1500)
    props = [str(x).strip() for x in (raw or {}).get("propositions") or [] if str(x).strip()][:3]
    return [p for p in props if not FORBIDDEN_CONTACT.search(p) and not c.PERSONAL_RE.search(p)
            and not _bad_price(c, p)]


def propose_replies(c, cortex, env, mid, sender, subject, text):
    """Format C : JOSY reçoit la réponse du prospect et 3 propositions ; il choisit /1, /2, /3
    ou écrit la sienne avec /r. Rien ne part sans son choix."""
    props = _draft_replies(c, cortex, env, text)
    db = cortex.s.db
    db.execute("CREATE TABLE IF NOT EXISTS reponses_attente (id INTEGER PRIMARY KEY AUTOINCREMENT, "
               "company TEXT, to_email TEXT, subject TEXT, in_reply_to TEXT, parent_envoi INTEGER, "
               "propositions TEXT, statut TEXT DEFAULT 'attente', cree_le TEXT)")
    db.execute("UPDATE reponses_attente SET statut='remplacee' WHERE statut='attente'")
    db.execute("INSERT INTO reponses_attente(company, to_email, subject, in_reply_to, parent_envoi, "
               "propositions, cree_le) VALUES(?,?,?,?,?,?,?)",
               (env["company"], sender, subject if subject.lower().startswith("re") else f"Re: {subject}",
                mid, env["id"], json.dumps(props, ensure_ascii=False), c.iso(c.now())))
    db.commit()
    import formats_telegram
    cortex.tg.send(formats_telegram.reponse_prospect(env["company"], text, props)[:4000])


def propose_hot_lead(c, cortex, env, mid, sender, subject, text):
    """Format D : un prospect veut avancer. Une réponse est proposée ; /valider l'envoie par email."""
    props = _draft_replies(c, cortex, env, text)
    if not props:
        propose_replies(c, cortex, env, mid, sender, subject, text)
        return
    body = props[0]
    aid = str(uuid.uuid4())
    p = {"action_id": aid, "timestamp": c.iso(c.now()), "risk_level": "R2",
         "mission": "M3_Relation_Client", "action_type": "reponse",
         "target": {"company": env["company"], "contact": "lead chaud", "email": sender},
         "content": {"subject": subject if subject.lower().startswith("re") else f"Re: {subject}",
                     "body": "Bonjour,\n\n" + body + SIGN_REPLY.format(signature=c.SIGNATURE)},
         "in_reply_to": mid, "parent_envoi": env["id"],
         "sources": [{"url": "réponse reçue", "date": c.iso(c.now())}],
         "justification": "Le prospect souhaite avancer.",
         "reversibility": "Rien n'est envoyé sans ton clic.", "timeout_hours": 24}
    text_d = (f"🔥 {c.html.escape(env['company'])} veut avancer. Réponse proposée : {c.html.escape(body.rstrip('. '))}. "
              f"/valider {aid[:8]} /refuser {aid[:8]}")
    cortex.dispatch(p, text=text_d)
    if not cortex.s.db.execute("SELECT 1 FROM proposals WHERE action_id=?", (aid,)).fetchone():
        propose_replies(c, cortex, env, mid, sender, subject, text)  # quota atteint : choix classique


def _bad_price(c, text):
    return any(re.sub(r"\D", "", a) not in c.ALLOWED_PRICES for a in c.PRICE_RE.findall(text))


def answer_reply(c, cortex, choice, free_text=""):
    """JOSY a choisi /1, /2, /3 ou /r : la réponse part par email (file d'envoi)."""
    db = cortex.s.db
    row = db.execute("SELECT * FROM reponses_attente WHERE statut='attente' ORDER BY id DESC LIMIT 1").fetchone() \
        if db.execute("SELECT name FROM sqlite_master WHERE name='reponses_attente'").fetchone() else None
    if not row:
        cortex.tg.send("Aucune réponse de prospect en attente.")
        return
    props = json.loads(row["propositions"])
    if choice == "r":
        body = free_text.strip()
    elif choice.isdigit() and 1 <= int(choice) <= len(props):
        body = props[int(choice) - 1]
    else:
        cortex.tg.send("Choix inconnu.")
        return
    if not body or FORBIDDEN_CONTACT.search(body) or c.PERSONAL_RE.search(body) or _bad_price(c, body):
        cortex.tg.send("Réponse refusée par le contrôle (appel/RDV, coordonnées perso ou prix hors catalogue).")
        return
    p = {"action_id": str(uuid.uuid4()), "action_type": "reponse",
         "target": {"company": row["company"], "email": row["to_email"]},
         "content": {"subject": row["subject"],
                     "body": "Bonjour,\n\n" + body + SIGN_REPLY.format(signature=c.SIGNATURE)},
         "in_reply_to": row["in_reply_to"], "parent_envoi": row["parent_envoi"]}
    db.execute("UPDATE reponses_attente SET statut='repondue' WHERE id=?", (row["id"],))
    db.execute("INSERT INTO proposals(action_id, created_at, risk_level, mission, action_type, status, "
               "expires_at, decided_at, decision_source, payload) VALUES(?,?,?,?,?,?,?,?,?,?)",
               (p["action_id"], c.iso(c.now()), "R2", "M3_Relation_Client", "reponse", "valide",
                c.iso(c.now()), c.iso(c.now()), "commande", json.dumps(p, ensure_ascii=False)))
    db.commit()
    cortex.s.log("HUMAIN", "reponse_choisie", p["action_id"], {"choix": choice})
    queue_from_proposal(c, cortex, p)


# ----------------------------------------------------------------- demandes de diagnostic
def propose_diagnostic(c, cortex, name, sender, mid, subject, text):
    """Règle 5 : analyse du site indiqué, diagnostic rédigé, envoyé après validation de JOSY."""
    import audit
    site = re.search(r"https?://[^\s<>\"]+|(?:www\.)?[a-z0-9-]+\.(?:fr|com|net|org|eu|bzh)\b", text or "", re.I)
    ville = (re.search(r"\b\d{5}\s+([A-Za-zÀ-ÿ' -]{2,40})", text or "") or [None, ""])[1].strip()
    row = {"nom": name, "secteur": "", "ville": ville, "email": sender,
           "site": (site.group(0) if site and site.group(0).startswith("http")
                    else f"https://{site.group(0)}" if site else None)}
    a = audit.audit_prospect(row)
    faits = a["manques"][:4]
    corps = ("Bonjour,\n\nMerci pour votre demande. Voici un premier diagnostic de votre présence en "
             "ligne, établi à partir d'informations publiques.\n\n"
             + ("Ce que j'ai constaté :\n" + "\n".join(f"- {f[0].upper() + f[1:]}." for f in faits)
                if faits else "Je n'ai pas relevé de manque évident sur les éléments publics vérifiés.")
             + "\n\nSi vous souhaitez en savoir plus, répondez directement à cet email."
             + SIGN_REPLY.format(signature=c.SIGNATURE))
    p = {"action_id": str(uuid.uuid4()), "timestamp": c.iso(c.now()), "risk_level": "R2",
         "mission": "M3_Relation_Client", "action_type": "diagnostic",
         "target": {"company": name, "contact": "demande de diagnostic", "email": sender},
         "content": {"subject": f"Re: {subject}", "body": corps}, "in_reply_to": mid,
         "sources": [{"url": a["site"].get("url_finale") or "demande reçue", "date": a["date"]}],
         "justification": f"{len(faits)} constat(s) vérifié(s).",
         "reversibility": "Rien n'est envoyé sans ton clic.", "timeout_hours": 24}
    resume = "; ".join(faits[:2]) or "aucun manque évident"
    cortex.dispatch(p, header=f"🔔 Demande de diagnostic : {c.html.escape(name)}. "
                              f"Résumé : {c.html.escape(resume[:300])}. Prêt à envoyer ?")


def plan_relances(c, cortex):
    """Une fois par jour : relances J+3 et J+7 sans réponse, regroupées en un seul lot à valider."""
    s = cortex.s
    today = c.now().astimezone(c.PARIS).date().isoformat()
    if s.get("relances_day") == today:
        return
    s.set("relances_day", today)
    opposed = {h for (h,) in s.db.execute("SELECT email_hash FROM liste_opposition")}
    items = []
    for n, days in enumerate(RELANCE_DAYS, 1):
        for e in s.db.execute("SELECT * FROM envois WHERE kind='premier' AND repondu=0 AND relance_n=? "
                              "AND sent_at<=?", (n - 1, c.iso(c.now() - timedelta(days=days)))).fetchall():
            if c.email_hash(e["to_email"]) in opposed or s.db.execute(
                    "SELECT 1 FROM file_envoi WHERE parent_envoi=? AND statut='en_file'", (e["id"],)).fetchone():
                continue
            items.append({"to": e["to_email"], "company": e["company"], "parent": e["id"],
                          "subject": e["subject"] if e["subject"].startswith("Re") else f"Re: {e['subject']}",
                          "body": RELANCE_TEXTS[n].format(booking=c.BOOKING_LINE, signature=c.SIGNATURE),
                          "in_reply_to": e["message_id"]})
    if not items:
        return
    p = {"action_id": str(uuid.uuid4()), "timestamp": c.iso(c.now()), "risk_level": "R2",
         "mission": "M3_Relation_Client", "action_type": "relance", "items": items,
         "target": {"company": f"{len(items)} prospects sans réponse", "contact": "J+3 / J+7"},
         "content": {"subject": "Relances", "body": items[0]["body"]},
         "sources": [{"url": "historique des envois (cortex.db)", "date": today}],
         "justification": f"{len(items)} emails sans réponse depuis 3 ou 7 jours.",
         "reversibility": "Rien n'est envoyé sans ton clic.", "timeout_hours": 24}
    cortex.dispatch(p, header=f"🔁 {len(items)} relance(s) prêtes (J+3 / J+7). Je les envoie toutes ?")


def notify_pending(c, cortex):
    """Format E : rappel au plus toutes les 4 h s'il reste des actions en attente depuis plus d'1 h."""
    s = cortex.s
    last = s.get("last_pending_notice")
    if last and c.now() - c.parse_iso(last) < timedelta(hours=4):
        return
    row = s.db.execute("SELECT COUNT(*), MIN(created_at) FROM proposals WHERE status=?", (c.PENDING,)).fetchone()
    if row[0] and c.now() - c.parse_iso(row[1]) > timedelta(hours=1):
        s.set("last_pending_notice", c.iso(c.now()))
        cortex.tg.send(f"⏳ {row[0]} actions en attente. /attente pour la liste.")


def cycle(c, cortex):
    setup(cortex.s)
    process_queue(c, cortex)
    check_inbox(c, cortex)
    plan_relances(c, cortex)
    notify_pending(c, cortex)
