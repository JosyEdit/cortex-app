"""Honnêteté du Cortex : état réel injecté dans le chat, /historique, /log, /lancer_prospection.

Règle : une donnée absente de cortex.db n'est jamais inventée. Réponses autorisées quand elle manque :
« je ne sais pas », « aucune action lancée », « aucune raison particulière ».
"""

import json
from datetime import datetime

CONSIGNES_HONNETE = (
    "RÈGLES D'HONNÊTETÉ ABSOLUES : n'invente jamais une heure, une fenêtre de temps, un cycle, une mission "
    "prête, une raison de lancer quelque chose, une tendance ou un comportement de clients. Utilise "
    "uniquement l'heure et l'état réels fournis ci-dessous. Si une donnée n'y figure pas, réponds « je ne "
    "sais pas ». Si rien n'a été lancé, réponds « aucune action lancée ». S'il n'y a pas de raison, réponds "
    "« aucune raison particulière ». Tu ne lances rien dans la conversation : n'écris jamais « je lance » ; "
    "écris « je peux lancer. Confirme avec /lancer_prospection. » seulement pour la prospection.")

# Événements du journal qui sont de vraies actions (pas les simples passages de cycle)
ACTIONS = ("proposition_en_attente_humain", "decision_valide", "decision_refuse", "email_envoye", "email_simule",
           "envoi_mis_en_file", "reponse_recue", "analyse_llm_fin", "recherche_prospects", "recherche_entreprises",
           "publication", "regles_restaurees", "droit_oubli_applique", "export_complet", "opposition_ajoutee")


def _ligne(r):
    d = ""
    try:
        det = json.loads(r["details"] or "{}")
        d = ", ".join(f"{k}={v}" for k, v in det.items() if k in ("mission", "type", "classe", "ajoutees", "emails",
                                                                   "emails_trouves", "risque", "fichier"))
    except ValueError:
        pass
    return f"{r['ts'][5:16].replace('T', ' ')} UTC · {r['event']}" + (f" ({d})" if d else "")


def historique(store, n=10):
    """Les n dernières actions réelles du journal (heure UTC du journal), sans commentaire."""
    q = ",".join("?" * len(ACTIONS))
    rows = store.db.execute(f"SELECT ts, event, details FROM journal WHERE event IN ({q}) ORDER BY id DESC LIMIT ?",
                            (*ACTIONS, n)).fetchall()
    return "\n".join(_ligne(r) for r in rows) or "Aucune action enregistrée."


def log_resume(store):
    def dernier(sql, args=()):
        return store.db.execute(sql, args).fetchone()

    mission = dernier("SELECT ts, details FROM journal WHERE event='analyse_llm_fin' ORDER BY id DESC LIMIT 1")
    action = dernier(f"SELECT ts, event, details FROM journal WHERE event IN ({','.join('?' * len(ACTIONS))}) "
                     "ORDER BY id DESC LIMIT 1", ACTIONS)
    prop = dernier("SELECT created_at, action_type, status FROM proposals ORDER BY created_at DESC LIMIT 1")
    valid = dernier("SELECT ts, event FROM journal WHERE event IN ('decision_valide','decision_refuse') "
                    "ORDER BY id DESC LIMIT 1")
    nom = "inconnue"
    if mission:
        try:
            nom = json.loads(mission["details"]).get("mission", "inconnue")
        except ValueError:
            pass
    return "\n".join([
        f"Dernière mission : {nom} ({mission['ts'][5:16].replace('T', ' ')} UTC)" if mission else "Dernière mission : aucune",
        f"Dernière action : {_ligne(action)}" if action else "Dernière action : aucune action lancée",
        f"Dernière proposition : {prop['action_type']} · {prop['status']} ({prop['created_at'][5:16].replace('T', ' ')} UTC)"
        if prop else "Dernière proposition : aucune",
        f"Dernière validation : {valid['event']} ({valid['ts'][5:16].replace('T', ' ')} UTC)" if valid
        else "Dernière validation : aucune"])


def contexte_reel(store):
    """Bloc injecté dans le prompt du chat : heure réelle du PC + état lu dans cortex.db."""
    maintenant = datetime.now().astimezone()
    en_attente = store.db.execute("SELECT COUNT(*) FROM proposals WHERE status='en_attente_humain'").fetchone()[0]
    return (f"HEURE RÉELLE DU PC : {maintenant.strftime('%d/%m/%Y %H:%M:%S')} (fuseau {maintenant.tzname()}).\n"
            f"ÉTAT RÉEL (cortex.db) : {en_attente} action(s) en attente de JOSY.\n" + log_resume(store))


def lancer_prospection(c, cortex):
    """Lance UNE prospection, avec les mêmes plafonds et la même validation par email que d'habitude."""
    propositions = cortex.prospect() or []
    for p in propositions:
        cortex.dispatch(p)
    if not propositions:
        cortex.tg.send("Aucun prospect qualifié pour l'instant : aucune proposition créée.")
    return len(propositions)
