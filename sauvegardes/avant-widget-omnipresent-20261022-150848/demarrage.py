"""Contrôle de démarrage : quelles clés ou autorisations manquent, et ce que chacune débloque.

Aucune valeur n'est lue ni affichée : seuls les NOMS de variables sont testés (présente et non vide).
Les variables viennent de l'environnement, de `.env` et des fichiers `.env.*` du dossier.
Un module externe (Google Business, source de repli…) reste inactif tant que sa variable manque ;
ce contrôle le dit une fois par jour sur Telegram, sans rien envoyer d'autre.
"""

import os
from pathlib import Path

try:
    from dotenv import dotenv_values
except Exception:  # python-dotenv absent : on lit seulement l'environnement
    dotenv_values = None

BASE = Path(__file__).resolve().parent

# (nom de la variable, service, ce que ça débloque, indispensable au fonctionnement actuel ?)
CLES = [
    ("TG_TOKEN", "Telegram", "messages et commandes", True),
    ("TG_CHAT", "Telegram", "identifiant du chat de JOSY", True),
    ("GROQ_API_KEY", "Groq", "analyses et dialogue (120b, 20b, qwen)", True),
    ("HOSTINGER_EMAIL", "Hostinger", "adresse d'envoi contact@josyei.com", True),
    ("HOSTINGER_PASSWORD", "Hostinger", "envoi et lecture des emails", True),
    ("SERPER_API_KEY", "Serper.dev", "arguments Google Maps (avis, concurrents)", True),
    ("GOOGLE_PLACES_KEY", "Google Places (API New)", "position et avis directement chez Google, repli sur Serper si refusée", False),
    ("BRAVE_API_KEY", "Brave Search", "recherche web de repli", False),
    ("GBP_CLIENT_ID", "Google Business Profile", "publication de posts et réponses aux avis (identifiant OAuth)", False),
    ("GBP_CLIENT_SECRET", "Google Business Profile", "publication de posts et réponses aux avis (secret OAuth)", False),
    ("GBP_REFRESH_TOKEN", "Google Business Profile", "autorisation obtenue côté Google", False),
    ("GBP_LOCATION", "Google Business Profile", "fiche à publier (accounts/…/locations/…)", False),
]


def _valeurs():
    vals = {k: v for k, v in os.environ.items() if v}
    if dotenv_values:
        for f in sorted(BASE.glob(".env*")):
            vals.update({k: v for k, v in (dotenv_values(f) or {}).items() if v})
    return vals


def manquantes(seulement_indispensables=False):
    vals = _valeurs()
    return [c for c in CLES if not vals.get(c[0]) and (c[3] or not seulement_indispensables)]


def rapport():
    """Texte lisible : ce qui manque, groupé par service."""
    manque = manquantes()
    if not manque:
        return "Toutes les clés attendues sont présentes."
    par_service = {}
    for nom, service, effet, indispensable in manque:
        par_service.setdefault((service, effet, indispensable), []).append(nom)
    lignes = []
    for (service, effet, indispensable), noms in par_service.items():
        lignes.append(f"- {service} ({', '.join(noms)}) : {effet}" + (" [INDISPENSABLE]" if indispensable else ""))
    return "\n".join(lignes)


def notifier(c, cortex, une_fois_par_jour=True):
    """Message Telegram unique par jour, seulement s'il manque quelque chose."""
    s = cortex.s
    jour = c.now().astimezone(c.PARIS).date().isoformat()
    if une_fois_par_jour and s.get("cles_manquantes_jour") == jour:
        return None
    manque = manquantes()
    s.set("cles_manquantes_jour", jour)
    if not manque:
        return None
    services = sorted({m[1] for m in manque})
    s.log("SYSTEME", "cles_manquantes", details={"services": services})  # noms de services, jamais de valeur
    cortex.tg.send(f"🔑 {len(manque)} clé(s) ou accès manquants : {c.html.escape(', '.join(services))}. "
                   "Modules concernés inactifs. Détail : /cles")
    return manque
