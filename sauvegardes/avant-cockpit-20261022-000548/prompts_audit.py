"""EXÉCUTIF — rédaction des emails d'audit par le modèle (Groq), à partir des seuls faits vérifiés.

Le modèle écrit l'objet et le corps ; le code ajoute la signature de l'entreprise émettrice (avec la
mention RGPD et la désinscription STOP). Le texte n'est jamais envoyé tel quel : il passe le veto
du judiciaire (regles_absolues.py), puis la validation de JOSY sur Telegram.
"""

import json
import re

# Prompt système de la décision JOSY du 19/10/2026 (10:01), repris mot pour mot. Les règles de rédaction de
# PROMPT_SYSTEME_AUDIT (format JSON, 8 lignes, preuve exacte, aucun chiffre inventé) lui sont ajoutées :
# le code en dépend pour extraire l'objet et passer le veto du judiciaire.
PROMPT_SYSTEME_EMAIL = """Tu es le moteur de prospection de JOSY EI. Tu rédiges des emails B2B professionnels.

TA MISSION :
1. Analyser l'entreprise cible (site web, fiche Google, présence en ligne).
2. Pointer UN problème concret et vérifiable (ex: "Le 1er résultat Google Maps pour 'plombier + [ville]' est votre concurrent X, vous n'y êtes pas").
3. Expliquer l'impact business de ce problème (perte de clients, invisibilité, manque d'appels).
4. Proposer un AUDIT ou DIAGNOSTIC GRATUIT pour résoudre ce problème.

RÈGLES ABSOLUES :
- ZÉRO PRIX : tu ne mentionnes JAMAIS de tarif, coût, abonnement, offre commerciale chiffrée.
- ZÉRO RDV : tu ne proposes pas de rendez-vous ni d'appel. Uniquement l'email.
- ZÉRO PROMESSE MAGIQUE : tu décris des faits vérifiables, pas des résultats garantis.
- SIGNATURE : contact@josyei.com
- LANGUE : français, professionnel, direct, concis.

FORMAT :
- Objet : court, percutant, sans prix, sans mot "gratuit" dans l'objet (éviter les filtres spam).
- Corps : problème identifié + impact + proposition d'audit.
- Pas de liste à puces inutile. Pas de bla-bla.
"""

PROMPT_SYSTEME_AUDIT = PROMPT_SYSTEME_EMAIL + """
RÈGLES TECHNIQUES (le code et le judiciaire en dépendent) :
1. Le problème est le FAIT VÉRIFIÉ fourni, cité avec ses noms et ses chiffres exacts. N'écris aucun autre chiffre.
   N'invente aucun fait, aucun résultat, aucune URL.
2. L'impact tient en deux phrases au plus. La personne répond simplement à cet email pour recevoir l'audit.
3. Mots refusés par le judiciaire, même dans un autre sens : prix, tarif, coût, abonnement, forfait, mensuel, annuel,
   offre (et « offrir », « offrent »), promotion, réduction, remise, solde, promo, pack, formule (et « formuler »),
   euro, et « écouter » (contient « cout »). N'écris pas non plus appel, téléphone, rendez-vous, visio, créneau,
   rencontre : parle de « clients » ou de « demandes », jamais d'« appels ».
4. Vouvoiement. Corps de 8 lignes au plus, commençant par « Bonjour, ». Pas de signature : le code l'ajoute
   (contact@josyei.com, SIREN, désinscription STOP).

Format de réponse : uniquement un objet JSON {"objet": "...", "corps": "..."}.
"""


def appeler_groq(system_prompt, user_prompt, temperature=0.4, max_tokens=800, store=None):
    """Un appel au modèle Groq configuré (GROQ_API_KEY, GROQ_MODEL), repli sur les autres modèles Groq.
    Renvoie l'objet JSON produit, ou None si aucun modèle n'a répondu."""
    import cortex
    for cfg in cortex.LLM_CHAIN:
        body = {"model": cfg["model"], "temperature": temperature, "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": system_prompt},
                             {"role": "user", "content": user_prompt}]}
        if "gpt-oss" in cfg["model"]:
            body["reasoning_effort"] = "low"
        try:
            r = cortex.HTTP.post(cfg["url"], json=body, timeout=cfg["timeout"],
                                 headers={"Authorization": f"Bearer {cfg['key']}",
                                          "Content-Type": "application/json"})
        except Exception as exc:
            if store:
                store.log("EXECUTIF", "llm_erreur_reseau", details={"modele": cfg["model"],
                                                                   "erreur": cortex.safe_error(exc)})
            continue
        if r.status_code != 200:
            if store:
                store.log("EXECUTIF", "llm_erreur_http", details={"modele": cfg["model"], "statut": r.status_code})
            continue
        try:
            content = r.json()["choices"][0]["message"]["content"]
            m = re.search(r"\{.*\}", str(content), re.S)
            data = json.loads(m.group(0) if m else content)
        except (ValueError, KeyError, IndexError, TypeError):
            continue
        if isinstance(data, dict):
            data["_modele"] = cfg["model"]
            return data
    return None


def construire_prompt_utilisateur(tenant_context, prospect_data):
    p = tenant_context.get("preuves_verifiables") or {}
    fuites = tenant_context.get("fuites_acquisition_detectees") or []
    if isinstance(fuites, (list, tuple)):
        fuites = "\n".join(f"- {f}" for f in fuites)
    return f"""
Entreprise émettrice : {tenant_context.get('nom_tenant', 'JOSY EI')}
Entreprise analysée : {prospect_data.get('nom', '')}
Site web : {prospect_data.get('site_web') or 'non vérifié'}
Fiche Google : {prospect_data.get('fiche_google_url') or prospect_data.get('fiche_google') or 'non vérifiée'}
Métier détecté : {prospect_data.get('metier') or 'non déterminé'}
Ville : {prospect_data.get('ville', '')}

Analyse effectuée :
{tenant_context.get('analyse_site_web', '')}
{tenant_context.get('analyse_fiche_google', '')}

Problèmes identifiés :
{fuites}

FAIT VÉRIFIÉ (source : {p.get('source', 'analyse publique')}), à citer avec ses noms et chiffres exacts :
{p.get('fait', '')}
Éléments à reprendre mot pour mot : {', '.join(str(x) for x in p.get('elements_obligatoires') or [])}

Rédige un email qui pointe le problème le plus critique, explique son impact, et propose un audit gratuit pour le résoudre.
N'oublie pas : zéro prix, zéro abonnement, uniquement expertise et diagnostic.
"""


def generer_email_audit(tenant_context: dict, prospect_data: dict, llm=None) -> str:
    """Génère un email d'audit personnalisé basé sur l'analyse du prospect.
    Renvoie « Objet : …\\n\\n<corps>\\n\\n<signature> », ou "" si le modèle n'a pas répondu.
    `llm` : fonction (system_prompt, user_prompt, temperature, max_tokens) -> dict, simulée en test."""
    user_prompt = construire_prompt_utilisateur(tenant_context, prospect_data)
    response = (llm or appeler_groq)(system_prompt=PROMPT_SYSTEME_AUDIT, user_prompt=user_prompt,
                                     temperature=0.4, max_tokens=800)
    if not isinstance(response, dict):
        return ""
    objet = re.sub(r"\s+", " ", str(response.get("objet", ""))).strip()[:120]
    corps = re.sub(r"\n{3,}", "\n\n", str(response.get("corps", "")).replace("\r", "")).strip()
    if not objet or not corps:
        return ""
    return f"Objet : {objet}\n\n{corps}\n\n{tenant_context.get('signature', '')}".rstrip()


def separer_objet(email):
    """(objet, corps) d'un email produit par generer_email_audit."""
    m = re.match(r"\s*Objet\s*:\s*([^\n]*)\n+(.*)", email or "", re.S)
    return (m.group(1).strip(), m.group(2).strip()) if m else ("", (email or "").strip())
