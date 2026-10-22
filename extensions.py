"""Point d'entrée des fonctionnalités avancées (catégories 1, 2, 6 et 7) : commandes Telegram et
passage à chaque cycle. cortex.py reste modulaire : un module par catégorie.

  memoire_avancee.py  catégorie 1 (mémoire)        apprentissage.py  catégorie 2 (auto-amélioration)
  clients.py          catégorie 6 (gestion client)  conformite.py     catégorie 7 (sécurité, RGPD)
"""

import re
from datetime import datetime
from pathlib import Path

import apprentissage
import clients
import conformite
import memoire_avancee

EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", re.I)

AIDE = ("🧠 Commandes avancées\n"
        "/client nom : fiche client (CRM)\n/memoire nom : derniers épisodes\n/important : événements saillants\n"
        "/fait cle = valeur : mémoire sémantique\n/versions : historique des règles\n/rollback ID : restaurer une version (validation requise)\n"
        "/rapport nom email : rapport mensuel à valider\n/livree nom email : enquête de satisfaction à valider\n"
        "/export : sauvegarde complète en JSON\n/donnees email : export RGPD d'une adresse\n/oubli email confirmer : droit à l'oubli")


def handle(c, cx, cmd, args, text):
    """Renvoie True si la commande a été traitée."""
    tg, s = cx.tg, cx.s
    esc = c.html.escape
    if cmd == "/client":
        tg.send(esc(clients.fiche(s, " ".join(args)) if args else "Usage : /client nom"))
    elif cmd == "/memoire":
        tg.send(esc(memoire_avancee.rappel(s, " ".join(args)) if args else "Usage : /memoire nom"))
    elif cmd == "/important":
        ev = memoire_avancee.importants(s)
        tg.send("\n".join(f"{e['ts'][:10]} [{e['salience']}] {esc(e['entreprise'] or '')} : {esc(e['action'])}"
                          for e in ev) or "Aucun événement saillant.")
    elif cmd == "/fait":
        m = re.match(r"/fait\s+([^=]{1,60})=(.+)", text, re.S)
        if m:
            memoire_avancee.definir_fait(s, m.group(1), m.group(2))
            tg.send("✅ Fait enregistré.")
        else:
            tg.send("Faits connus :\n" + esc("\n".join(f"{k} : {v}" for k, v in memoire_avancee.faits(s).items()))
                    + "\n\nUsage : /fait cle = valeur")
    elif cmd == "/versions":
        v = apprentissage.liste_versions(s)
        tg.send("\n".join(f"{x['id']} · {x['ts'][:16]} · {x['fichier']} · {x['sha']} · {esc(x['motif'])}"
                          for x in v) or "Aucune version enregistrée.")
    elif cmd == "/rollback":
        if args and args[0].isdigit():
            apprentissage.proposer_rollback(c, cx, int(args[0]))
        else:
            tg.send("Usage : /rollback ID (voir /versions)")
    elif cmd in ("/rapport", "/livree"):
        email = next((a for a in args if EMAIL_RE.fullmatch(a)), None)
        nom = " ".join(a for a in args if a != email)
        if not email or not nom:
            tg.send(f"Usage : {cmd} nom email")
        elif cmd == "/rapport":
            clients.proposer_rapport(c, cx, nom, email)
        else:
            clients.proposer_enquete(c, cx, nom, email)
    elif cmd == "/export":
        dossier = Path(c.BASE_DIR) / "exports"
        dossier.mkdir(exist_ok=True)
        chemin = dossier / f"cortex-{datetime.now().strftime('%Y%m%d-%H%M')}.json"
        compte = memoire_avancee.exporter(s, chemin)
        s.log("HUMAIN", "export_complet", details={"lignes": sum(compte.values())})
        tg.send(f"✅ Export complet : {sum(compte.values())} lignes, {len(compte)} tables, fichier local "
                f"exports\\{chemin.name}.")
    elif cmd == "/donnees":
        if args and EMAIL_RE.fullmatch(args[0]):
            chemin, compte = conformite.donnees(s, args[0], Path(c.BASE_DIR) / "exports")
            tg.send(f"✅ Données de cette adresse exportées : {compte or 'aucune ligne'} (exports\\{chemin.name}).")
        else:
            tg.send("Usage : /donnees adresse@exemple.fr")
    elif cmd == "/oubli":
        if len(args) >= 2 and EMAIL_RE.fullmatch(args[0]) and args[1].lower() == "confirmer":
            compte = conformite.oublier(s, args[0])
            tg.send(f"✅ Adresse effacée ou anonymisée ({sum(compte.values())} lignes) et inscrite à la liste "
                    "d'opposition : plus jamais contactée.")
        else:
            tg.send("Irréversible. Confirme avec : /oubli adresse@exemple.fr confirmer")
    elif cmd == "/aide":
        tg.send(esc(AIDE))
    else:
        return False
    return True


def cycle(c, cx):
    """Un passage par cycle ; une erreur ici n'arrête jamais le cycle principal."""
    try:
        memoire_avancee.setup(cx.s)
        apprentissage.cycle(c, cx, c.BASE_DIR)
        conformite.verifier_journal(c, cx)
        clients.notifier_fins_de_relance(c, cx)
    except Exception as exc:
        cx.s.log("EXECUTIF", "extension_erreur", details={"erreur": c.safe_error(exc)})
        c.alert(cx.s, "extension", c.safe_error(exc))


def fin_de_mission(cx):
    """Mémoire de travail : vidée à la fin de chaque cycle (mission)."""
    memoire_avancee.travail_vider(cx.s)
