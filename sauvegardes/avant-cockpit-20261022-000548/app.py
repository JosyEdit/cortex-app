#!/usr/bin/env python3
"""Cortex — interface locale (navigateur, 127.0.0.1 uniquement).

Ce que c'est : une fenêtre sur le Cortex, pas un deuxième Cortex. Elle réutilise
`fondateur.py` et `cortex.py` pour agir — aucune logique n'est dupliquée :

  - « Aujourd'hui »  : le plan du jour, ses créneaux, sa priorité, ses alertes ;
  - « Ma vie »       : le profil de vie et ce qui manque encore ;
  - « À valider »    : les propositions en attente (même chemin que /valider sur
                       Telegram : I2, I10 et la file d'envoi sont respectés) ;
  - « Journal »      : les derniers événements, pour vérifier ce qui a été fait.

Comment lancer :

    python app.py                 # puis ouvre le lien affiché
    python cortex-app.bat         # ou double-clic sur le raccourci Windows

Sécurité (trois verrous, parce qu'un port local reste joignable par une page web) :

  1. écoute sur 127.0.0.1 seulement — jamais 0.0.0.0, donc rien sur le réseau ;
  2. en-tête Host vérifié (127.0.0.1 / localhost) — bloque le rebinding DNS ;
  3. jeton secret dans l'URL, lu ou créé dans `.app-token` (ignoré par git).

Aucun message n'est envoyé sur Telegram par cette interface : ce qu'elle fait est
écrit dans la console et dans le journal local (I1).
"""

import argparse
import html
import json
import re
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import cortex as C          # noqa: E402
import fondateur as F       # noqa: E402

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
ETIQUETTE = {"deep": "travail profond", "admin": "administratif", "business": "business",
             "perso": "perso", "sante": "santé", "repos": "repos"}


# --------------------------------------------------------------------------
# Le Cortex sans Telegram : ce que l'interface fait s'affiche dans la console
# --------------------------------------------------------------------------
class Console:
    """Tient lieu de Telegram pour les fonctions réutilisées. Garde les messages."""

    def __init__(self):
        self.messages = []

    def send(self, texte, buttons=None):
        propre = html.unescape(re.sub(r"<[^>]+>", " ", texte or ""))
        propre = re.sub(r"\s+", " ", propre).strip()
        self.messages.append(propre)
        _imprimer("[cortex] " + propre[:300])
        return None

    def alert(self, kind, message):
        self.send(f"erreur {kind} : {message}")

    def clear_buttons(self, message_id):
        pass


def _imprimer(texte):
    """La console Windows (cp1252) refuse les emoji : ça ne doit jamais casser une action."""
    try:
        print(texte)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "ascii"
        print(texte.encode(enc, "replace").decode(enc, "replace"))


class Interface:
    """Ce que `fondateur.py` attend : une base (`.s`) et un canal (`.tg`)."""

    def __init__(self, store, console):
        self.s, self.tg = store, console


def ouvrir_base():
    return C.Store(C.DB_PATH)


def dernier(console, defaut="C'est fait."):
    return console.messages[-1] if console.messages else defaut


# --------------------------------------------------------------------------
# Gestion des actions (POST) — tout passe par les fonctions existantes
# --------------------------------------------------------------------------
def agir(store, console, quoi, params):
    """Exécute une action de l'interface. Renvoie (message, page de retour)."""
    auj = C.now().astimezone(C.PARIS).date().isoformat()
    cx = Interface(store, console)

    if quoi in ("plan", "fait", "reporte", "off", "vie"):
        commande = {"plan": "/jour", "off": "/jour", "fait": "/fait",
                    "reporte": "/reporte", "vie": "/vie"}[quoi]
        args = {"plan": [], "off": ["off"], "fait": [params.get("n", "")],
                "reporte": [params.get("n", "")] + (params.get("raison", "").split() or []),
                "vie": ([params["champ"], ":"] + params.get("texte", "").split())
                if params.get("champ") else params.get("texte", "").split()}[quoi]
        F.commande(C, cx, commande, args, f"{commande} app")
        return dernier(console), ("vie" if quoi == "vie" else "jour")

    if quoi in ("valider", "refuser"):
        # Même chemin que /valider sur Telegram : decide() -> execute() -> file d'envoi.
        cortex = C.Cortex(store, console)
        cortex.decide(params.get("id", ""), "valide" if quoi == "valider" else "refuse",
                      C.now(), "application locale", motif=params.get("motif", "")[:300])
        return dernier(console, "Décision enregistrée."), "valider"

    return "Action inconnue.", "jour"


# --------------------------------------------------------------------------
# Rendu HTML (aucun gabarit externe, aucune dépendance)
# --------------------------------------------------------------------------
CSS = """
:root{color-scheme:dark light}
*{box-sizing:border-box}
body{margin:0;background:#12141a;color:#e8eaf0;font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
header{position:sticky;top:0;background:#181b23;border-bottom:1px solid #262a35;padding:10px 14px;
       display:flex;gap:10px;align-items:center;flex-wrap:wrap}
header b{font-size:15px;letter-spacing:.3px}
nav a{color:#9fb4d8;text-decoration:none;padding:6px 10px;border-radius:8px;font-size:14px}
nav a.on{background:#243049;color:#fff}
main{max-width:820px;margin:0 auto;padding:16px 14px 60px}
h1{font-size:20px;margin:6px 0 2px}
h2{font-size:15px;margin:22px 0 8px;color:#9fb4d8;text-transform:uppercase;letter-spacing:.5px}
.card{background:#181b23;border:1px solid #262a35;border-radius:12px;padding:14px;margin:10px 0}
.prio{border-left:4px solid #5b9dff}
.cr{display:flex;gap:12px;align-items:flex-start;padding:10px 0;border-bottom:1px solid #232733}
.cr:last-child{border-bottom:0}
.heure{font-variant-numeric:tabular-nums;color:#c9d4e8;min-width:104px;font-weight:600}
.tag{font-size:12px;color:#8ea0bd;border:1px solid #313848;border-radius:999px;padding:1px 8px}
.fait{opacity:.55;text-decoration:line-through}
.reporte{opacity:.75}
.det{color:#a8b3c7;font-size:14px}
.btn{display:inline-block;background:#243049;color:#dce6f7;border:1px solid #34425e;border-radius:9px;
     padding:7px 12px;font-size:14px;text-decoration:none;cursor:pointer}
.btn.ok{background:#1d3a2a;border-color:#2f6046;color:#c8f0da}
.btn.no{background:#3a1f22;border-color:#6b3238;color:#f6d3d6}
.btn.ghost{background:transparent}
form{display:inline}
.m{background:#1d3a2a;border:1px solid #2f6046;color:#d8f5e5;padding:10px 12px;border-radius:10px;margin:10px 0}
.warn{background:#3a2f1a;border:1px solid #6b552a;color:#f6e6c8;padding:10px 12px;border-radius:10px}
.mut{color:#8b97ad;font-size:14px}
table{width:100%;border-collapse:collapse;font-size:14px}
td,th{text-align:left;padding:6px 8px;border-bottom:1px solid #232733;vertical-align:top}
input[type=text],textarea,select{width:100%;background:#12141a;color:#e8eaf0;border:1px solid #313848;
     border-radius:9px;padding:9px}
textarea{min-height:70px;font-family:inherit}
label{display:block;font-size:13px;color:#9fb4d8;margin:8px 0 3px}
"""


def esc(x):
    return html.escape(str(x if x is not None else ""))


def page(titre, corps, actif, token, message=None):
    onglets = [("jour", "Aujourd'hui", "/"), ("vie", "Ma vie", "/vie"),
               ("valider", "À valider", "/valider"), ("journal", "Journal", "/journal")]
    nav = "".join(f'<a class="{"on" if cle == actif else ""}" href="{url}?t={token}">{nom}</a>'
                  for cle, nom, url in onglets)
    ou = f'<div class="m">{esc(message)}</div>' if message else ""
    return ("<!doctype html><html lang=fr><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{esc(titre)} — Cortex</title><style>{CSS}</style></head><body>"
            f"<header><b>🧠 Cortex</b><nav>{nav}</nav></header><main>{ou}{corps}</main></body></html>")


def vue_jour(store, token, message=None):
    auj = C.now().astimezone(C.PARIS)
    jour = auj.date().isoformat()
    plan = F.plan_du_jour(store, jour)
    p = F.profil(store)
    question = F.question_en_attente(C, store, p) or None
    q = next((c for c in F.CHAMPS if c[0] == question), None)
    if plan is None:
        corps = (f"<h1>Aujourd'hui</h1><p class=mut>{esc(JOURS[auj.weekday()])} {auj.day} "
                 f"{esc(MOIS[auj.month - 1])} · {auj.strftime('%H:%M')}</p>"
                 "<div class=card><b>Aucun plan pour aujourd'hui.</b>"
                 "<p class=mut>Le Cortex le construit tout seul au premier passage après "
                 f"<b>{esc(p.get('preferences.plan_heure') or '07:30')}</b>. "
                 "Tu peux le demander maintenant.</p>"
                 f"<form method=post action='/action?t={token}'>"
                 "<input type=hidden name=quoi value=plan>"
                 "<button class='btn ok'>Construire ma journée</button></form>"
                 f"<form method=post action='/action?t={token}'>"
                 "<input type=hidden name=quoi value=off>"
                 "<button class='btn ghost'>Journée off</button></form></div>")
        return page("Aujourd'hui", corps, "jour", token, message)

    prio = plan.get("priorite_absolue") or {}
    h = [f"<h1>{esc(JOURS[auj.weekday()]).capitalize()} {auj.day} {esc(MOIS[auj.month - 1])}</h1>"]
    if plan.get("resume"):
        h.append(f"<p class=mut>{esc(plan['resume'])}</p>")
    if prio.get("titre"):
        h.append("<div class='card prio'><h2 style='margin-top:0'>Priorité absolue</h2>"
                 f"<b>{esc(prio['titre'])}</b>"
                 + (f" · <span class=tag>{esc(prio['creneau'])}</span>" if prio.get("creneau") else "")
                 + (f"<p class=det>{esc(prio['pourquoi'])}</p>" if prio.get("pourquoi") else "")
                 + "</div>")
    h.append("<h2>Créneaux</h2><div class=card>")
    for i, cr in enumerate(plan.get("creneaux", []), 1):
        statut = cr.get("statut")
        classe = {"fait": "fait", "reporte": "reporte"}.get(statut, "")
        h.append(f"<div class='cr {classe}'><div class=heure>{esc(cr['debut'])}–{esc(cr['fin'])}</div>"
                 f"<div style='flex:1'><b>{i}. {esc(cr['titre'])}</b> "
                 f"<span class=tag>{esc(ETIQUETTE.get(cr['type'], cr['type']))}</span>"
                 + (" <span class=tag>obligatoire</span>" if cr.get("obligatoire") else "")
                 + (" <span class=tag>fait</span>" if statut == "fait" else "")
                 + (" <span class=tag>reporté</span>" if statut == "reporte" else "")
                 + (f"<div class=det>{esc(cr['details'])}</div>" if cr.get("details") else "")
                 + "<div style='margin-top:6px'>"
                 f"<form method=post action='/action?t={token}'><input type=hidden name=quoi value=fait>"
                 f"<input type=hidden name=n value='{i}'><button class='btn ok'>Fait</button></form> "
                 f"<form method=post action='/action?t={token}'><input type=hidden name=quoi value=reporte>"
                 f"<input type=hidden name=n value='{i}'><button class='btn'>Reporté</button></form>"
                 "</div></div></div>")
    h.append("</div>")
    details = []
    if plan.get("charge_min"):
        details.append(f"Charge de travail prévue : <b>{plan['charge_min'] // 60} h "
                       f"{plan['charge_min'] % 60:02d}</b> sur une capacité de "
                       f"{F.capacite_minutes(p) // 60} h {F.capacite_minutes(p) % 60:02d}")
    for titre, cle in (("Ce que je prends en charge", "ce_que_je_prends_en_charge"),
                       ("Ce que je laisse de côté", "ce_que_je_laisse_de_cote")):
        if plan.get(cle):
            details.append(f"{titre} : " + " · ".join(esc(x) for x in plan[cle]))
    if details:
        h.append("<div class=card>" + "<br>".join(details) + "</div>")
    for alerte in plan.get("alertes") or []:
        h.append(f"<div class=warn>⚠️ {esc(alerte)}</div>")
    if q:
        h.append(f"<div class=card><h2 style='margin-top:0'>Question en attente</h2>"
                 f"<b>{esc(q[1])}</b><p class=mut>{esc(q[2])}</p>"
                 f"<form method=post action='/action?t={token}'>"
                 f"<input type=hidden name=quoi value=vie><input type=hidden name=champ value='{esc(q[0])}'>"
                 "<label>Ta réponse</label><textarea name=texte></textarea>"
                 "<p><button class='btn ok'>Enregistrer</button></p></form></div>")
    h.append(f"<div class=card><form method=post action='/action?t={token}'>"
             "<input type=hidden name=quoi value=plan>"
             "<button class='btn'>Refaire ma journée</button></form> "
             f"<form method=post action='/action?t={token}'>"
             "<input type=hidden name=quoi value=off>"
             "<button class='btn ghost'>Journée off</button></form></div>")
    return page("Aujourd'hui", "".join(h), "jour", token, message)


def vue_vie(store, token, message=None):
    p = F.profil(store)
    questions = {c[0]: c for c in F.CHAMPS}
    h = ["<h1>Ma vie</h1>",
         "<p class=mut>Ce que le Cortex sait de toi, et ce qu'il ignore encore. "
         "Rien de tout cela ne sort dans un email ou une publication (I4, I14).</p>"]
    manquants = [c[0] for c in F.CHAMPS if not p.get(c[0])]
    h.append(f"<div class=card><b>{len(F.CHAMPS) - len(manquants)}/{len(F.CHAMPS)}</b> champs "
             f"renseignés. <span class=mut>Il apprend une question à la fois, sur Telegram.</span></div>")
    for prefixe, titre in F.SECTIONS:
        entrees = [(k, v) for k, v in sorted(p.items())
                   if k.startswith(prefixe) and isinstance(v, str)]
        if not entrees:
            continue
        h.append(f"<h2>{esc(titre)}</h2><div class=card><table>")
        for k, v in entrees:
            h.append(f"<tr><td class=mut>{esc(k)}</td><td>{esc(v)}</td></tr>")
        h.append("</table></div>")
    if manquants:
        h.append("<h2>Ce que le Cortex ne sait pas encore</h2><div class=card><table>")
        for cle in manquants:
            c = questions[cle]
            h.append(f"<tr><td class=mut>{esc(cle)}</td><td>{esc(c[1])}</td></tr>")
        h.append("</table></div>")
    h.append(f"<div class=card><h2 style='margin-top:0'>Ajouter ou corriger</h2>"
             f"<form method=post action='/action?t={token}'>"
             "<input type=hidden name=quoi value=vie>"
             "<label>Champ (facultatif)</label><select name=champ><option value=''>"
             "— réponse libre —</option>"
             + "".join(f"<option value='{esc(c[0])}'>{esc(c[0])} — {esc(c[1])}</option>"
                       for c in F.CHAMPS)
             + "</select><label>Ta réponse</label><textarea name=texte></textarea>"
             "<p><button class='btn ok'>Enregistrer</button></p></form>"
             "<p class=mut>Le fichier <code>vie-fondateur.md</code> est régénéré à chaque "
             "changement.</p></div>")
    return page("Ma vie", "".join(h), "vie", token, message)


def vue_valider(store, token, message=None):
    rows = store.db.execute("SELECT * FROM proposals WHERE status='en_attente_humain' "
                            "ORDER BY created_at").fetchall()
    h = ["<h1>À valider</h1>",
         "<p class=mut>Les mêmes décisions que sur Telegram. Valider ici déclenche exactement le "
         "même chemin (I2, I10) : la décision est journalisée, et un email validé part dans la file "
         "d'envoi — il est expédié au passage suivant du Cortex.</p>"]
    if not rows:
        h.append("<div class=card>Aucune action en attente.</div>")
    for r in rows:
        p = {}
        try:
            p = json.loads(r["payload"] or "{}")
        except ValueError:
            pass
        cible = (p.get("target") or {}).get("company", "—")
        h.append(f"<div class=card><b>{esc(r['action_type'])}</b> · {esc(r['risk_level'])} · "
                 f"{esc(cible)}<div class=det>{esc((p.get('justification') or '')[:400])}</div>"
                 f"<p class=mut>identifiant <code>{esc(r['action_id'][:8])}</code> · "
                 f"expire {esc(C.paris(C.parse_iso(r['expires_at'])))}</p>"
                 f"<form method=post action='/action?t={token}'>"
                 f"<input type=hidden name=quoi value=valider>"
                 f"<input type=hidden name=id value='{esc(r['action_id'][:8])}'>"
                 "<button class='btn ok'>Valider</button></form> "
                 f"<form method=post action='/action?t={token}'>"
                 f"<input type=hidden name=quoi value=refuser>"
                 f"<input type=hidden name=id value='{esc(r['action_id'][:8])}'>"
                 "<button class='btn no'>Refuser</button></form></div>")
    return page("À valider", "".join(h), "valider", token, message)


def vue_journal(store, token, message=None):
    rows = store.db.execute("SELECT ts, power, event, details FROM journal "
                            "ORDER BY id DESC LIMIT 60").fetchall()
    ok, ligne = store.verify_journal()
    h = ["<h1>Journal</h1>",
         f"<div class=card>Intégrité du journal : "
         + ("<b>intègre</b>" if ok else f"<b>ALTÉRÉ à la ligne {ligne}</b>")
         + " <span class=mut>(chaîne SHA-256, I1)</span></div>",
         "<div class=card><table><tr><th>Quand</th><th>Pouvoir</th><th>Événement</th></tr>"]
    for r in rows:
        h.append(f"<tr><td class=mut>{esc(C.paris(C.parse_iso(r['ts'])))}</td>"
                 f"<td>{esc(r['power'])}</td><td>{esc(r['event'])}</td></tr>")
    h.append("</table></div>")
    return page("Journal", "".join(h), "journal", token, message)


# --------------------------------------------------------------------------
# Serveur HTTP
# --------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "CortexLocal/1.0"

    def log_message(self, fmt, *args):  # pas de bruit dans la console
        pass

    # -- outils -------------------------------------------------------------
    def _hote_ok(self):
        return (self.headers.get("Host") or "").split(":")[0] in ("127.0.0.1", "localhost")

    def _repondre(self, code, corps, entete="text/html; charset=utf-8"):
        donnees = corps.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", entete)
        self.send_header("Content-Length", str(len(donnees)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(donnees)

    def _rediriger(self, chemin, message=None, token=None):
        cible = f"{chemin}?t={token}"
        if message:
            cible += "&m=" + urllib.parse.quote(message[:300])
        self.send_response(303)
        self.send_header("Location", cible)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _refus(self, texte, proposer_lien=False):
        bouton = ""
        if proposer_lien:
            bouton = ("<div class=card><p>Rien n'est cassé. Clique ici :</p>"
                      f"<p><a class=btn href='/?t={esc(self.server.token)}'>Ouvrir ma journée</a></p>"
                      "<p class=mut>Le plus simple reste le raccourci "
                      "<b>Cortex (ma journee)</b> sur ton Bureau, qui met ce laissez-passer "
                      "tout seul.</p></div>")
        self._repondre(403, page("Refusé", f"<h1>Refusé</h1><div class=warn>{esc(texte)}</div>{bouton}",
                                 "", self.server.token))

    # -- lecture ------------------------------------------------------------
    def do_GET(self):
        if not self._hote_ok():
            return self._refus("Cette interface n'accepte que 127.0.0.1 ou localhost.")
        url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(url.query)
        if params.get("t", [""])[0] != self.server.token:
            return self._refus("Il manque le laissez-passer dans l'adresse : tu as ouvert la page "
                               "sans lui. Ce n'est pas une panne.", proposer_lien=True)
        message = (params.get("m", [""])[0] or None)
        store = ouvrir_base()
        try:
            if url.path == "/vie":
                corps = vue_vie(store, self.server.token, message)
            elif url.path == "/valider":
                corps = vue_valider(store, self.server.token, message)
            elif url.path == "/journal":
                corps = vue_journal(store, self.server.token, message)
            else:
                corps = vue_jour(store, self.server.token, message)
        finally:
            store.db.close()
        self._repondre(200, corps)

    # -- actions ------------------------------------------------------------
    def do_POST(self):
        if not self._hote_ok():
            return self._refus("Cette interface n'accepte que 127.0.0.1 ou localhost.")
        url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(url.query)
        if params.get("t", [""])[0] != self.server.token:
            return self._refus("Jeton absent ou invalide : action refusée.")
        origine = (self.headers.get("Origin") or "").split(":")[0]
        if origine and origine not in ("127.0.0.1", "localhost"):
            return self._refus("Origine inconnue : action refusée.")
        taille = int(self.headers.get("Content-Length") or 0)
        if taille > 100_000:
            return self._refus("Requête trop grosse.")
        champs = {k: v[0] for k, v in urllib.parse.parse_qs(
            self.rfile.read(taille).decode("utf-8", "replace")).items()}
        store = ouvrir_base()
        console = Console()
        try:
            message, retour = agir(store, console, (champs.get("quoi") or "").strip(), champs)
        except Exception as exc:  # une erreur ne doit pas tuer l'interface
            store.log("EXECUTIF", "interface_erreur", details={"erreur": C.safe_error(exc)})
            message, retour = f"Erreur : {C.safe_error(exc)}. Rien n'a été fait.", "jour"
            print(f"[cortex] erreur interface : {exc!r}")
        finally:
            store.db.close()
        self._rediriger("/" if retour == "jour" else f"/{retour}", message, self.server.token)


def jeton(chemin):
    """Jeton local : stable entre deux lancements, jamais dans git."""
    fichier = Path(chemin)
    if fichier.exists():
        valeur = fichier.read_text(encoding="utf-8").strip()
        if len(valeur) >= 16:
            return valeur
    valeur = secrets.token_urlsafe(24)
    fichier.write_text(valeur, encoding="utf-8")
    return valeur


def ouvrir_navigateur(adresse):
    """Ouvre le navigateur par défaut. Ne fait jamais échouer le démarrage."""
    try:
        webbrowser.open(adresse)
        return True
    except Exception:
        return False


def journaliser(message, visible=False, chemin=None):
    """Trace le démarrage dans cortex-app.log : si ça échoue, la raison est écrite."""
    ligne = f"{datetime.now().isoformat(timespec='seconds')}  {message}"
    try:
        with open(chemin or (BASE_DIR / "cortex-app.log"), "a", encoding="utf-8") as f:
            f.write(ligne + "\n")
    except OSError:
        pass
    if visible:
        print("   " + ligne)
    return ligne


def deja_en_service(port, timeout=2.0):
    """Vrai si notre interface répond déjà sur ce port (double-clic répété sur le lanceur)."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=timeout) as rep:
            return b"Cortex" in rep.read(4000)
    except urllib.error.HTTPError as exc:
        return exc.code == 403          # notre page « Refusé » : c'est bien nous
    except Exception:
        return False


class ServeurCortex(ThreadingHTTPServer):
    """Serveur local en instance unique.

    Windows interprète SO_REUSEADDR comme « je peux prendre un port déjà occupé » :
    avec le réglage par défaut, deux lancements écoutent le même port et se
    volent les requêtes. On le désactive pour qu'un second lancement échoue
    proprement et rouvre simplement la page existante.
    """

    allow_reuse_address = False


def preparer_serveur(port_prefere, essais=6):
    """Cherche un port libre et renvoie (serveur, port, note).

    Si le port préféré est déjà tenu par une autre copie de l'interface, on ne
    démarre pas un deuxième serveur : on rouvrira la page existante.
    """
    note = ""
    for essai in range(essais):
        port = port_prefere + essai
        try:
            return ServeurCortex(("127.0.0.1", port), Handler), port, note
        except OSError as exc:
            note = f"port {port} indisponible ({getattr(exc, 'strerror', None) or exc})"
            if essai == 0 and deja_en_service(port):
                return None, port, "deja_en_service"
    return None, None, note


def main():
    ap = argparse.ArgumentParser(description="Interface locale du Cortex (127.0.0.1).")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--db", default=C.DB_PATH, help="base SQLite (défaut : celle du Cortex)")
    ap.add_argument("--token-fichier", default=str(BASE_DIR / ".app-token"))
    ap.add_argument("--ouvrir", action="store_true",
                    help="ouvre le navigateur dès que l'interface est prête")
    args = ap.parse_args()

    C.DB_PATH = args.db
    try:  # console Windows : écrire en UTF-8 plutôt que planter sur un emoji
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    print("🧠 Interface locale du Cortex")
    try:
        jeton_local = jeton(args.token_fichier)
    except OSError as exc:
        print(f"   Impossible d'écrire le jeton : {exc}")
        print(f"   Vérifie que tu peux écrire dans {BASE_DIR}.")
        journaliser(f"echec jeton : {exc}", visible=True)
        return 1
    serveur, port, note = preparer_serveur(args.port)
    adresse = f"http://127.0.0.1:{port or args.port}/?t={jeton_local}"
    if note == "deja_en_service":
        print(f"   L'interface tourne déjà sur le port {port} : je rouvre la page.")
        journaliser(f"deja en service sur {port}, page rouverte")
        if args.ouvrir:
            ouvrir_navigateur(adresse)
        return 0
    if serveur is None:
        print(f"   Aucun port disponible à partir de {args.port} (essayé {6} ports).")
        print(f"   Dernier échec : {note}")
        print("   Essaie à la main : python app.py --port 8901")
        journaliser(f"echec demarrage : {note}", visible=True)
        return 1
    if port != args.port:
        print(f"   Le port {args.port} était pris : j'utilise {port} ({note}).")
    serveur.token = jeton_local
    print(f"   base   : {args.db}")
    print(f"   adresse: {adresse}")
    print("   (garde cette fenêtre ouverte ; ferme-la ou Ctrl+C pour arrêter)")
    journaliser(f"demarrage OK sur le port {port} (base {args.db})")
    if args.ouvrir:
        if not ouvrir_navigateur(adresse):
            print(f"   Ouvre ton navigateur à la main : {adresse}")
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt.")
    finally:
        serveur.server_close()
        journaliser("arret de l'interface")
    return 0


if __name__ == "__main__":
    sys.exit(main())
