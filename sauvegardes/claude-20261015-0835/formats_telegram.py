"""Les 8 formats Telegram stricts (décision de JOSY, 13/10/2026). Un message = une action ; les détails
restent dans cortex.db. Fonctions pures : elles renvoient le texte HTML à envoyer.

  1. email_pret      2. envoye          3. reponse_prospect   4. statut
  5. recommandation  6. client_chaud    7. erreur             8. chat libre (réponse normale, 2 à 6 phrases)

Branchement prévu dans cortex.py / vente.py (non appliqué : modification refusée par le garde-fou) :
  - dispatch(cold_email)        -> email_pret(...)
  - process_queue               -> envoye(entreprise)
  - vente.propose_replies       -> reponse_prospect(...) ; /1 /2 /3 /r inchangés
  - Cortex.status_text          -> statut(...)
  - amélioration de règle       -> recommandation(...) ; commandes /oui et /non = /valider et /refuser du dernier en attente
  - vente.propose_hot_lead      -> client_chaud(...) (réponse par /r)
  - Telegram.alert              -> erreur(...)
"""

import html
import re


def _e(t, n=None):
    t = re.sub(r"\s+", " ", str(t or "")).strip()
    return html.escape(t[:n] if n else t)


def email_pret(destinataire, objet, argument, aid):
    return (f"📧 <b>EMAIL PRÊT</b>\n\nÀ : {_e(destinataire)}\nObjet : {_e(objet, 120)}\n"
            f"Argument : {_e(argument, 200)}\n\n/valider {aid[:8]}  •  /refuser {aid[:8]}")


def envoye(entreprise):
    return f"✅ Envoyé à {_e(entreprise)}"


def reponse_prospect(entreprise, texte, propositions):
    lignes = [f"📩 <b>RÉPONSE DE {_e(entreprise).upper()}</b>", "", f"« {_e(texte, 400)} »", ""]
    lignes += [f"{i}. {_e(p, 300)}" for i, p in enumerate(propositions[:3], 1)]
    choix = "  •  ".join(f"/{i}" for i in range(1, len(propositions[:3]) + 1))
    lignes += ["", (choix + "  •  " if choix else "") + "/r [ta réponse]"]
    return "\n".join(lignes)


def statut(actif, en_attente, prochaine_mission):
    return (f"🧠 {'Actif' if actif else 'Arrêté'}\n📋 {en_attente} action{'s' if en_attente != 1 else ''} en attente\n"
            f"🎯 Prochaine mission : {_e(prochaine_mission)}")


def recommandation(titre, recommandation_, justification):
    """Une seule recommandation, jamais une liste d'options. Réponse : /oui ou /non."""
    return (f"💡 <b>{_e(titre, 80)}</b>\n\nRecommandation : {_e(recommandation_, 200)}\n"
            f"Justification : {_e(justification, 200)}\n\n/oui  •  /non")


def client_chaud(entreprise, extrait):
    return f"🔥 <b>CLIENT CHAUD</b>\n\n{_e(entreprise)}\n« {_e(extrait, 300)} »\n\n/r [ta réponse]"


def erreur(probleme, ligne):
    return f"⚠️ <b>{_e(probleme, 80)}</b>\n\n{_e(ligne, 200)}"


def exemples():
    """Jeu de 5 exemples (données fictives, aucun prospect réel) pour validation du format."""
    aid = "3f9a1c2e-0000-0000-0000-000000000000"
    return [
        email_pret("contact@exemple-plomberie.fr", "Exemple Plomberie : ce que j'ai remarqué en ligne",
                   "Votre fiche Google compte 10 avis, la moyenne locale est de 22.", aid),
        envoye("Exemple Plomberie"),
        reponse_prospect("Exemple Plomberie", "Bonjour, combien ça coûte ?",
                         ["Le Cortex démarre à 9,99 € HT par mois.", "Pouvez-vous préciser votre besoin ?",
                          "Le Cortex gère votre fiche Google et votre site."]),
        statut(True, 2, "Prospection"),
        recommandation("Accroche des emails", "Citer d'abord le nombre d'avis Google.",
                       "3 réponses sur 40 emails, aucune sur les arguments de site daté."),
        client_chaud("Exemple Plomberie", "Je suis intéressé, envoyez-moi plus d'informations."),
        erreur("Messagerie injoignable", "Connexion IMAP refusée, nouvel essai au prochain cycle."),
    ]
