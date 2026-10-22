"""Tests du moteur d'audit universel (aucun réseau : modèle, Telegram et email simulés).

Lancement : python test_moteur_audit.py   (ou python -m pytest test_moteur_audit.py)
Bases de test temporaires : rien n'est écrit dans cortex.db ni dans audit.db de production.
"""

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="cortex_tests_"))
os.environ["CORTEX_AUDIT_DB"] = str(TMP / "audit_test.db")      # avant tout import du moteur
os.environ["HOSTINGER_EMAIL"] = "contact@josyei.com"             # valeurs factices : aucun envoi réel
os.environ["HOSTINGER_PASSWORD"] = "factice"
sys.path.insert(0, str(Path(__file__).resolve().parent))

import cortex as c  # noqa: E402
import dossier_audit_manager as dam  # noqa: E402
import prompts_audit  # noqa: E402
import regles_absolues  # noqa: E402
import vente  # noqa: E402
import workflow_audit  # noqa: E402
from dossier_audit_manager import DossierAuditManager  # noqa: E402
from prompts_audit import generer_email_audit  # noqa: E402
from regles_absolues import ReglesAbsolues, valider_email_audit  # noqa: E402

vente.MAIL_USER = ""  # simulation : l'email est écrit dans envois_simules\, jamais envoyé

import osint_tools  # noqa: E402


def osint_simule(nom, site, siren=""):
    return {"legal_data": {"status": "ok", "siren": "123456789", "activite": "56.10A",
                           "dirigeants": [{"nom": "X", "qualite": "Gérant"}]},
            "technologies": {"status": "ok", "technologies": [{"nom": "WordPress"}]},
            "google_maps": osint_tools.google_maps_exclu(), "social_profiles": {"status": "ok", "plateformes": []},
            "emails_pro": ["contact@restaurant-test.fr"], "erreurs": [], "timestamp": "2026-10-19T00:00:00+00:00"}


osint_tools.run_full_osint_audit = osint_simule  # aucun appel réseau dans les tests

FAIT = ("sur Google Maps, le 1er résultat pour « restaurant Montmorillon » est Le Bistrot du Marché, avec 412 avis, "
        "et votre entreprise n'apparaît pas dans les 20 premiers résultats")
CORPS_OK = ("Bonjour,\n\nSur Google Maps, le 1er résultat pour « restaurant Montmorillon » est Le Bistrot du Marché, "
            "avec 412 avis, et Restaurant Test n'apparaît pas dans les 20 premiers résultats.\n\n"
            "Les clients qui cherchent un restaurant près de chez eux contactent ceux qu'ils voient en premier. "
            "Chaque réservation qui part chez un concurrent est perdue pour vous.\n\n"
            "Je vous propose un audit gratuit de votre fiche Google pour comprendre ce qui vous empêche d'apparaître. "
            "Répondez simplement à cet email pour le recevoir.")


def analyse_fictive(nom="Restaurant Test", email="contact@restaurant-test.fr"):
    return {"entreprise": {"nom": nom, "secteur": "", "ville": "Montmorillon", "email": email,
                           "email_source": "", "metier": "restaurant", "officiel": None},
            "site": {"site": "https://restaurant-test.fr", "joignable": True, "url_finale": "https://restaurant-test.fr",
                     "https": True, "mobile": False, "meta_description": False, "mentions_legales": True,
                     "google_maps": {"requete": "restaurant Montmorillon", "rang": None, "total": 20,
                                     "premier": {"nom": "Le Bistrot du Marché", "avis": 412, "adresse": "86500"},
                                     "prospect": None, "moyenne_avis": 120, "nb_autres": 20,
                                     "source": "Google Maps (Serper)"}},
            "manques": [FAIT], "services": ["concurrents"], "manques_detail": [[FAIT, "concurrents"]],
            "non_verifie": [], "recherche": "test", "date": "2026-10-19"}


def llm_simule(corps=CORPS_OK, objet="Restaurant Test absent de Google Maps à Montmorillon"):
    appels = []

    def llm(system_prompt, user_prompt, temperature, max_tokens):
        appels.append((system_prompt, user_prompt))
        return {"objet": objet, "corps": corps}
    llm.appels = appels
    return llm


def manager_neuf():
    return DossierAuditManager(str(TMP / f"audit_{uuid.uuid4().hex[:8]}.db"))


def tenant_josy(m):
    return m.assurer_tenant("JOSY EI", email_contact="contact@josyei.com", signature=c.SIGNATURE)


def email_complet(corps=CORPS_OK, objet="Restaurant Test absent de Google Maps"):
    return f"Objet : {objet}\n\n{corps}\n\n{c.SIGNATURE}"


def contexte_ok():
    return {"signature": c.SIGNATURE, "preuves_verifiables": dam.preuves_depuis_audit(analyse_fictive())}


# ----------------------------------------------------------------- 1. zéro prix
def test_validation_zero_prix():
    """Test que tout email avec prix est rejeté"""
    emails_invalides = [
        "Je vous propose un audit pour 9,99€/mois",
        "Notre offre à 19.99 EUR vous permettra...",
        "Abonnement mensuel à 29€ pour...",
        "Forfait annuel avec réduction de 50%",
        "Le coût est modeste.",
        "Nos TARIFS sont en ligne.",
        "Seulement 490 euros HT.",
        "Profitez de nos promotions.",
        # décision JOSY du 19/10/2026 (10:01), étape 3.2 et mots ajoutés
        "Un audit à 9,99€ pour votre fiche.",
        "Un abonnement mensuel vous suffit.",
        "Profitez des soldes.",
        "Notre pack visibilité.",
        "Une formule adaptée.",
        "Seulement 15 par mois.",
        "Objet : Audit gratuit de votre fiche\n\nBonjour,",
    ]
    for email in emails_invalides:
        assert not valider_email_audit(email), f"Email invalide non détecté: {email}"

    emails_valides = [
        "J'ai identifié un problème sur votre fiche Google. Je peux vous faire un diagnostic gratuit.",
        "Je vous propose un diagnostic gratuit.",
        "Un audit de votre fiche Google permettrait de comprendre pourquoi.",
        "Votre site perd des visiteurs. Un audit permettrait de comprendre pourquoi.",
        "Le rappel des horaires compte.",
    ]
    for email in emails_valides:
        assert valider_email_audit(email), f"Email valide rejeté: {email}"

    # Faux positifs connus de la recherche par sous-chaîne demandée par JOSY : rejetés, à éviter à la rédaction.
    faux_positifs = [
        "Vos clients veulent être écoutés.",          # « cout » dans « écoutés »
        "Votre coffre-fort numérique compte.",        # « offre » dans « coffre »
        "Vos clients vous offrent leur confiance.",   # « offre » dans « offrent »
        "Le package de votre site est ancien.",       # « pack » dans « package »
        "Je peux formuler trois constats.",           # « formule » dans « formuler »
    ]
    for email in faux_positifs:
        assert not valider_email_audit(email), f"Faux positif attendu non rejeté: {email}"


# ----------------------------------------------------------------- 2. règles absolues
def test_regles_absolues():
    ctx = contexte_ok()
    assert ReglesAbsolues.valider_email_complet(email_complet(), ctx), ReglesAbsolues.motifs(email_complet(), ctx)
    assert ReglesAbsolues.CANAL_UNIQUE == "email" and ReglesAbsolues.ZERO_PRIX_OBLIGATOIRE
    assert ReglesAbsolues.SIGNATURE_EMAIL in c.SIGNATURE
    cas = {
        "rendez-vous": CORPS_OK + " Prenons rendez-vous.",
        "appel": CORPS_OK + " Je vous appelle demain.",
        "rdv": CORPS_OK + " Un RDV ?",
        "téléphone": CORPS_OK + " Par téléphone si vous préférez.",
        "prix": CORPS_OK + " Le prix est bas.",
        "chiffre inventé": CORPS_OK.replace("412 avis", "412 avis (+35 % en un an)"),
        "concurrent absent": CORPS_OK.replace("Le Bistrot du Marché", "un concurrent"),
        "nombre d'avis absent": CORPS_OK.replace("avec 412 avis, ", ""),
        "trop long": CORPS_OK + "\n" * 2 + "\n".join(["Ligne."] * 10),
    }
    for nom, corps in cas.items():
        assert not ReglesAbsolues.valider_email_complet(email_complet(corps), ctx), f"non rejeté : {nom}"
    sans_signature = f"Objet : x\n\n{CORPS_OK}"
    assert "VETO: signature absente" in ReglesAbsolues.motifs(sans_signature, ctx)
    assert "VETO: argument non vérifiable" in ReglesAbsolues.motifs(email_complet(), {"signature": c.SIGNATURE})
    # « rappel » n'est pas « appel » ; la signature (SIREN, 86, RGPD) ne compte pas comme chiffre inventé
    assert ReglesAbsolues.valider_email_complet(email_complet(CORPS_OK + " Petit rappel : c'est gratuit."), ctx)


# ----------------------------------------------------------------- 3. isolation des tenants
def test_isolation_multi_tenant():
    """Test que les dossiers sont isolés par tenant"""
    manager = manager_neuf()
    tenant1_id = manager.assurer_tenant("TENANT_1")
    tenant2_id = manager.assurer_tenant("TENANT_2")
    dossier1 = manager.creer_dossier_audit(tenant1_id, {'nom': 'Entreprise A', 'site_web': 'https://a.com'})
    dossier2 = manager.creer_dossier_audit(tenant1_id, {'nom': 'Entreprise B', 'site_web': 'https://b.com'})
    dossier3 = manager.creer_dossier_audit(tenant2_id, {'nom': 'Entreprise C', 'site_web': 'https://c.com'})
    dossiers_tenant1 = manager.lister_dossiers_par_tenant(tenant1_id)
    dossiers_tenant2 = manager.lister_dossiers_par_tenant(tenant2_id)
    assert len(dossiers_tenant1) == 2
    assert len(dossiers_tenant2) == 1
    assert dossier3 not in [d['id'] for d in dossiers_tenant1]
    assert {dossier1, dossier2} == {d['id'] for d in dossiers_tenant1}
    try:  # clé étrangère : pas de dossier pour un tenant inexistant
        manager.creer_dossier_audit(str(uuid.uuid4()), {'nom': 'Orphelin'})
        assert False, "dossier orphelin accepté"
    except Exception as exc:
        assert "FOREIGN KEY" in str(exc)
    manager.close()


def test_migration():
    tables = dam.migrer(str(TMP / "migration.db"))
    assert {"tenants", "dossiers_audit", "journal_judiciaire"} <= set(tables)
    assert dam.migrer(str(TMP / "migration.db")) == tables  # idempotente


# ----------------------------------------------------------------- 4. prompt universel
def test_prompt_systeme_universel():
    """Test que le prompt génère des emails sans prix (modèle simulé)"""
    prospect_data = {'nom': 'Boulangerie Test', 'site_web': 'https://boulangerie-test.fr',
                     'metier': 'Boulangerie', 'ville': 'Poitiers'}
    tenant_context = {'analyse_site_web': 'Site lent, pas de HTTPS',
                      'analyse_fiche_google': 'Pas de photos, horaires incomplets',
                      'fuites_acquisition_detectees': ['Faible visibilité locale', "Pas d'avis Google"],
                      'signature': c.SIGNATURE, 'preuves_verifiables': {'fait': 'test', 'elements_obligatoires': []}}
    llm = llm_simule("Bonjour,\n\nVotre fiche Google n'affiche aucune photo. Un audit gratuit vous dirait quoi corriger.")
    email = generer_email_audit(tenant_context, prospect_data, llm=llm)
    assert valider_email_audit(email), "Email contient un prix"
    assert 'audit' in email.lower() or 'diagnostic' in email.lower()
    assert 'contact@josyei.com' in email
    system, user = llm.appels[0]
    assert system == prompts_audit.PROMPT_SYSTEME_AUDIT and "Boulangerie Test" in user and "Poitiers" in user
    for regle in ("GRATUIT", "ZÉRO PRIX", "ZÉRO RDV", "sans mot \"gratuit\" dans l'objet"):
        assert regle in system
    # aucune règle sectorielle : le même prompt sert toute activité
    assert "notaire" not in system.lower() and "naf" not in system.lower()


# ----------------------------------------------------------------- 5. workflow complet (dry-run)
def test_workflow_complet():
    """Workflow complet en dry-run : Telegram et email simulés"""
    m = manager_neuf()
    tenant_id = m.assurer_tenant("TENANT_TEST", site_web="https://test.com", email_contact="contact@josyei.com",
                                 signature=c.SIGNATURE)
    prospect_data = {'nom': 'Restaurant Test', 'site_web': 'https://restaurant-test.fr',
                     'fiche_google': 'https://google.com/maps/place/test', 'metier': 'Restaurant',
                     'ville': 'Montmorillon', 'email_contact': 'contact@restaurant.fr'}
    soumis, envoyes = [], []
    dossier_id = workflow_audit.workflow_audit_complet(
        tenant_id, prospect_data, manager=m, analyse=analyse_fictive(), llm=llm_simule(),
        soumettre=lambda d, e: soumis.append(e) or "approuve",
        envoyer_email=lambda to, e: envoyes.append((to, e)), log=lambda *a: None)
    assert dossier_id is not None
    dossier = m.obtenir(dossier_id)
    assert dossier is not None and dossier['email_genere'] is not None
    assert dossier['email_valide'] == 1 and dossier['statut'] == 'envoye' and dossier['email_envoye'] == 1
    assert len(soumis) == 1 and envoyes == [('contact@restaurant.fr', dossier['email_genere'])]
    assert dossier['probleme_principal'] == FAIT
    m.close()


def test_workflow_veto_avant_telegram():
    """Un email avec prix ne parvient jamais à Telegram"""
    m = manager_neuf()
    tid = tenant_josy(m)
    soumis = []
    res = workflow_audit.workflow_audit_complet(
        tid, {"nom": "Restaurant Test", "email_contact": "contact@b.fr"}, manager=m, analyse=analyse_fictive(),
        llm=llm_simule(CORPS_OK + " Abonnement à 19,99 €."), soumettre=lambda d, e: soumis.append(e) or "approuve",
        log=lambda *a: None)
    assert res is None and soumis == []
    d = m.lister_dossiers_par_tenant(tid)[0]
    assert d["statut"] == "rejete_veto" and d["email_valide"] == 0
    assert any("prix" in x or "abonnement" in x for x in json.loads(d["motifs_veto"]))
    m.close()


def test_workflow_sans_fait_verifie():
    m = manager_neuf()
    tid = tenant_josy(m)
    a = analyse_fictive()
    a["manques"], a["manques_detail"] = [], []
    llm = llm_simule()
    assert workflow_audit.workflow_audit_complet(tid, {"nom": "X"}, manager=m, analyse=a, llm=llm,
                                                 soumettre=lambda d, e: "approuve", log=lambda *a: None) is None
    assert llm.appels == []  # pas de fait vérifié : aucun appel au modèle
    assert m.lister_dossiers_par_tenant(tid)[0]["statut"] == "sans_probleme"
    m.close()


# ----------------------------------------------------------------- 6. intégration dans le Cortex
class FakeTG:
    enabled = True
    chat = "1"

    def __init__(self):
        self.out, self.buttons = [], []

    def send(self, text, buttons=None):
        self.out.append(text)
        self.buttons.append(buttons)
        return len(self.out)

    def alert(self, kind, message):
        self.out.append(f"alerte {kind}")

    def clear_buttons(self, message_id):
        pass

    def call(self, *a, **k):
        return {"ok": True}


def cortex_simule(prospects):
    store = c.Store(":memory:")
    tg = FakeTG()
    store.tg = tg
    cx = c.Cortex(store, tg)
    c.load_prospects = lambda: prospects
    import audit
    audit.audit_prospect = lambda row: analyse_fictive(row["nom"], row["email"])
    prompts_audit.appeler_groq = llm_simule()
    return store, tg, cx


def test_cortex_prospection_validation_envoi():
    prospects = [{"nom": "Restaurant Test", "secteur": "", "ville": "Montmorillon", "email": "contact@restaurant-test.fr",
                  "statut": "", "source": "test", "siren": ""}]
    store, tg, cx = cortex_simule(prospects)
    assert cx.prospect() == []
    p = store.db.execute("SELECT * FROM proposals").fetchone()
    assert p and p["status"] == c.PENDING and p["action_type"] == "cold_email"
    assert "NOUVEL AUDIT À VALIDER" in tg.out[-1] and "Le Bistrot du Marché" in tg.out[-1]
    assert tg.buttons[-1] and tg.buttons[-1][0]["callback_data"].startswith("v:")
    m = DossierAuditManager()
    d = m.db.execute("SELECT * FROM dossiers_audit WHERE action_id=?", (p["action_id"],)).fetchone()
    assert d and d["statut"] == "attente_validation"
    # une seule validation à la fois : pas de second email tant que JOSY n'a pas décidé
    assert cx.prospect() == [] and store.db.execute("SELECT COUNT(*) FROM proposals").fetchone()[0] == 1
    # JOSY valide -> file d'envoi -> envoi simulé -> dossier « envoye »
    cx.decide(p["action_id"][:8], "valide", c.now(), "bouton")
    assert store.db.execute("SELECT statut FROM file_envoi").fetchone()[0] == "en_file"
    vente.process_queue(c, cx)
    assert store.db.execute("SELECT statut FROM file_envoi").fetchone()[0] == "envoye"
    d = m.db.execute("SELECT * FROM dossiers_audit WHERE action_id=?", (p["action_id"],)).fetchone()
    assert d["statut"] == "envoye" and d["email_envoye"] == 1
    m.close()


def test_cortex_refus_josy():
    prospects = [{"nom": "Garage Exemple", "secteur": "", "ville": "Montmorillon", "email": "contact@garage-exemple.fr",
                  "statut": "", "source": "test", "siren": ""}]
    store, tg, cx = cortex_simule(prospects)
    prompts_audit.appeler_groq = llm_simule(CORPS_OK.replace("Restaurant Test", "Garage Exemple"))
    cx.prospect()
    p = store.db.execute("SELECT * FROM proposals").fetchone()
    cx.decide(p["action_id"][:8], "refuse", c.now(), "commande")
    m = DossierAuditManager()
    assert m.db.execute("SELECT statut FROM dossiers_audit WHERE action_id=?", (p["action_id"],)).fetchone()[0] == "refuse"
    m.close()
    vente.setup(store)
    assert store.db.execute("SELECT COUNT(*) FROM file_envoi").fetchone()[0] == 0


def test_envoi_bloque_si_prix_ou_hors_dossier():
    store, tg, cx = cortex_simule([])
    vente.setup(store)
    for kind, body in (("premier", CORPS_OK + "\n\n" + c.SIGNATURE),          # hors dossier d'audit
                       ("reponse", "Bonjour,\n\nLe Cortex coûte 9,99 € par mois.\n\n" + c.SIGNATURE),
                       ("relance", "Bonjour,\n\nNotre offre tient toujours.\n\n" + c.SIGNATURE)):
        store.db.execute("INSERT INTO file_envoi(action_id, kind, company, to_email, subject, body, cree_le) "
                         "VALUES(?,?,?,?,?,?,?)", (str(uuid.uuid4()), kind, "X", "x@exemple.fr", "Objet", body, c.iso(c.now())))
    store.db.commit()
    vente.process_queue(c, cx)
    assert [r[0] for r in store.db.execute("SELECT statut FROM file_envoi")] == ["annule_judiciaire"] * 3


def test_review_mission_zero_prix():
    """Les propositions des missions (publication, article) passent aussi le veto zéro prix."""
    judge = c.Judiciaire({"https://a.fr": ("https://a.fr", "2026-10-19"), "https://b.fr": ("https://b.fr", "2026-10-19")})
    raw = {"mission": "M2_Visibilite", "action_type": "article_blog", "risk_level": "R1",
           "target": {"company": "JOSY EI"}, "content": {"subject": "Site", "body": "Votre site web à 9,99 € par mois."},
           "sources": ["https://a.fr", "https://b.fr"], "justification": "j", "reversibility": "r"}
    prop, motifs = judge.review(raw)
    assert prop is None and any("prix" in m for m in motifs)


def test_cortex_demarre_sans_secteurs():
    """Après les suppressions, le Cortex démarre et cherche des prospects (toutes activités)."""
    base = Path(c.__file__).resolve().parent
    assert not (base / "secteurs.json").exists() and not (base / "livraison.py").exists()
    assert len(c.RESEARCH_TARGETS) > 100 and all(set(q) == {"departement"} for q, _ in c.RESEARCH_TARGETS)
    assert not hasattr(c, "ALLOWED_PRICES") and not hasattr(c, "SECTEURS_PATH")
    store, tg, cx = cortex_simule([])

    class R:
        def raise_for_status(self):
            pass

        def json(self):
            return {"results": [{"siren": "123456789", "nom_complet": "NOTAIRES ASSOCIES", "statut_diffusion": "O",
                                 "activite_principale": "69.10Z", "siege": {"departement": "86", "libelle_commune": "POITIERS"},
                                 "complements": {}}]}
    vu = {}
    real_get = c.requests.get
    c.requests.get = lambda url, **k: vu.update(k.get("params") or {}) or R()
    try:
        cx.collect_companies()
    finally:
        c.requests.get = real_get
    assert "activite_principale" not in vu and vu.get("departement") == "86"
    row = store.db.execute("SELECT * FROM candidates").fetchone()
    assert row and row["secteur"] == "NAF 69.10Z"  # profession réglementée : plus exclue


def test_aucun_tarif_dans_le_code():
    base = Path(c.__file__).resolve().parent
    import re
    motif = re.compile(r"9[,.]99|14[,.]99|19[,.]99|29[,.]99|ALLOWED_PRICES|OFFER_LINE")
    for f in base.glob("*.py"):
        if f.name in ("publier_page.py", Path(__file__).name):
            continue  # publier_page.py : hors périmètre (décision du coordinateur), signalé dans le rapport
        assert not motif.search(f.read_text(encoding="utf-8")), f"tarif restant dans {f.name}"
    assert not motif.search((base / "AGENTS.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and callable(f)]
    ok = 0
    for nom, f in tests:
        try:
            f()
            ok += 1
            print("OK    ", nom)
        except Exception as exc:  # noqa: BLE001
            import traceback
            print("ÉCHEC ", nom, "->", type(exc).__name__, exc)
            traceback.print_exc()
    print(f"\n{ok}/{len(tests)} tests réussis")
    sys.exit(0 if ok == len(tests) else 1)
