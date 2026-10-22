"""Catégorie 6 : gestion client (fonctionnalités 26 à 30).

26. CRM intégré : `fiche()` rassemble, depuis cortex.db, coordonnées, statut, envois, réponses et épisodes ;
27. relances J+3, J+7, J+14 (vente.py) ; `notifier_fins_de_relance()` prévient JOSY si rien après J+14 ;
28. qualification automatique : vente.classify / HOT_RE détectent « combien », « devis », « rdv »… et
    déclenchent le message 🔥 (format D) ;
29. rapport mensuel client : `rapport_mensuel()` ne cite que les actions consignées dans `actions_client` ;
    sans action consignée, il le dit. Envoi après validation de JOSY ;
30. enquête de satisfaction : `proposer_enquete()` après une mission marquée livrée, envoyée après validation.
Aucun chiffre n'est inventé : tout vient des tables.
"""

import uuid
from datetime import datetime, timedelta, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS actions_client (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, entreprise TEXT, email TEXT, type TEXT,
  detail TEXT, resultat TEXT);
CREATE TABLE IF NOT EXISTS satisfaction (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, entreprise TEXT, email TEXT, reponse TEXT);
"""


def _now():
    return datetime.now(timezone.utc)


def setup(store):
    store.db.executescript(SCHEMA)
    store.db.commit()


# ---------------------------------------------------------------- 26. CRM
def fiche(store, recherche):
    setup(store)
    db, q = store.db, f"%{recherche.lower()}%"
    ent = db.execute("SELECT * FROM entreprises WHERE lower(denomination) LIKE ? OR lower(email_contact) LIKE ? "
                     "LIMIT 1", (q, q)).fetchone()
    envois = db.execute("SELECT kind, sent_at, repondu, classe, to_email FROM envois WHERE lower(company) LIKE ? "
                        "OR lower(to_email) LIKE ? ORDER BY id", (q, q)).fetchall()
    if not ent and not envois:
        return f"Aucune fiche pour « {recherche} »."
    lignes = []
    if ent:
        lignes.append(f"{ent['denomination']} ({ent['commune'] or '?'}) · statut {ent['statut']}"
                      + (f" · {ent['email_contact']}" if ent["email_contact"] else ""))
        if ent["reponse_resume"]:
            lignes.append(f"Dernière réponse : {ent['reponse_resume']}")
    for e in envois:
        lignes.append(f"{e['sent_at'][:10]} : {e['kind']}" + (f" → réponse {e['classe']}" if e["repondu"] else ""))
    acts = db.execute("SELECT ts, type, detail FROM actions_client WHERE lower(entreprise) LIKE ? ORDER BY id DESC "
                      "LIMIT 5", (q,)).fetchall()
    for a in acts:
        lignes.append(f"{a['ts'][:10]} : {a['type']} {a['detail'] or ''}".strip())
    return "\n".join(lignes)


# ---------------------------------------------------------------- 27. fin de relances
def notifier_fins_de_relance(c, cortex, jours_apres_derniere=7):
    """Prévient JOSY (une seule fois par prospect) quand les 3 relances sont restées sans réponse."""
    s = cortex.s
    limite = c.iso(c.now() - timedelta(days=14 + jours_apres_derniere))
    for e in s.db.execute("SELECT id, company FROM envois WHERE kind='premier' AND repondu=0 AND relance_n>=3 "
                          "AND sent_at<=?", (limite,)).fetchall():
        cle = f"fin_relances_{e['id']}"
        if s.get(cle):
            continue
        s.set(cle, "1")
        cortex.tg.send(f"📭 {c.html.escape(e['company'])} n'a pas répondu après 3 relances.")


# ---------------------------------------------------------------- 29. rapport mensuel
def consigner_action(store, entreprise, type_, detail="", resultat="", email=""):
    setup(store)
    store.db.execute("INSERT INTO actions_client(ts, entreprise, email, type, detail, resultat) VALUES(?,?,?,?,?,?)",
                     (_now().isoformat(timespec="seconds"), entreprise, email.lower(), type_, detail[:300],
                      resultat[:300]))
    store.db.commit()


def rapport_mensuel(store, entreprise, mois=None):
    """mois : 'AAAA-MM' (par défaut le mois précédent). Texte factuel tiré de actions_client."""
    setup(store)
    if not mois:
        premier = _now().replace(day=1) - timedelta(days=1)
        mois = premier.strftime("%Y-%m")
    rows = store.db.execute("SELECT ts, type, detail, resultat FROM actions_client WHERE lower(entreprise) LIKE ? "
                            "AND substr(ts,1,7)=? ORDER BY ts", (f"%{entreprise.lower()}%", mois)).fetchall()
    if not rows:
        return mois, "Aucune action enregistrée ce mois-ci."
    par_type = {}
    for r in rows:
        par_type[r["type"]] = par_type.get(r["type"], 0) + 1
    lignes = [f"Actions réalisées en {mois} : " + ", ".join(f"{t} ({n})" for t, n in sorted(par_type.items())) + "."]
    lignes += [f"- {r['ts'][:10]} : {r['type']} {r['detail'] or ''}" + (f" → {r['resultat']}" if r["resultat"] else "")
               for r in rows[:20]]
    return mois, "\n".join(lignes)


def _proposer_email(c, cortex, action_type, entreprise, email, sujet, corps, annonce):
    aid = str(uuid.uuid4())
    p = {"action_id": aid, "timestamp": c.iso(c.now()), "risk_level": "R2", "mission": "M3_Relation_Client",
         "action_type": action_type, "target": {"company": entreprise, "contact": "client", "email": email},
         "content": {"subject": sujet, "body": corps + "\n\n" + c.SIGNATURE},
         "sources": [{"url": "actions_client (cortex.db)", "date": c.iso(c.now())[:10]}],
         "justification": annonce, "reversibility": "Rien n'est envoyé sans ton clic.", "timeout_hours": 24}
    cortex.dispatch(p, text=f"📧 {annonce} pour {c.html.escape(entreprise)}. /valider {aid[:8]} /refuser {aid[:8]}")
    return aid


def proposer_rapport(c, cortex, entreprise, email, mois=None):
    mois, texte = rapport_mensuel(cortex.s, entreprise, mois)
    corps = f"Bonjour,\n\nVoici votre rapport pour {mois}.\n\n{texte}\n\nPour toute question, répondez à cet email."
    return _proposer_email(c, cortex, "rapport_client", entreprise, email, f"Votre rapport {mois}", corps,
                           f"Rapport mensuel {mois} prêt")


# ---------------------------------------------------------------- 30. satisfaction
def proposer_enquete(c, cortex, entreprise, email):
    corps = ("Bonjour,\n\nVotre mission est terminée. Pour nous améliorer, pouvez-vous répondre à cet email "
             "par une note de 1 à 5 (5 = très satisfait) et, si vous le souhaitez, un commentaire ?")
    return _proposer_email(c, cortex, "enquete", entreprise, email, "Votre avis sur notre travail", corps,
                           "Enquête de satisfaction prête")


def enregistrer_reponse_enquete(store, entreprise, email, texte):
    setup(store)
    store.db.execute("INSERT INTO satisfaction(ts, entreprise, email, reponse) VALUES(?,?,?,?)",
                     (_now().isoformat(timespec="seconds"), entreprise, email.lower(), texte[:500]))
    store.db.commit()
