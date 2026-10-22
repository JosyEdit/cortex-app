---
id: methode-sequences-relances
type: methode
titre: Séquences de relance, règles d'arrêt et gestion des réponses (prospection B2B JOSY EI)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [methode, relance, sequence, follow-up, reponses, objections, opt-out, rendez-vous, agenda]
---

# Séquences de relance et gestion des réponses

Chaque relance est une action R2 (validation JOSY avant envoi, refus automatique après 2 h). Les chiffres viennent d'éditeurs d'outils d'emailing (sources secondaires, campagnes de masse). La séquence JOSY EI est volontairement plus courte et plus espacée que celle des éditeurs, car chaque envoi est validé à la main et vise des TPE locales.

## Pourquoi relancer : ce que disent les données

- Sur 7,5 millions d'emails B2B envoyés en 2025, les relances (étapes 2 à 6) génèrent **58,6 %** des réponses, contre **41,4 %** pour le premier email [S1].
- Le premier email a le meilleur taux par étape (**0,59 %**) ; l'étape 6 ne rapporte que **0,28 %** ; recommandation : **3 à 5 étapes** au total [S1].
- Campagnes avec au moins une relance : ≈ **13 %** de réponse contre ≈ **9 %** sans relance ; la **première relance** a le meilleur rendement, environ 40 % de plus que l'email initial selon l'éditeur [S2].
- Woodpecker juge optimal **2 à 3 relances** et recommande au moins **2 à 3 jours** entre deux messages [S2].
- Limite : aucune de ces études ne mesure l'effet des relances sur les désinscriptions ou plaintes [S1]. Pour une petite entreprise locale, une relance de trop abîme la réputation (estimation).

## Séquence JOSY EI : 3 messages maximum

| Étape | Jour | Contenu | Longueur |
|---|---|---|---|
| E1 | J0 | Email initial : signal + problème + preuve + 15 min | 50-90 mots |
| E2 | J+4 ouvrés | Relance utile : un **nouvel élément** (fait sourcé, mini-conseil) | 40-60 mots |
| E3 | J+10 ouvrés | Email de **rupture** : on clôt poliment, porte ouverte | 30-50 mots |

- 3 messages au total = bas de la fourchette éditeur (3-5) [S1], cohérent avec 2-3 relances [S2] (estimation pour le choix final).
- Espacement ≥ 2-3 jours recommandé [S2] ; JOSY EI prend 4 puis 6 jours ouvrés pour ne pas paraître insistant (estimation).
- Envoyer en **réponse dans le même fil** (même objet précédé de « Re: » légitime, car c'est bien une réponse au message précédent) (estimation).
- Jamais de 4e message dans les 3 mois. Nouvelle tentative possible après 3 mois **seulement** si un nouveau signal apparaît, et dans la limite de 3 ans de conservation (voir `legal-prospection-b2b`).
- Chaque relance garde le **pied d'email légal** complet avec la ligne STOP.

## Contenu de la relance E2 (valeur ajoutée)

Règle : ne jamais écrire « Je me permets de revenir vers vous » seul. Apporter quelque chose.

```
Objet : Re: factures électroniques en 2027

Bonjour,

Un point pratique en complément : l'e-reporting suit votre régime de TVA. En réel mensuel, c'est trois transmissions par mois, en réel simplifié une seule.

Si vous voulez, je vous envoie une fiche d'une page qui résume les étapes avant septembre 2027.

Bien cordialement,
JOSY EI
[pied d'email légal]
```
Fait cité : fréquences d'e-reporting, voir `legal-obligations-clients-2026-2027`.

## Email de rupture (E3)

But : obtenir une réponse claire, même négative, et clore proprement.

```
Objet : Re: factures électroniques en 2027

Bonjour,

Je ne veux pas encombrer votre boîte : ce sera mon dernier message sur ce sujet.

Si la question revient plus tard, il suffit de répondre à cet email.

Bonne continuation,
JOSY EI
[pied d'email légal]
```
Après E3 : statut `sequence_terminee`, aucune relance automatique.

## Règles d'arrêt immédiat

La séquence s'arrête **avant l'envoi suivant** dès que l'un de ces événements est détecté :

1. **Toute réponse humaine** (positive, négative, question) : la séquence automatique cesse ; JOSY répond à la main.
2. **Opposition** : « STOP », « désinscription », « ne plus me contacter », ou équivalent → inscription sur la **liste repoussoir**, plus aucun message. Après opposition, les données ne sont plus traitées à des fins de prospection (art. 21.3 RGPD) [S3].
3. **Rebond définitif** (adresse inexistante) : adresse marquée invalide, jamais réessayée. Gmail bloque l'envoi 24 h en cas de trop nombreux messages non distribuables [S5].
4. **Réponse automatique d'absence** : décaler la relance après la date de retour indiquée.
5. **Changement de signal** (entreprise cessée, radiée au BODACC) : arrêt.

Délais :
- Traiter un STOP **le jour même** (règle JOSY EI). Yahoo exige que les désinscriptions soient traitées **sous 2 jours** pour les expéditeurs en volume [S4].
- Toute demande de droits RGPD (accès, effacement) : réponse **sous un mois** au plus [S6].
- Liste d'opposition conservée **au moins 3 ans** [S7].

## Réponses types : intéressé

Objectif : fixer l'échange de 15 minutes en un seul aller-retour.

```
Merci pour votre réponse.

Voici mon agenda pour choisir un créneau de 15 minutes : [lien d'agenda]
Si aucun horaire ne convient, indiquez-moi deux moments qui vous arrangent.

Pour préparer l'échange, une seule question : combien de postes informatiques utilisez-vous, à peu près ?

Bien cordialement,
JOSY EI
```
Ensuite : statut `rdv_propose`, notification à JOSY. Un devis ou une proposition commerciale reste un brouillon R3 soumis à JOSY.

## Réponses types : pas maintenant

```
Merci, je comprends.

Voulez-vous que je vous recontacte à une période précise ? Sinon, je ne vous relancerai pas : il vous suffira de répondre à ce message le moment venu.

Bien cordialement,
JOSY EI
```
Si une date est donnée : rappel interne à cette date (une seule relance). Sinon : statut `pas_maintenant`, aucune relance.

## Réponses types : mauvaise personne

```
Merci de m'avoir répondu.

Pouvez-vous me dire quelle fonction s'occupe de l'informatique ou de la facturation chez vous ? Je lui écrirai directement, sans mentionner votre nom si vous préférez.

Bien cordialement,
JOSY EI
```
Ne jamais insister. Ne pas enregistrer le nom d'une personne transmis par le prospect sans nécessité : noter la **fonction** et, si fournie, l'adresse générique ou professionnelle (règle I4).

## Réponses types : refus

```
Bien noté, merci pour votre réponse claire. Je ne vous écrirai plus.

Bonne continuation,
JOSY EI
```
Action : liste repoussoir. Pas d'argumentation, pas de « dernière offre ».

## Réponses types : colère ou plainte

Principe : excuses brèves, arrêt immédiat, transparence sur la source, aucune justification juridique longue.

```
Je vous prie de m'excuser pour ce message non souhaité. Votre adresse a été retirée : vous ne recevrez plus rien de ma part.

Pour information, votre adresse provenait de [source exacte]. Si vous souhaitez que j'efface aussi la trace de votre refus, dites-le-moi ; je la conserve uniquement pour ne plus vous écrire.

JOSY EI, entrepreneur individuel, SIREN 914 113 543
```
Actions : liste repoussoir ; alerte immédiate à JOSY ; si la personne demande l'accès à ses données, communiquer **la source réelle** (KASPR sanctionné pour ne pas l'avoir fait, voir `legal-prospection-b2b`) ; analyser le ciblage pour éviter la répétition.

## Passage au rendez-vous : lien d'agenda

- Envoyer le lien d'agenda **seulement après une réponse positive**, jamais dans le premier email (estimation : un lien dans un premier email est perçu comme intrusif et augmente le risque de filtrage).
- Créneaux de **15 minutes**, visio ou téléphone, avec un tampon de 15 minutes après (estimation).
- Le formulaire de réservation demande le minimum : nom de l'entreprise, adresse email, sujet. Pas de champ téléphone obligatoire (minimisation).
- Outil gratuit possible : prise de rendez-vous de Google Agenda ou équivalent (non vérifié : conditions de gratuité à confirmer).
- Confirmation : un email récapitulatif avec l'heure, le sujet et ce que JOSY préparera.
- Après l'échange : proposition du diagnostic à 490 € HT en brouillon R3, validée par JOSY avant envoi.

## Statuts de séquence dans la base du Cortex

| Statut | Déclencheur | Prochaine action |
|---|---|---|
| `a_valider` | E1 préparé | Validation JOSY |
| `e1_envoye` / `e2_envoye` | Envoi | Relance selon calendrier |
| `repondu` | Réponse humaine | JOSY répond |
| `rdv_propose` / `rdv_fixe` | Intéressé | Préparer l'échange |
| `pas_maintenant` | Report | Rappel daté ou rien |
| `oppose` | STOP / refus / plainte | Liste repoussoir |
| `invalide` | Rebond | Aucune |
| `sequence_terminee` | E3 sans réponse | Purge à 3 ans |

## Sources

[S1] Belkins — Sales follow-up statistics in B2B (données éditeur, source secondaire) — https://belkins.io/blog/sales-follow-up-statistics — mis à jour 2026-06-26 — consulté 2026-10-11
[S2] Woodpecker — Follow-up statistics (données éditeur, source secondaire) — https://woodpecker.co/blog/follow-up-statistics/ — publié 2019-01-24, mis à jour 2025-01-21 — consulté 2026-10-11
[S3] CNIL — RGPD, chapitre 3 (art. 21) — https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre3 — date non indiquée — consulté 2026-10-11
[S4] Yahoo — Sender Best Practices — https://senders.yahooinc.com/best-practices/ — date non indiquée (application depuis février 2024) — consulté 2026-10-11
[S5] Google — Aide Gmail : limites d'envoi et erreurs (compte personnel) — https://support.google.com/mail/answer/22839?hl=fr — date non indiquée — consulté 2026-10-11
[S6] CNIL — La prospection commerciale par courrier électronique, SMS-MMS et automate d'appel — https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique — publié 2026-06-10 — consulté 2026-10-11
[S7] CNIL — Questions-réponses sur les référentiels relatifs à la gestion des activités commerciales et des impayés — https://www.cnil.fr/fr/questions-reponses-sur-les-referentiels-relatifs-la-gestion-des-activites-commerciales-et-des — publié 2022-01-28 — consulté 2026-10-11
