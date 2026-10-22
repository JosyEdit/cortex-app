"""Démonstration (dry-run) : tenant ENTREPRISE_DEMO, prospect fictif, UN vrai appel Groq pour l'email.

Rien n'est envoyé : la soumission Telegram et l'envoi d'email sont simulés. Base : audit_demo.db (jetable),
jamais cortex.db ni l'audit.db de production. Résultat écrit dans demo_resultat.json.
Usage : python demo_audit.py [chemin du .env contenant GROQ_API_KEY]
"""

import json
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ENV = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / ".env"
os.environ["CORTEX_AUDIT_DB"] = str(BASE / "audit_demo.db")
try:
    from dotenv import load_dotenv
    load_dotenv(ENV)  # GROQ_API_KEY et GROQ_MODEL seulement utiles ici ; aucune valeur n'est affichée
except ImportError:
    pass
for k in ("TG_TOKEN", "TG_CHAT", "HOSTINGER_PASSWORD"):
    os.environ.pop(k, None)  # aucun canal sortant possible pendant la démo
sys.path.insert(0, str(BASE))

import cortex  # noqa: E402
import dossier_audit_manager as dam  # noqa: E402
import regles_absolues  # noqa: E402
import workflow_audit  # noqa: E402

cortex.require_groq_key()
(BASE / "audit_demo.db").unlink(missing_ok=True)
print("Migration :", dam.migrer())
m = dam.DossierAuditManager()
tenant_id = m.assurer_tenant("ENTREPRISE_DEMO", site_web="https://josyei.com", email_contact="contact@josyei.com",
                             signature=cortex.SIGNATURE)

FAIT = ("sur Google Maps, le 1er résultat pour « restaurant Montmorillon » est Le Bistrot du Marché, avec 412 avis, "
        "et votre entreprise n'apparaît pas dans les 20 premiers résultats")
analyse = {  # prospect FICTIF : aucune recherche web, aucune donnée réelle
    "entreprise": {"nom": "Restaurant Test", "ville": "Montmorillon", "email": "contact@restaurant-test.invalid",
                   "metier": "restaurant", "officiel": None, "secteur": ""},
    "site": {"site": "https://restaurant-test.invalid", "joignable": True, "url_finale": "https://restaurant-test.invalid",
             "https": True, "mobile": False, "meta_description": False, "mentions_legales": True,
             "google_maps": {"requete": "restaurant Montmorillon", "rang": None, "total": 20,
                             "premier": {"nom": "Le Bistrot du Marché", "avis": 412}, "prospect": None,
                             "moyenne_avis": 120, "nb_autres": 20, "source": "Google Maps (Serper)"}},
    "manques": [FAIT], "services": ["concurrents"], "manques_detail": [[FAIT, "concurrents"]], "date": "2026-10-19"}
prospect = {"nom": "Restaurant Test", "site_web": "https://restaurant-test.invalid", "metier": "restaurant",
            "ville": "Montmorillon", "email_contact": "contact@restaurant-test.invalid"}



def osint_simule(nom, site, siren=""):  # prospect fictif : OSINT simulé, aucune requête vers un site réel
    import osint_tools
    return {"legal_data": {"status": "ok", "siren": "000000000", "activite": "56.10A", "date_creation": "2015-03-01",
                           "dirigeants": [{"nom": "FICTIF", "qualite": "Gérant"}]},
            "technologies": {"status": "ok", "technologies": [{"nom": "WordPress"}, {"nom": "Google Analytics"}]},
            "google_maps": osint_tools.google_maps_exclu(),
            "social_profiles": {"status": "ok", "plateformes": [{"plateforme": "Instagram", "url": "fictif"}]},
            "emails_pro": ["contact@restaurant-test.invalid"], "erreurs": [], "timestamp": dam._now()}


telegram_simule = []
dossier_id = workflow_audit.workflow_audit_complet(
    tenant_id, prospect, manager=m, analyse=analyse, osint=osint_simule,
    soumettre=lambda d, e: telegram_simule.append(e) or "en_attente")  # rien ne part vers Telegram
d = m.obtenir(dossier_id) if dossier_id else m.lister_dossiers_par_tenant(tenant_id)[0]
email = d["email_genere"] or ""
motifs = regles_absolues.ReglesAbsolues.motifs(email, m.contexte_validation(d["id"]))
resultat = {
    "dossier": {k: d[k] for k in ("id", "tenant_id", "prospect_nom", "prospect_ville", "prospect_metier", "statut",
                                  "email_valide", "created_at")},
    "analyse": {"site": d["analyse_site_web"], "google": d["analyse_fiche_google"],
                "probleme_principal": d["probleme_principal"], "impact": d["impact_business"]},
    "osint_dans_le_dossier": (json.loads(d["preuves_verifiables"] or "{}").get("osint")),
    "osint_timestamp": d["osint_timestamp"],
    "email": email,
    "validation_judiciaire": "ADMIS" if not motifs else "REJETÉ",
    "motifs_veto": motifs,
    "zero_prix": not regles_absolues.motifs_zero_prix(email),
    "soumis_telegram_simule": len(telegram_simule),
    "modele": cortex.GROQ_MODEL,
}
(BASE / "demo_resultat.json").write_text(json.dumps(resultat, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(resultat, ensure_ascii=False, indent=2))
m.close()
