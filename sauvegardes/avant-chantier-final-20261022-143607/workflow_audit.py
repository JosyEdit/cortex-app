"""Workflow complet d'un audit : dossier -> analyse -> email -> veto judiciaire -> validation JOSY -> envoi.

En service (cortex.py), `soumettre` publie l'email sur Telegram (boutons Valider / Refuser, lecteur unique
chat_daemon.py) et renvoie « en_attente » : l'envoi a lieu plus tard, après le clic de JOSY, par la file
d'envoi de vente.py. En test, `soumettre` et `envoyer_email` sont simulés et rien ne sort du PC.
"""

import json

from dossier_audit_manager import DossierAuditManager


def _log(niveau, message):
    print(json.dumps({"workflow_audit": niveau, "message": message}, ensure_ascii=False))


def workflow_audit_complet(tenant_id: str, prospect_data: dict, manager=None, analyse=None, analyseur=None,
                           llm=None, soumettre=None, envoyer_email=None, log=_log, osint=None):
    """Renvoie l'identifiant du dossier si l'email a été soumis à JOSY (ou envoyé), sinon None.

    analyse   : analyse déjà faite (audit.audit_prospect), sinon `analyseur` ou audit.audit_prospect
    osint     : collecte OSINT simulée (tests), False pour s'en passer ; par défaut osint_tools
    llm       : rédacteur simulé (tests) ; par défaut, Groq
    soumettre : f(dossier, email) -> "approuve" | "refuse" | "en_attente" | None (non soumis)
    """
    import osint_tools
    manager = manager or DossierAuditManager()
    manager.purger_osint()  # conservation limitée : 90 jours

    # 1. Créer le dossier d'audit
    dossier_id = manager.creer_dossier_audit(tenant_id, prospect_data)
    log("info", f"Dossier créé: {dossier_id}")

    # Contact : jamais une adresse nominative (veto 2), jamais un domaine ou un SIREN exclu (F1.6)
    destinataire = prospect_data.get("email_contact") or prospect_data.get("email") or ""
    if destinataire and not osint_tools.email_generique(destinataire):
        manager.maj_statut(dossier_id, "email_nominatif")
        log("info", f"Adresse non générique pour {dossier_id} : pas de contact")
        return None
    if manager.est_exclu(destinataire, prospect_data.get("siren"), prospect_data.get("site_web")):
        manager.maj_statut(dossier_id, "exclu")
        log("info", f"Prospect sur la liste d'exclusion pour {dossier_id}")
        return None

    # 2. Analyser le prospect (site, Google Maps via Serper, annuaire officiel, OSINT)
    if analyse is not None:
        res = manager.enregistrer_analyse(dossier_id, analyse, manager.collecter_osint(dossier_id, analyse, osint))
    else:
        res = manager.analyser_prospect(dossier_id, analyseur, osint)
    if not res["probleme"]:
        log("info", f"Aucun fait vérifié pour {dossier_id} : pas d'email")
        return None
    siren = ((res.get("osint") or {}).get("legal_data") or {}).get("siren")
    if siren and manager.est_exclu(siren=siren):
        manager.maj_statut(dossier_id, "exclu")
        log("info", f"SIREN sur la liste d'exclusion pour {dossier_id}")
        return None
    log("info", f"Analyse terminée pour {dossier_id}")

    # 3. Générer l'email d'audit (le veto du judiciaire est appliqué dans la foulée)
    email = manager.generer_email_audit(dossier_id, llm=llm)
    log("info", f"Email généré pour {dossier_id}")

    # 4. Vérifier la validation judiciaire
    dossier = manager.obtenir(dossier_id)
    if not dossier["email_valide"]:
        log("warning", f"Email rejeté par veto Judiciaire pour {dossier_id} : {dossier['motifs_veto']}")
        return None

    # 5. Soumettre à JOSY sur Telegram (validation humaine obligatoire)
    if soumettre is None:
        log("warning", f"Aucun canal de validation : {dossier_id} reste en attente")
        return None
    decision = soumettre(dossier, email)
    if decision == "en_attente":
        manager.maj_statut(dossier_id, "attente_validation")
        log("info", f"Email soumis à JOSY pour {dossier_id}")
        return dossier_id
    if decision != "approuve":
        if manager.obtenir(dossier_id)["statut"] != "rejete_veto":
            manager.maj_statut(dossier_id, "refuse" if decision == "refuse" else "non_soumis")
        log("info", f"Email refusé ou non soumis pour {dossier_id}")
        return None

    # 6. Envoyer l'email (approbation synchrone : mode test ou appel direct)
    manager.maj_statut(dossier_id, "valide")
    if envoyer_email is None:
        return dossier_id
    envoyer_email(prospect_data.get("email_contact") or prospect_data.get("email"), email)
    from dossier_audit_manager import _now
    manager.maj_statut(dossier_id, "envoye", email_envoye=1, date_envoi=_now())
    log("success", f"Email envoyé pour {dossier_id}")
    return dossier_id
