"""Tests du module OSINT (aucun réseau : requêtes HTTP, Sherlock et Wappalyzer simulés).

Lancement : python test_osint_tools.py   (ou python -m pytest test_osint_tools.py)
"""

import ast
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import types
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="cortex_osint_"))
os.environ["CORTEX_AUDIT_DB"] = str(TMP / "audit_osint.db")
os.environ["HOSTINGER_EMAIL"] = "contact@josyei.com"
os.environ["HOSTINGER_PASSWORD"] = "factice"
sys.path.insert(0, str(Path(__file__).resolve().parent))

import cortex as c  # noqa: E402
import dossier_audit_manager as dam  # noqa: E402
import osint_tools as o  # noqa: E402
import workflow_audit  # noqa: E402

APPELS_SUBPROCESS = []
_vrai_run = subprocess.run
subprocess.run = lambda *a, **k: APPELS_SUBPROCESS.append(a[0] if a else k.get("args")) or _vrai_run(*a, **k)


class Rep:
    def __init__(self, code=200, data=None, text=""):
        self.status_code, self._d, self.text = code, data, text

    def json(self):
        return self._d

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def avec_get(fake):
    vrai = o.requests.get
    o.requests.get = fake
    return vrai


# ----------------------------------------------------------------- 1. données légales
def test_get_legal_data():
    vrai = avec_get(lambda url, **k: Rep(200, {"results": [
        {"siren": "123456789", "nom_complet": "RESTAURANT TEST", "activite_principale": "56.10A",
         "date_creation": "2015-03-01", "tranche_effectif_salarie": "03",
         "siege": {"siret": "12345678900011", "adresse": "1 rue X 86500 MONTMORILLON"},
         "dirigeants": [{"prenoms": "Jean Paul", "nom": "Martin", "qualite": "Gérant"}]},
        {"siren": "987654321"}]}))
    try:
        r = o.get_legal_data("Restaurant Test")
    finally:
        o.requests.get = vrai
    assert r["status"] == "ok" and r["siren"] == "123456789" and r["activite"] == "56.10A"
    assert r["dirigeants"] == [{"nom": "Jean MARTIN", "qualite": "Gérant"}] and r["siren_siege"] == "12345678900011"
    vrai = avec_get(lambda url, **k: Rep(200, {"results": []}))
    try:
        assert o.get_legal_data("Inconnue")["status"] == "aucun_resultat"
    finally:
        o.requests.get = vrai

    def timeout(url, **k):
        raise o.requests.Timeout("délai dépassé")
    vrai = avec_get(timeout)
    try:
        r = o.get_legal_data("X")
    finally:
        o.requests.get = vrai
    assert r["status"] == "erreur" and "Timeout" in r["detail"]


# ----------------------------------------------------------------- 2. technologies
def test_scan_technologies():
    sys.modules.pop("Wappalyzer", None)
    if not __import__("importlib").util.find_spec("Wappalyzer"):
        r = o.scan_technologies("https://exemple.fr")
        assert r["status"] == "erreur" and "non installé" in r["detail"]
    fake = types.ModuleType("Wappalyzer")

    class W:
        @staticmethod
        def latest():
            return W()

        def analyze_with_versions_and_categories(self, page):
            return {"WordPress": {"categories": ["CMS"], "versions": ["6.4"]}, "PHP": {"categories": ["Langage"]}}

    fake.Wappalyzer = W
    fake.WebPage = types.SimpleNamespace(new_from_url=lambda url, timeout=30: object())
    sys.modules["Wappalyzer"] = fake
    try:
        r = o.scan_technologies("https://exemple.fr")
    finally:
        sys.modules.pop("Wappalyzer", None)
    assert r["status"] == "ok" and [t["nom"] for t in r["technologies"]] == ["PHP", "WordPress"] and r["https"]


# ----------------------------------------------------------------- 3. Google Maps exclu
def test_google_maps_exclu():
    assert o.google_maps_exclu("restaurant Montmorillon")["status"] == "exclu"
    code = ast.get_docstring(ast.parse(Path(o.__file__).read_text(encoding="utf-8")))
    source = Path(o.__file__).read_text(encoding="utf-8").replace(code, "")
    assert "playwright" not in source.lower() and "google.com/maps" not in source.lower()


# ----------------------------------------------------------------- 4. réseaux sociaux (marques seulement)
def test_find_social_profiles():
    for personne in ("Jean Dupont", "Marie Martin", "Sophie", "Lucie Bernard"):
        r = o.find_social_profiles(personne, runner=lambda a: None)
        assert r["status"] == "refuse", personne
    vus = []

    def runner(args):
        vus.append(args)
        return types.SimpleNamespace(stdout="[+] Instagram: https://instagram.com/restauranttest\n"
                                            "[+] Facebook: https://facebook.com/restauranttest\n[-] X: Not Found!\n")
    r = o.find_social_profiles("Restaurant Test", runner=runner)
    assert r["status"] == "ok" and r["identifiant"] == "restauranttest"
    assert [p["plateforme"] for p in r["plateformes"]] == ["Instagram", "Facebook"]
    assert vus[0][0] == "restauranttest"
    for marque in ("Le Bistrot du Marché", "POUPELIN", "Garage Exemple SARL"):
        assert o.find_social_profiles(marque, runner=runner)["status"] == "ok", marque

    def trop_long(args):
        raise subprocess.TimeoutExpired("sherlock", 120)
    assert o.find_social_profiles("Restaurant Test", runner=trop_long)["status"] == "erreur"


# ----------------------------------------------------------------- 5. emails génériques
def test_email_generique():
    assert o.email_generique("contact@exemple.fr", "exemple.fr")
    assert o.email_generique("info@exemple.fr") and o.email_generique("Accueil@Exemple.fr", "www.exemple.fr")
    for perso in ("jean.dupont@exemple.fr", "jdupont@exemple.fr", "contact2@exemple.fr", "contact@exemple2024.fr",
                  "marie@exemple.fr", "pas-un-email"):
        assert not o.email_generique(perso, "exemple.fr"), perso
    assert not o.email_generique("contact@autre.fr", "exemple.fr")


def site_simule(pages, robots="User-agent: *\nAllow: /\n"):
    vus = []

    def get(url):
        vus.append(url)
        if url.endswith("/robots.txt"):
            return Rep(200, text=robots)
        chemin = url.split("exemple.fr/", 1)[-1]
        if chemin in pages:
            v = pages[chemin]
            if isinstance(v, Exception):
                raise v
            return Rep(200, text=v)
        return Rep(404, text="")
    return get, vus


def test_scrape_website_emails():
    get, vus = site_simule({
        "": '<a href="mailto:contact@exemple.fr">écrire</a> jean.dupont@exemple.fr',
        "contact": "Écrivez à info@exemple.fr ou à marie.durand@exemple.fr, contact2@exemple.fr, contact@gmail.com",
        "mentions-legales": RuntimeError("réseau"),
        "a-propos": "direction@exemple.fr",
    })
    pauses = []
    r = o.scrape_website_emails("https://exemple.fr", getter=get, pause=pauses.append)
    assert r["status"] == "ok" and r["emails"] == ["contact@exemple.fr", "info@exemple.fr", "direction@exemple.fr"]
    pages = [u for u in vus if not u.endswith("robots.txt")]
    assert len(pages) <= o.MAX_PAGES and pauses == [1.0] * (len(pages) - 1)
    lignes = sqlite3.connect(o.AUDIT_DB).execute("SELECT detail FROM audit_log").fetchall()
    assert not any("dupont" in d[0] or "marie" in d[0] for d in lignes)  # aucune adresse nominative journalisée


def test_robots_txt_interdit():
    get, vus = site_simule({"": "contact@exemple.fr"}, robots="User-agent: *\nDisallow: /\n")
    assert o.scrape_website_emails("https://exemple.fr", getter=get, pause=lambda s: None) == \
        {"status": "robots_txt_interdit"}
    assert vus == ["https://exemple.fr/robots.txt"]  # aucune page lue
    get, vus = site_simule({"": "x", "contact": "contact@exemple.fr"}, robots="User-agent: *\nDisallow: /contact\n")
    r = o.scrape_website_emails("https://exemple.fr", getter=get, pause=lambda s: None)
    assert "https://exemple.fr/contact" not in vus and r["emails"] == []


# ----------------------------------------------------------------- 6. orchestration
def test_run_full_osint_audit_continue_apres_erreur():
    def casse(*a):
        raise ValueError("panne")
    r = o.run_full_osint_audit("Restaurant Test", "https://exemple.fr", outils={
        "legal": lambda q: {"status": "ok", "siren": "1"},
        "technologies": casse,
        "social": lambda n: {"status": "refuse", "detail": "x"},
        "emails": lambda u: {"status": "ok", "emails": ["contact@exemple.fr"]}})
    assert set(r) == {"legal_data", "technologies", "google_maps", "social_profiles", "emails_pro", "erreurs", "timestamp"}
    assert r["legal_data"]["siren"] == "1" and r["emails_pro"] == ["contact@exemple.fr"]
    assert r["google_maps"]["status"] == "exclu"
    assert {e["etape"] for e in r["erreurs"]} == {"technologies", "social_profiles"}


def test_aucun_scanner_de_vulnerabilites():
    APPELS_SUBPROCESS.clear()
    vrai = avec_get(lambda url, **k: Rep(404, {}, ""))
    try:
        o.run_full_osint_audit("Restaurant Test", "https://exemple.fr")
    finally:
        o.requests.get = vrai
    assert not any("nuclei" in json.dumps(a, default=str).lower() for a in APPELS_SUBPROCESS)
    code = Path(o.__file__).read_text(encoding="utf-8")
    code = code.replace(ast.get_docstring(ast.parse(code)), "")
    assert "nuclei" not in code.lower() and "nmap" not in code.lower()


def test_journal_chaine():
    db = sqlite3.connect(o.AUDIT_DB)
    rows = db.execute("SELECT ts, fonction, cible, statut, detail, prev_hash, hash FROM audit_log ORDER BY id").fetchall()
    assert rows
    prev = "GENESIS"
    import hashlib
    for ts, f, cible, st, det, p, h in rows:
        assert p == prev and h == hashlib.sha256(f"{p}|{ts}|{f}|{cible}|{st}|{det}".encode()).hexdigest()
        prev = h


# ----------------------------------------------------------------- 7. intégration au dossier d'audit
FAIT = ("sur Google Maps, le 1er résultat pour « restaurant Montmorillon » est Le Bistrot du Marché, avec 412 avis, "
        "et votre entreprise n'apparaît pas dans les 20 premiers résultats")
CORPS = ("Bonjour,\n\nSur Google Maps, le 1er résultat pour « restaurant Montmorillon » est Le Bistrot du Marché, "
         "avec 412 avis, et Restaurant Test n'apparaît pas dans les 20 premiers résultats.\n\n"
         "Votre site sous WordPress et votre page Instagram ne suffisent pas à vous faire apparaître.\n\n"
         "Je vous propose un audit gratuit de votre fiche Google. Répondez à cet email pour le recevoir.")


def analyse_fictive():
    return {"entreprise": {"nom": "Restaurant Test", "ville": "Montmorillon", "email": "contact@restaurant-test.fr",
                           "metier": "restaurant", "officiel": None},
            "site": {"joignable": True, "url_finale": "https://restaurant-test.fr", "https": True, "mobile": True,
                     "meta_description": True, "mentions_legales": True,
                     "google_maps": {"requete": "restaurant Montmorillon", "rang": None, "total": 20,
                                     "premier": {"nom": "Le Bistrot du Marché", "avis": 412}, "prospect": None,
                                     "moyenne_avis": 120, "nb_autres": 20, "source": "Google Maps (Serper)"}},
            "manques": [FAIT], "services": ["concurrents"], "manques_detail": [[FAIT, "concurrents"]], "date": "2026-10-19"}


def osint_fictif(nom, site, siren=""):
    return {"legal_data": {"status": "ok", "siren": "123456789", "activite": "56.10A", "date_creation": "2015-03-01",
                           "dirigeants": [{"nom": "Jean MARTIN", "qualite": "Gérant"}]},
            "technologies": {"status": "ok", "technologies": [{"nom": "WordPress"}, {"nom": "Google Analytics"}]},
            "google_maps": o.google_maps_exclu(),
            "social_profiles": {"status": "ok", "plateformes": [{"plateforme": "Instagram", "url": "u"}]},
            "emails_pro": ["contact@restaurant-test.fr"], "erreurs": [], "timestamp": dam._now()}


def nouveau_manager():
    m = dam.DossierAuditManager(str(TMP / f"audit_{uuid.uuid4().hex[:8]}.db"))
    return m, m.assurer_tenant("ENTREPRISE_DEMO", email_contact="contact@josyei.com", signature=c.SIGNATURE)


def llm(corps=CORPS):
    appels = []

    def f(system_prompt, user_prompt, temperature, max_tokens):
        appels.append(user_prompt)
        return {"objet": "Restaurant Test absent de Google Maps", "corps": corps}
    f.appels = appels
    return f


PROSPECT = {"nom": "Restaurant Test", "site_web": "https://restaurant-test.fr", "ville": "Montmorillon",
            "metier": "restaurant", "email_contact": "contact@restaurant-test.fr"}


def test_osint_dans_le_dossier():
    m, tid = nouveau_manager()
    redacteur = llm()
    did = workflow_audit.workflow_audit_complet(tid, PROSPECT, manager=m, analyse=analyse_fictive(), llm=redacteur,
                                                osint=osint_fictif, soumettre=lambda d, e: "en_attente",
                                                log=lambda *a: None)
    d = m.obtenir(did)
    assert d["statut"] == "attente_validation" and d["email_valide"] == 1
    assert d["osint_timestamp"] and json.loads(d["osint_legal_data"])["siren"] == "123456789"
    assert json.loads(d["osint_emails_pro"]) == ["contact@restaurant-test.fr"]
    assert json.loads(d["osint_google_maps"])["status"] == "exclu"
    ecart = datetime.fromisoformat(d["osint_purge_date"]) - datetime.fromisoformat(d["osint_timestamp"])
    assert ecart == timedelta(days=90)
    preuves = json.loads(d["preuves_verifiables"])
    assert preuves["osint"]["technologies"] == ["WordPress", "Google Analytics"]
    assert preuves["osint"]["reseaux"] == ["Instagram"] and preuves["osint"]["legal"]["siren"] == "123456789"
    assert preuves["osint"]["legal"]["dirigeants"] == ["Gérant"]  # minimisation : la qualité, pas le nom
    assert "WordPress" in d["analyse_site_web"] and "Instagram" in d["analyse_site_web"]
    assert "WordPress" in redacteur.appels[0]  # le modèle reçoit les données OSINT
    m.close()


def test_veto_toujours_actif_avec_osint():
    for ajout in (" Le prix est de 49 €.", " Prenons rendez-vous jeudi."):
        m, tid = nouveau_manager()
        soumis = []
        r = workflow_audit.workflow_audit_complet(tid, PROSPECT, manager=m, analyse=analyse_fictive(),
                                                  llm=llm(CORPS + ajout), osint=osint_fictif,
                                                  soumettre=lambda d, e: soumis.append(e) or "approuve",
                                                  log=lambda *a: None)
        assert r is None and soumis == [] and m.lister_dossiers_par_tenant(tid)[0]["statut"] == "rejete_veto"
        m.close()


def test_email_nominatif_jamais_contacte():
    m, tid = nouveau_manager()
    redacteur = llm()
    r = workflow_audit.workflow_audit_complet(tid, dict(PROSPECT, email_contact="jean.martin@restaurant-test.fr"),
                                              manager=m, analyse=analyse_fictive(), llm=redacteur, osint=osint_fictif,
                                              soumettre=lambda d, e: "approuve", log=lambda *a: None)
    assert r is None and redacteur.appels == []
    assert m.lister_dossiers_par_tenant(tid)[0]["statut"] == "email_nominatif"
    m.close()


def test_liste_exclusion():
    m, tid = nouveau_manager()
    m.exclure(domaine="restaurant-test.fr", motif="demande du prospect")
    r = workflow_audit.workflow_audit_complet(tid, PROSPECT, manager=m, analyse=analyse_fictive(), llm=llm(),
                                              osint=osint_fictif, soumettre=lambda d, e: "approuve", log=lambda *a: None)
    assert r is None and m.lister_dossiers_par_tenant(tid)[0]["statut"] == "exclu"
    m.close()
    m, tid = nouveau_manager()
    m.exclure(siren="123456789", motif="test")
    r = workflow_audit.workflow_audit_complet(tid, PROSPECT, manager=m, analyse=analyse_fictive(), llm=llm(),
                                              osint=osint_fictif, soumettre=lambda d, e: "approuve", log=lambda *a: None)
    assert r is None and m.lister_dossiers_par_tenant(tid)[0]["statut"] == "exclu"  # SIREN trouvé par l'OSINT
    m.close()


def test_purge_90_jours():
    m, tid = nouveau_manager()
    ancien = workflow_audit.workflow_audit_complet(tid, PROSPECT, manager=m, analyse=analyse_fictive(), llm=llm(),
                                                   osint=osint_fictif, soumettre=lambda d, e: "en_attente",
                                                   log=lambda *a: None)
    recent = workflow_audit.workflow_audit_complet(tid, PROSPECT, manager=m, analyse=analyse_fictive(), llm=llm(),
                                                   osint=osint_fictif, soumettre=lambda d, e: "en_attente",
                                                   log=lambda *a: None)
    vieux = (datetime.now(timezone.utc) - timedelta(days=91)).replace(microsecond=0).isoformat()
    m.db.execute("UPDATE dossiers_audit SET osint_timestamp=?, osint_purge_date=? WHERE id=?", (vieux, (datetime.fromisoformat(vieux) + timedelta(days=90)).isoformat(), ancien))
    m.db.commit()
    assert m.purger_osint() == 1
    a, r = m.obtenir(ancien), m.obtenir(recent)
    assert a["osint_legal_data"] is None and a["osint_technologies"] is None and a["preuves_verifiables"] is None
    assert a["probleme_principal"] == FAIT and a["analyse_site_web"]  # conclusions conservées
    assert r["osint_legal_data"] and r["preuves_verifiables"]
    m.close()


def test_migration_base_existante():
    path = str(TMP / "ancienne.db")
    db = sqlite3.connect(path)  # base créée avec le schéma d'avant le module OSINT
    ancien = dam.SCHEMA
    for col in dam.OSINT_COLONNES:
        ancien = ancien.replace(f"    {col} TEXT,\n", "")
    assert "osint_" not in ancien
    db.executescript(ancien)
    db.commit()
    db.close()
    cols = {r[1] for r in dam.connecter(path).execute("PRAGMA table_info(dossiers_audit)")}
    assert set(dam.OSINT_COLONNES) <= cols
    assert {"audit_log", "exclusion"} <= set(dam.migrer(path))


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
