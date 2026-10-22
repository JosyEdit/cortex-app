"""Fiabilité « Enterprise » de l'interface (22/10/2026), version locale (Python + SQLite) :

  - idempotence   : chaque clic porte une clé unique (UUID) ; une clé déjà vue est ignorée ;
  - limite de débit : 5 appels par minute et par utilisateur sur les actions coûteuses (Groq, API de l'État) ;
  - plans         : table `plans` (fonctionnalités par formule) et colonne `plan` des utilisateurs ;
  - disjoncteur   : 3 échecs Groq de suite → mode dégradé 5 minutes (réponses de secours, alerte).

Limites assumées : compteurs en mémoire (un redémarrage les remet à zéro) et une seule machine.
Sur plusieurs serveurs, il faudrait un stockage partagé (Redis) pour les limites et le disjoncteur.
"""

import threading
import time

_verrou = threading.Lock()

# --------------------------------------------------------------------------- limite de débit
LIMITE, FENETRE_S = 5, 60
_appels = {}  # (uid, catégorie) -> [horodatages]


def limiter(uid, categorie="groq", limite=LIMITE, fenetre=FENETRE_S):
    """(True, None) si l'appel est permis, sinon (False, message clair)."""
    maintenant = time.time()
    with _verrou:
        h = [t for t in _appels.get((uid, categorie), []) if maintenant - t < fenetre]
        if len(h) >= limite:
            attente = int(fenetre - (maintenant - h[0])) + 1
            _appels[(uid, categorie)] = h
            return False, (f"Limite atteinte : {limite} demandes par minute. Réessayez dans {attente} s "
                           "(protection contre les abus et les coûts).")
        h.append(maintenant)
        _appels[(uid, categorie)] = h
    return True, None


# --------------------------------------------------------------------------- disjoncteur Groq
SEUIL_ECHECS, PAUSE_S = 3, 5 * 60
_etat = {"echecs": 0, "ouvert_jusqua": 0.0}


def groq_disponible():
    return time.time() >= _etat["ouvert_jusqua"]


def groq_echec(store=None):
    with _verrou:
        _etat["echecs"] += 1
        ouvre = _etat["echecs"] >= SEUIL_ECHECS and groq_disponible()
        if ouvre:
            _etat["ouvert_jusqua"] = time.time() + PAUSE_S
            _etat["echecs"] = 0
    if ouvre and store is not None:
        store.set("groq_degrade_jusqua", str(_etat["ouvert_jusqua"]))
        store.log("SYSTEME", "groq_mode_degrade", details={"pause_s": PAUSE_S})
    return ouvre


def groq_succes():
    with _verrou:
        _etat["echecs"] = 0


def mode_degrade_restant():
    """Secondes restantes en mode dégradé (0 si Groq est utilisable)."""
    return max(0, int(_etat["ouvert_jusqua"] - time.time()))


# --------------------------------------------------------------------------- idempotence
SCHEMA = """
CREATE TABLE IF NOT EXISTS idempotence (cle TEXT PRIMARY KEY, utilisateur_id INTEGER, chemin TEXT, vu_le REAL);
CREATE TABLE IF NOT EXISTS plans (plan TEXT, fonction TEXT, valeur INTEGER, PRIMARY KEY(plan, fonction));
"""
# Fonctionnalités par formule (valeur : 1 = oui, 0 = non, n > 1 = plafond, -1 = illimité).
PLANS = {
    "Découverte": {"documentation": 0, "deep_research": 0, "rapports_pdf": 0, "memoire_long_terme": 0, "analyses_mois": 3},
    "Starter": {"documentation": 5, "deep_research": 0, "rapports_pdf": 0, "memoire_long_terme": 0, "analyses_mois": 20},
    "Pro": {"documentation": -1, "deep_research": 1, "rapports_pdf": 1, "memoire_long_terme": 1, "analyses_mois": 20},
    "Business": {"documentation": -1, "deep_research": 1, "rapports_pdf": 1, "memoire_long_terme": 1, "analyses_mois": -1},
}
PLAN_MINIMUM = {"documentation": "Starter", "deep_research": "Pro", "rapports_pdf": "Pro", "memoire_long_terme": "Pro"}


_pret = set()  # bases déjà préparées pendant ce lancement


def preparer(store):
    cle = store.db.execute("PRAGMA database_list").fetchone()[2]
    if cle in _pret:
        return
    store.db.executescript(SCHEMA)
    store.db.executemany("INSERT OR REPLACE INTO plans(plan, fonction, valeur) VALUES(?,?,?)",
                         [(p, f, v) for p, fs in PLANS.items() for f, v in fs.items()])
    cols = {r[1] for r in store.db.execute("PRAGMA table_info(utilisateurs)")}
    if "plan" not in cols:
        store.db.execute("ALTER TABLE utilisateurs ADD COLUMN plan TEXT DEFAULT 'Découverte'")
        store.db.execute("UPDATE utilisateurs SET plan='Business' WHERE role='fondateur'")  # le fondateur a tout
    store.db.commit()
    _pret.add(cle)


def deja_traite(store, cle, uid, chemin):
    """Vrai si cette clé de clic a déjà été traitée (le second clic est ignoré). Enregistre sinon."""
    if not cle:
        return False
    preparer(store)
    try:
        store.db.execute("INSERT INTO idempotence(cle, utilisateur_id, chemin, vu_le) VALUES(?,?,?,?)",
                         (cle[:80], uid, chemin, time.time()))
        store.db.execute("DELETE FROM idempotence WHERE vu_le < ?", (time.time() - 86400,))
        store.db.commit()
        return False
    except Exception:  # clé déjà présente : même clic reçu deux fois
        store.db.rollback()
        store.log("SYSTEME", "requete_dupliquee_ignoree", details={"chemin": chemin, "utilisateur_id": uid})
        return True


def plan_de(store, uid):
    preparer(store)
    row = store.db.execute("SELECT plan, role FROM utilisateurs WHERE id=?", (uid,)).fetchone()
    if not row:
        return "Découverte"
    return "Business" if row[1] == "fondateur" else (row[0] or "Découverte")


def autorise(store, uid, fonction):
    """(True, valeur) si la fonctionnalité est incluse dans le plan de l'utilisateur, sinon (False, plan requis)."""
    plan = plan_de(store, uid)
    row = store.db.execute("SELECT valeur FROM plans WHERE plan=? AND fonction=?", (plan, fonction)).fetchone()
    valeur = row[0] if row else 0
    return (valeur != 0, valeur) if valeur != 0 else (False, PLAN_MINIMUM.get(fonction, "Pro"))
