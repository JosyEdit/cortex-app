---
id: methode-email-froid
type: methode
titre: Méthode d'email de prospection B2B pour un consultant solo (format JOSY EI)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [methode, cold-email, prospection, redaction, objet, signal, personnalisation, mesure, exemples]
---

# Méthode d'email de prospection B2B (JOSY EI)

Objectif d'un premier email : obtenir **une réponse**, pas une vente. L'offre d'appel est le « Diagnostic IA, RGPD et sauvegardes » (demi-journée, 490 € HT). Mais le premier email ne vend pas le diagnostic : il propose un échange de 15 minutes.

Les statistiques de cette fiche viennent d'**éditeurs d'outils d'emailing** (Hunter, Belkins, Woodpecker). Ce sont des sources secondaires, sur des campagnes surtout anglophones et à fort volume. Elles donnent des ordres de grandeur, pas des garanties.

## Structure en 5 blocs

1. **Objet** : 2 à 6 mots, en minuscules ou casse normale, lié au signal. Pas de majuscules criardes, pas de « Offre », pas de « Re: » trompeur. L'objet doit être fidèle au contenu (interdit par L34-5 sinon, voir `legal-prospection-b2b`).
2. **Première ligne personnalisée** : un fait public, vérifiable, propre à l'entreprise (signal). Une phrase.
3. **Problème** : la conséquence concrète du signal pour cette entreprise. Une à deux phrases, sans dramatiser.
4. **Preuve ou crédibilité** : un fait sourcé (obligation datée, chiffre officiel) ou ce que JOSY EI fait concrètement. Jamais de résultat chiffré promis.
5. **Appel à l'action léger** : une question fermée ou un échange de 15 minutes. Une seule demande.

Puis signature courte et pied d'email légal (modèle dans `legal-prospection-b2b#modele-de-pied-d-email-information-opt-out`).

## Longueur et ton

- Règle JOSY EI : **corps de moins de 120 mots**, hors pied d'email (fixée par JOSY).
- Donnée éditeur : sur 34 millions d'emails froids (Hunter, 2022-2024), la tranche **20-39 mots** obtient le meilleur taux de réponse moyen (**4,5 %**) ; les emails de moins de 100 mots font **3,9 %** contre **3,7 %** au-delà [S1]. L'écart est faible : la longueur n'est pas le levier principal [S1].
- Cible pratique : **50 à 90 mots** pour un premier email (estimation : assez pour un signal + un problème + une preuve).
- Ton : vouvoiement, phrases courtes, pas de jargon (« IA générative », « transformation digitale »). Parler en conséquences métier : facture, sauvegarde, client, salarié, amende.
- Une seule idée par email. Pas de liste à puces dans le premier email.
- Pas de pièce jointe, pas d'image, au plus un lien (page de vente) ; idéalement aucun lien dans le premier email (estimation : moins de risque de filtrage, voir `methode-delivrabilite`).

## Personnalisation par signal

Un signal est un **fait public récent** qui rend le sujet pertinent aujourd'hui. Sources de signaux : voir `methode-sources-donnees-entreprises`.

| Signal | Où le trouver | Angle JOSY EI |
|---|---|---|
| Création ou reprise (cession) | BODACC A | Partir sur des bases saines : sauvegardes, RGPD, outils |
| Nouvel établissement | Annuaire des entreprises | Second site = second réseau à sécuriser |
| Passage à 10, 20 salariés | Tranche d'effectif Sirene | Registre RGPD, charte informatique |
| Chatbot ou formulaire IA sur le site | Site de l'entreprise | AI Act art. 50 : dire que c'est une IA |
| Offre d'emploi administrative | Site de l'entreprise | Facturation électronique 2027 |
| Secteur visé par une actualité | Presse, CNIL, ANSSI | Obligation ou risque sectoriel |

Règles : le signal doit être **vérifiable** (URL conservée) ; jamais de donnée personnelle (pas de nom du gérant, pas d'information sur sa vie privée) ; ne pas citer de source à laquelle le prospect ne s'attend pas (ex. « j'ai vu vos comptes annuels ») (estimation).

## Appel à l'action : 15 minutes, une question

- Une seule demande, facile à accepter : « Un échange de 15 minutes la semaine prochaine vous serait-il utile ? »
- Variante sans engagement : « Voulez-vous que je vous envoie la liste des 5 points à vérifier ? » (réponse oui/non).
- Pas de lien d'agenda dans le premier email : il est envoyé après une réponse positive (voir `methode-sequences-relances`).
- Ne pas demander « quand êtes-vous disponible ? » (question ouverte, plus d'effort) (estimation).

## Erreurs à éviter

- Promettre un résultat chiffré (« -30 % de temps administratif ») : interdit par la règle JOSY EI.
- Faire peur avec l'amende en première phrase : préférer le gain ou la conséquence concrète.
- Parler de soi d'abord (« Je suis consultant depuis… »).
- Objet trompeur, faux « Re: » ou « Fwd: » (contraire à L34-5).
- Plusieurs liens, images, pièces jointes, mots en majuscules (signaux de spam, estimation).
- Affirmer qu'une TPE de moins de 50 salariés est soumise à NIS2 (faux en règle générale, voir `legal-obligations-clients-2026-2027`).
- Pixel de suivi ou lien traqué : contraire à la recommandation CNIL d'avril 2026 pour ce type d'envoi [S5].
- Oublier le pied d'email : information art. 14 + opt-out obligatoires à chaque message.

## Exemple 1 : facturation électronique (PME de services, 20-49 salariés)

Signal : offre d'emploi d'assistant(e) comptable publiée sur le site de l'entreprise.

```
Objet : factures électroniques en 2027

Bonjour,

Je vois que vous recrutez un(e) assistant(e) comptable : votre volume de facturation grandit.

Au 1er septembre 2027, les PME devront émettre leurs factures au format électronique via une plateforme agréée et transmettre l'e-reporting. Le choix de l'outil et le test du circuit prennent souvent plus de temps que prévu.

J'accompagne des TPE et PME sur ce passage, en lien avec leur expert-comptable.

Un échange de 15 minutes pour faire le point sur votre situation vous serait-il utile ?

Bien cordialement,
JOSY EI — conseil informatique et IA, Montmorillon
[pied d'email légal]
```
Corps : environ 80 mots. Faits sourcés dans `legal-obligations-clients-2026-2027` (calendrier 2027).

## Exemple 2 : sauvegardes et cyberassurance (artisan BTP, 6-9 salariés)

Signal : reprise de l'entreprise publiée au BODACC (vente et cession).

```
Objet : reprise et sauvegardes

Bonjour,

Félicitations pour la reprise de l'entreprise, publiée récemment au BODACC.

Une reprise est souvent le bon moment pour vérifier une chose simple : vos devis, factures et plans sont-ils sauvegardés ailleurs que sur un seul ordinateur ? Vos factures doivent être conservées 10 ans.

Autre point méconnu : après une cyberattaque, l'assureur exige une plainte sous 72 heures pour indemniser.

Voulez-vous que je vous envoie la liste des 5 points à vérifier ?

Bien cordialement,
JOSY EI — conseil informatique et IA, Montmorillon
[pied d'email légal]
```
Corps : environ 85 mots. Faits : 10 ans (code de commerce), 72 h (LOPMI) dans `legal-obligations-clients-2026-2027`.

## Exemple 3 : IA au travail (cabinet ou commerce, 10-19 salariés)

Signal : chatbot visible sur le site de l'entreprise.

```
Objet : votre assistant en ligne

Bonjour,

J'ai remarqué l'assistant de discussion sur votre site.

Depuis le 2 août 2026, le règlement européen sur l'IA demande d'indiquer clairement aux visiteurs qu'ils échangent avec une IA. Il demande aussi aux entreprises de sensibiliser les équipes qui utilisent ces outils.

C'est rarement compliqué : une mention sur le site, une charte d'une page, une courte session pour l'équipe.

Un échange de 15 minutes pour vérifier votre cas vous serait-il utile ?

Bien cordialement,
JOSY EI — conseil informatique et IA, Montmorillon
[pied d'email légal]
```
Corps : environ 80 mots. Faits : art. 50 et art. 4 AI Act dans `legal-obligations-clients-2026-2027`.

## Mesure : suivre les réponses, pas les ouvertures

- **Apple Mail Privacy Protection** (iOS 15, septembre 2021) précharge le contenu des emails, pixel compris, même non ouverts : ces emails sont comptés comme « ouverts » [S4]. Le taux d'ouverture est donc **peu fiable** [S4].
- La CNIL encadre les pixels de suivi depuis avril 2026 ; leur usage en prospection n'entre pas dans l'exemption de délivrabilité [S5]. JOSY EI ne mesure donc **pas** les ouvertures.
- Indicateurs à suivre dans la base du Cortex :
  - **taux de réponse** (toutes réponses / emails délivrés) ;
  - **taux de réponse positive** (intéressé ou demande d'info) ;
  - **taux de rendez-vous** (échange de 15 min obtenu) ;
  - **taux d'opposition** (STOP) et **taux de rebond** (adresse invalide).
- Repère éditeur : sur 7,5 millions d'emails B2B en 2025, le premier email obtient **0,59 %** de réponse par étape, et les relances totalisent **58,6 %** des réponses [S2]. Ces taux concernent des campagnes de masse ; un envoi ciblé et validé un par un devrait faire mieux (estimation, non vérifié).
- Repère éditeur : campagnes avec au moins une relance ≈ **13 %** de réponse contre ≈ **9 %** sans relance (Woodpecker) [S3].
- Seuil d'alerte JOSY EI : plus de 2 STOP ou plaintes sur 50 envois → revoir le ciblage et le message (estimation).

## Checklist avant envoi (à valider par JOSY)

1. Signal réel, récent, URL enregistrée.
2. Destinataire = fonction liée au sujet ; adresse générique de préférence.
3. Objet fidèle, 2-6 mots.
4. Corps < 120 mots, une seule demande, aucune promesse chiffrée.
5. Chaque fait cité renvoie à une fiche de la Mémoire avec source.
6. Aucun pixel, au plus un lien.
7. Pied d'email légal présent, ligne STOP séparée.
8. Adresse absente de la liste repoussoir.

## Sources

[S1] Hunter — What's the Best Word Count & Length for Cold Emails (données éditeur, source secondaire) — https://hunter.io/blog/cold-email-word-count — publié 2024-04-26 — consulté 2026-10-11
[S2] Belkins — Sales follow-up statistics in B2B (données éditeur, source secondaire) — https://belkins.io/blog/sales-follow-up-statistics — mis à jour 2026-06-26 — consulté 2026-10-11
[S3] Woodpecker — Follow-up statistics (données éditeur, source secondaire) — https://woodpecker.co/blog/follow-up-statistics/ — publié 2019-01-24, mis à jour 2025-01-21 — consulté 2026-10-11
[S4] Brevo — Apple Mail Privacy Protection (source secondaire) — https://www.brevo.com/fr/blog/apple-mail-privacy-protection/ — publié 2021-09-08 — consulté 2026-10-11
[S5] CNIL — Pixels de suivi dans les courriers électroniques : la CNIL publie ses recommandations — https://www.cnil.fr/fr/recommandation-pixel-suivi-courriels — publié 2026-04-14 — consulté 2026-10-11
