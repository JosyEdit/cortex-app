"""Envoi d'un email par SMTP Hostinger (smtp.hostinger.com:465, SSL). Utilitaire sans logique propre :
il envoie exactement ce qu'on lui donne. Les contrôles (liste d'opposition, plafond quotidien, validation
de JOSY, mentions RGPD) sont faits par vente.py AVANT l'appel.

Identifiants : HOSTINGER_EMAIL et HOSTINGER_PASSWORD, lus dans .env. Le mot de passe n'est jamais
écrit dans un message d'erreur ni dans un journal.
"""

import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from dotenv import load_dotenv

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, ".env"))
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.hostinger.com")
SMTP_PORT = 465


class EmailError(Exception):
    """Échec d'envoi, message sans secret."""


def configured():
    return bool(os.environ.get("HOSTINGER_EMAIL", "").strip() and os.environ.get("HOSTINGER_PASSWORD", "").strip())


def build_message(to, subject, body, in_reply_to=None, sender=None):
    user = os.environ.get("HOSTINGER_EMAIL", "").strip()
    sender = sender or user
    msg = EmailMessage()
    msg["From"] = f"JOSY EI <{sender}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=sender.split("@")[-1] or "josyei.com")
    msg["List-Unsubscribe"] = f"<mailto:{sender}?subject=STOP>"
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    msg.set_content(body)
    return msg


def send_email(to, subject, body, in_reply_to=None):
    """Envoie un email. Renvoie l'identifiant du message ; lève EmailError (sans secret) en cas d'échec."""
    user = os.environ.get("HOSTINGER_EMAIL", "").strip()
    password = os.environ.get("HOSTINGER_PASSWORD", "").strip()
    if not user or not password:
        raise EmailError("identifiants Hostinger absents du fichier .env")
    if not to or "@" not in to:
        raise EmailError("destinataire invalide")
    msg = build_message(to, subject, body, in_reply_to, sender=user)
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ssl.create_default_context(), timeout=30) as s:
            s.login(user, password)
            s.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        raise EmailError("authentification SMTP refusée") from None
    except smtplib.SMTPRecipientsRefused:
        raise EmailError("destinataire refusé par le serveur") from None
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailError(f"envoi impossible ({type(exc).__name__})") from None
    return msg["Message-ID"]
