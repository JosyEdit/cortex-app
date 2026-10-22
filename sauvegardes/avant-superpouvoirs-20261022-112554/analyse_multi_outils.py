"""Cerveau orchestrateur : outils d'analyse que l'onglet Discuter appelle avant de répondre.

Chaque outil renvoie un dict {"outil", "source", "ok", "donnees" | "erreur"} : la réponse finale
cite ces sources et dit ce qui manque quand un outil échoue (rien n'est inventé, I1).

  analyse_site_web(url)              : audit technique (requests + BeautifulSoup + Playwright)
  analyse_entreprise_siren(q)        : registre public de l'État (+ Bourse si société cotée)
  analyse_concurrence(ville, secteur): entreprises actives du même secteur dans la ville (registre)
  analyse_osint_entreprise(q, url)   : sources publiques sur une ENTREPRISE (registre, site, TLS)

Choix (21/10/2026) : « webaudit » et « pyseoa » ne sont pas installés (paquets récents d'un seul
auteur, peu de versions : risque non vérifié) ; l'audit est fait avec des outils reconnus.
Pas d'instaloader (réseaux sociaux désactivés pour le Cortex, extraction interdite par leurs
conditions), pas de profilage de personnes (RGPD). Pas de scan réseau (nmap) depuis le chat :
uniquement sur ses propres équipements, et à la main.
"""

import re
import socket
import ssl
import time
import urllib.parse
from datetime import datetime, timezone

import requests

import analyse_entreprise as AE

UA = {"User-Agent": "Mozilla/5.0 (JOSY-EI-Cortex audit; +https://josyei.com)", "Accept-Language": "fr,en;q=0.8"}


def adresse_publique(hote):
    import ipaddress
    try:
        infos = socket.getaddrinfo(hote, None)
    except OSError:
        return False
    return all(not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast)
               for ip in (ipaddress.ip_address(i[4][0]) for i in infos))


def _resultat(outil, source, donnees=None, erreur=None):
    return {"outil": outil, "source": source, "ok": erreur is None, "donnees": donnees or {},
            "erreur": erreur}


def _public(url):
    hote = urllib.parse.urlparse(url).hostname or ""
    if not hote:
        raise ValueError("adresse invalide")
    if not adresse_publique(hote):  # pas d'adresse interne (ce PC, box, réseau local)
        raise ValueError("adresse interne refusée")
    if AE.RESEAUX.search(hote):
        raise ValueError("réseau social : extraction automatisée interdite par ses conditions")
    return hote


# --------------------------------------------------------------------------- site web
def analyse_site_web(url):
    """Audit technique : temps de réponse, HTTPS, balises SEO, liens brisés, robots/sitemap,
    rendu réel (Playwright) et certificat TLS."""
    if not re.match(r"https?://", url or ""):
        url = "https://" + (url or "").strip("/ ")
    try:
        hote = _public(url)
        t0 = time.perf_counter()
        r = requests.get(url, headers=UA, timeout=20, allow_redirects=True)
        duree = time.perf_counter() - t0
    except Exception as exc:
        return _resultat("audit_site", url, erreur=str(exc) if isinstance(exc, ValueError) else type(exc).__name__)
    from bs4 import BeautifulSoup
    soupe = BeautifulSoup(r.content, "html.parser")
    meta = lambda nom: (soupe.find("meta", attrs={"name": nom}) or {}).get("content")  # noqa: E731
    titre = soupe.title.get_text(strip=True) if soupe.title else ""
    imgs = soupe.find_all("img")
    d = {
        "url_finale": r.url, "statut_http": r.status_code, "https": r.url.startswith("https://"),
        "redirections": len(r.history), "temps_reponse_s": round(duree, 2),
        "poids_html_ko": round(len(r.content) / 1024, 1),
        "titre": titre, "longueur_titre": len(titre),
        "meta_description": bool(meta("description")),
        "longueur_description": len(meta("description") or ""),
        "h1": len(soupe.find_all("h1")), "h2": len(soupe.find_all("h2")),
        "images": len(imgs), "images_sans_alt": sum(1 for i in imgs if not (i.get("alt") or "").strip()),
        "viewport_mobile": bool(meta("viewport")),
        "langue": (soupe.html or {}).get("lang") if soupe.html else None,
        "canonical": bool(soupe.find("link", rel="canonical")),
        "robots_noindex": "noindex" in (meta("robots") or "").lower(),
        "donnees_structurees": bool(soupe.find("script", type="application/ld+json")),
        "mentions_legales": bool(re.search(r"mentions\s+l[ée]gales", soupe.get_text(" "), re.I)),
    }
    base = f"{urllib.parse.urlparse(r.url).scheme}://{urllib.parse.urlparse(r.url).netloc}"
    for fichier in ("robots.txt", "sitemap.xml"):
        try:
            d[fichier] = requests.get(f"{base}/{fichier}", headers=UA, timeout=10).status_code == 200
        except Exception:
            d[fichier] = None
    liens = []
    for a in soupe.find_all("a", href=True):
        lien = urllib.parse.urljoin(r.url, a["href"]).split("#")[0]
        if lien.startswith("http") and lien not in liens:
            liens.append(lien)
    def tester(lien):
        hote_lien = (urllib.parse.urlparse(lien).hostname or "").removeprefix("www.")
        if AE.RESEAUX.search(hote_lien) or hote_lien.startswith(("g.page", "maps.app.goo.gl", "google.")):
            return None  # réseaux sociaux et Google bloquent les robots : non vérifiables, pas « brisés »
        try:
            rl = requests.head(lien, headers=UA, timeout=6, allow_redirects=True)
            if rl.status_code == 405:
                rl = requests.get(lien, headers=UA, timeout=6, stream=True)
            return f"{lien} ({rl.status_code})" if rl.status_code >= 400 else None
        except Exception:
            return f"{lien} (injoignable)"
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as pool:  # échantillon de 20 liens, testés en parallèle
        brises = [b for b in pool.map(tester, liens[:20]) if b]
    d.update({"liens_trouves": len(liens), "liens_testes": min(len(liens), 20), "liens_brises": brises[:10]})
    d.update(_rendu_navigateur(r.url))
    d.update(_certificat(hote))
    return _resultat("audit_site", r.url, d)


def _rendu_navigateur(url):
    """Temps de chargement réel mesuré par Playwright (Chrome du PC)."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            nav = p.chromium.launch(channel="chrome", headless=True)
            try:
                page = nav.new_page(locale="fr-FR")
                page.goto(url, timeout=30000, wait_until="load")
                t = page.evaluate("() => { const n = performance.getEntriesByType('navigation')[0];"
                                  " return n ? {dom: n.domContentLoadedEventEnd, load: n.loadEventEnd} : null; }")
                ressources = page.evaluate("() => performance.getEntriesByType('resource').length")
            finally:
                nav.close()
        if not t:
            return {"rendu_navigateur": "mesure indisponible"}
        return {"chargement_dom_s": round(t["dom"] / 1000, 2), "chargement_complet_s": round(t["load"] / 1000, 2),
                "ressources_chargees": ressources}
    except Exception as exc:
        return {"rendu_navigateur": f"échec ({type(exc).__name__})"}


def _certificat(hote):
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hote, 443), timeout=8) as s, ctx.wrap_socket(s, server_hostname=hote) as t:
            cert = t.getpeercert()
        fin = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        emetteur = dict(x[0] for x in cert.get("issuer", ())).get("organizationName")
        return {"certificat_valide_jusqua": fin.date().isoformat(),
                "certificat_jours_restants": (fin - datetime.now(timezone.utc)).days,
                "certificat_emetteur": emetteur}
    except Exception as exc:
        return {"certificat": f"non vérifié ({type(exc).__name__})"}


# --------------------------------------------------------------------------- entreprise
def analyse_entreprise_siren(nom_ou_siren):
    """Registre public (SIREN, activité, effectif, finances publiées, dirigeants) + Bourse si cotée."""
    try:
        e, n = AE.registre(nom_ou_siren)
    except Exception as exc:
        try:  # l'API publique a parfois un incident passager : un second essai
            time.sleep(1.5)
            e, n = AE.registre(nom_ou_siren)
        except Exception:
            return [_resultat("registre_public", AE.API, erreur=type(exc).__name__)]
    if not e:
        return [_resultat("registre_public", AE.API, erreur=f"aucune entreprise trouvée pour « {nom_ou_siren} »")]
    siege = e.get("siege") or {}
    tranche = e.get("tranche_effectif_salarie") or siege.get("tranche_effectif_salarie")
    d = {"nom": e.get("nom_complet"), "siren": e.get("siren"),
         "etat": "active" if e.get("etat_administratif") == "A" else "fermée",
         "naf": e.get("activite_principale"), "creation": e.get("date_creation"),
         "siege": f"{siege.get('code_postal', '')} {siege.get('libelle_commune', '')}".strip(),
         "code_postal": siege.get("code_postal"), "commune": siege.get("libelle_commune"),
         "effectif_declare": AE.TRANCHES.get(tranche, "non publié"),
         "annee_effectif": e.get("annee_tranche_effectif_salarie"),
         "finances": AE._finances(e), "dirigeants": AE._dirigeants(e),
         "etablissements": e.get("nombre_etablissements"),
         "resultats_homonymes_registre": n}
    resultats = [_resultat("registre_public", "recherche-entreprises.api.gouv.fr", d)]
    resultats.append(_bourse(d["nom"], tranche))
    return resultats


def _bourse(nom, tranche):
    """Données boursières seulement pour une grande entreprise : une TPE/PME n'est pas cotée."""
    if tranche not in ("41", "42", "51", "52", "53"):
        return _resultat("bourse_yfinance", "Yahoo Finance", erreur="sans objet : entreprise non cotée (taille TPE/PME)")
    try:
        import yfinance as yf
        cotes = [q for q in (yf.Search(nom, max_results=5).quotes or []) if q.get("quoteType") == "EQUITY"]
        if not cotes:
            return _resultat("bourse_yfinance", "Yahoo Finance", erreur="aucune cotation trouvée")
        sym = cotes[0]["symbol"]
        info = yf.Ticker(sym).fast_info
        return _resultat("bourse_yfinance", f"Yahoo Finance ({sym})", {
            "symbole": sym, "place": cotes[0].get("exchange"), "dernier_cours": round(info.last_price, 2),
            "devise": info.currency, "capitalisation": int(info.market_cap or 0)})
    except Exception as exc:
        return _resultat("bourse_yfinance", "Yahoo Finance", erreur=type(exc).__name__)


# --------------------------------------------------------------------------- concurrence
def analyse_concurrence(ville, secteur, naf=None, code_postal=None):
    """Entreprises actives du secteur dans la ville, d'après le registre public (pas de moteur de
    recherche aspiré : leurs conditions l'interdisent et ils bloquent les robots)."""
    params = {"q": f"{secteur} {ville}".strip(), "etat_administratif": "A", "per_page": 15, "page": 1}
    if naf:
        params = {"activite_principale": naf, "etat_administratif": "A", "per_page": 15, "page": 1}
        if code_postal:
            params["code_postal"] = code_postal
    try:
        r = requests.get(AE.API, params=params, timeout=20, headers=UA)
        r.raise_for_status()
        corps = r.json()
    except Exception as exc:
        return _resultat("concurrence_registre", AE.API, erreur=type(exc).__name__)
    liste = [{"nom": e.get("nom_complet"), "siren": e.get("siren"),
              "commune": (e.get("siege") or {}).get("libelle_commune"),
              "effectif": AE.TRANCHES.get(e.get("tranche_effectif_salarie"), "non publié"),
              "creation": e.get("date_creation")} for e in corps.get("results") or []]
    return _resultat("concurrence_registre", "recherche-entreprises.api.gouv.fr",
                     {"critere": f"NAF {naf}, {code_postal}" if naf else params["q"],
                      "total_registre": corps.get("total_results"), "exemples": liste[:10]})


# --------------------------------------------------------------------------- OSINT (entreprises)
def analyse_osint_entreprise(nom, url=None):
    """Sources publiques sur une entreprise : registre, site (contenu et technique). Aucune
    recherche sur des personnes."""
    resultats = analyse_entreprise_siren(nom) if nom else []
    if url:
        resultats.append(analyse_site_web(url))
    return resultats


# --------------------------------------------------------------------------- clients perdus
def diagnostic_entonnoir(db, jours=30):
    """Où se perdent les prospects, d'après cortex.db : propositions, envois, réponses, opposition."""
    from datetime import timedelta
    depuis = (datetime.now(timezone.utc) - timedelta(days=jours)).replace(microsecond=0).isoformat()
    q = lambda sql, *a: db.execute(sql, a).fetchone()[0]  # noqa: E731
    try:
        props = dict(db.execute("SELECT status, COUNT(*) FROM proposals WHERE created_at>=? GROUP BY status",
                                (depuis,)).fetchall())
        envois = dict(db.execute("SELECT kind, COUNT(*) FROM envois WHERE sent_at>=? GROUP BY kind",
                                 (depuis,)).fetchall())
        classes = dict(db.execute("SELECT classe, COUNT(*) FROM reponses WHERE recu_le>=? GROUP BY classe",
                                  (depuis,)).fetchall())
        file_ = dict(db.execute("SELECT statut, COUNT(*) FROM file_envoi WHERE cree_le>=? GROUP BY statut",
                                (depuis,)).fetchall())
        statuts = dict(db.execute("SELECT statut, COUNT(*) FROM entreprises GROUP BY statut").fetchall())
        d = {"periode": f"{jours} derniers jours",
             "propositions_creees": sum(props.values()),
             "propositions_expirees_sans_decision": props.get("refuse_timeout", 0),
             "propositions_refusees": sum(v for k, v in props.items() if k.startswith("refuse") and k != "refuse_timeout"),
             "emails_envoyes": sum(envois.values()), "dont_premiers": envois.get("premier", 0),
             "dont_relances": envois.get("relance", 0),
             "reponses_recues": sum(v for k, v in classes.items() if k not in ("fondateur", "usurpation_possible")),
             "reponses_par_type": {k: v for k, v in classes.items() if k not in ("fondateur", "usurpation_possible")},
             "envois_annules_par_controle": sum(v for k, v in file_.items() if k.startswith("annule")),
             "prospects_par_statut": statuts,
             "opposition_total": q("SELECT COUNT(*) FROM liste_opposition"),
             "derniers_envois_reussis": db.execute("SELECT MAX(sent_at) FROM envois").fetchone()[0]}
        d["reponses_par_type"] = "; ".join(f"{k} {v}" for k, v in d["reponses_par_type"].items()) or "aucune"
        d["prospects_par_statut"] = "; ".join(f"{k} {v}" for k, v in statuts.items())
        return _resultat("entonnoir_cortex_db", "cortex.db (tes données de prospection)", d)
    except Exception as exc:
        return _resultat("entonnoir_cortex_db", "cortex.db", erreur=type(exc).__name__)


# --------------------------------------------------------------------------- orchestration
INTENTIONS = (
    ("clients", re.compile(r"perd[s]?\s+(des\s+)?clients|perte\s+de\s+clients|pourquoi.*clients", re.I)),
    ("audit_site", re.compile(r"\b(audite[rz]?|audit)\b.*\b(site|https?://)", re.I | re.S)),
    ("concurrence", re.compile(r"\bconcurren(ce|ts?)\b", re.I)),
    ("osint", re.compile(r"\bosint\b", re.I)),
    ("entreprise", AE.DEMANDE_RE),
)


def detecter(texte):
    """Intention d'analyse du message, ou None (conversation normale)."""
    for nom, rx in INTENTIONS:
        if rx.search(texte or "") if nom != "entreprise" else rx.match(texte or ""):
            return nom
    return None


def _nom_cible(texte):
    """Nom d'entreprise dans « … la société X », « … de X », ou le texte sans l'URL."""
    m = AE.DEMANDE_RE.match(texte)
    if m:
        return AE.demande(texte)[0]
    m = re.search(r"(?:soci[ée]t[ée]|entreprise|osint (?:sur|de)?)\s+(.+)", texte, re.I)
    nom = (m.group(1) if m else texte)
    nom = re.sub(r"https?://\S+", "", nom)
    return nom.strip(" ,.;:?!«»\"'") or None


def executer(texte, db=None):
    """Lance les outils selon l'intention. Renvoie (intention, [résultats]) ; au moins deux outils
    quand c'est possible (règle de réflexion croisée)."""
    intention = detecter(texte)
    if not intention:
        return None, []
    url = (re.search(r"https?://\S+", texte) or [None])[0]
    url = url.rstrip(".,;:!?)") if url else None
    res = []
    if intention == "clients":  # base de prospection + site de JOSY EI (la porte d'entrée des clients)
        if db is not None:
            res.append(diagnostic_entonnoir(db))
        res.append(analyse_site_web(url or "https://josyei.com"))
    elif intention == "audit_site":
        if not url:
            m = re.search(r"\b([a-z0-9-]+\.(?:fr|com|net|org|eu|io|bzh))\b", texte, re.I)
            url = ("https://" + m.group(1)) if m else None
        if not url:
            return intention, [_resultat("audit_site", "—", erreur="aucune adresse de site dans la demande")]
        res.append(analyse_site_web(url))
        domaine = (urllib.parse.urlparse(url).hostname or "").removeprefix("www.").split(".")[0]
        for r in analyse_entreprise_siren(domaine.replace("-", " ")):  # croisement : qui est derrière ?
            if r["ok"]:
                r["donnees"]["rapprochement"] = "trouvé par le nom de domaine : à confirmer"
            res.append(r)
    elif intention == "concurrence":
        m = re.search(r"(?:concurren\w*)\s+(?:des?\s+|du\s+|pour\s+|en\s+)?(.+?)\s+(?:à|a|sur|dans|autour de)\s+([\w\s'-]+)",
                      texte, re.I)
        secteur, ville = (m.group(1), m.group(2)) if m else (texte, "")
        res.append(analyse_concurrence(ville.strip(" ?."), secteur.strip()))
        if url:
            res.append(analyse_site_web(url))
    elif intention == "osint":
        res += analyse_osint_entreprise(_nom_cible(texte), url)
    else:  # entreprise
        nom, url = AE.demande(texte)
        res += analyse_entreprise_siren(nom) if nom else []
        reg = next((r for r in res if r["outil"] == "registre_public" and r["ok"]), None)
        if reg and reg["donnees"].get("naf") and reg["donnees"].get("code_postal"):
            res.append(analyse_concurrence(reg["donnees"].get("commune") or "", "",
                                           naf=reg["donnees"]["naf"], code_postal=reg["donnees"]["code_postal"]))
        if url:
            res.append(analyse_site_web(url))
    return intention, res


def resume_outils(resultats):
    """Bloc lisible et sourcé, outil par outil (affiché tel quel, avant la synthèse de Groq)."""
    blocs = []
    for r in resultats:
        tete = f"[{r['outil']}] source : {r['source']}"
        if not r["ok"]:
            blocs.append(f"{tete}\n  non disponible : {r['erreur']}")
            continue
        lignes = []
        for k, v in r["donnees"].items():
            if isinstance(v, list):
                v = "aucun" if not v else "; ".join(
                    (f"{x.get('nom')} ({x.get('commune')}, effectif {x.get('effectif')})" if isinstance(x, dict) else str(x))
                    for x in v[:10])
            lignes.append(f"  {k.replace('_', ' ')} : {v}")
        blocs.append(tete + "\n" + "\n".join(lignes))
    return "\n\n".join(blocs)
