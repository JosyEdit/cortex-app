---
id: secteur-services-aux-entreprises
type: secteur
titre: Services aux entreprises — agences de communication, conseil, recrutement, intérim (NAF 70.2, 73, 78)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [secteur, services-aux-entreprises, agence-communication, conseil, recrutement, interim, NAF702, NAF73, NAF78, sous-traitance-rgpd, article-28, ia-generative, propriete-intellectuelle, ai-act, M1_Prospection]
---

# Services aux entreprises : agences, cabinets de conseil, recrutement, intérim

Cible : agences de communication et de marketing digital, cabinets de conseil en gestion, cabinets de recrutement et agences d'emploi de la tranche d'effectif cible JOSY EI (6-49 personnes). Point commun : elles traitent les données de leurs clients (ou des candidats) et utilisent déjà l'IA générative. Elles sont souvent **sous-traitantes RGPD** de leurs clients.

## Identité du secteur

- Codes NAF : 70.21Z (conseil en relations publiques et communication), 70.22Z (conseil pour les affaires et autres conseils de gestion) ; 73.11Z (activités des agences de publicité), 73.12Z (régie publicitaire de médias), 73.20Z (études de marché et sondages) ; 78.10Z (activités des agences de placement de main-d'œuvre, dont cabinets de recrutement), 78.20Z (activités des agences de travail temporaire), 78.30Z (autre mise à disposition de ressources humaines).
- Taille : l'agrégat INSEE « services aux entreprises » compte 1 042 315 entreprises et 2,92 millions de salariés EQTP en 2023 [S1] ; le détail par division NAF (70.2, 73, 78) n'est pas donné sur la page consultée (non vérifié).
- Part 6-49 salariés : non sourcée (non vérifié). Beaucoup d'indépendants en 70.22Z ; les agences et les cabinets de recrutement structurés de la cible comptent typiquement 8 à 30 personnes (estimation).
- Structure typique : 2 à 4 associés, chefs de projet ou consultants, créatifs ou chargés de recrutement, un ou deux profils administratifs ; nombreux freelances en renfort (estimation).

## Organisation type et outils numériques

- Bureautique et stockage : Google Workspace ou Microsoft 365, partage de fichiers avec les clients via Drive, SharePoint, WeTransfer, Dropbox (estimation).
- Agences : suite Adobe, Figma, Canva, outils d'IA générative (texte, image, vidéo), accès délégués aux comptes clients (Google Ads, Meta, sites WordPress, CRM des clients) (estimation).
- Conseil : tableurs et données financières ou RH des clients, outils de visioconférence et de prise de notes avec IA (estimation).
- Recrutement et intérim : ATS (logiciel de suivi des candidatures) et CVthèque, jobboards, LinkedIn Recruiter ; en intérim, logiciel métier de gestion des missions, contrats et paie (exemples d'éditeurs non vérifiés).
- Qui gère l'informatique : un associé « geek » ou l'office manager, avec un prestataire ponctuel ; pas de RSSI (estimation).
- Point faible typique : accès clients (mots de passe Google Ads, admin WordPress) stockés dans un tableur partagé ; comptes de freelances jamais désactivés (estimation).

## Besoins IT, IA, RGPD et cybersécurité

- Statut de sous-traitant (RGPD art. 28) : quand l'agence gère le fichier clients d'un client, envoie ses newsletters ou administre son site, elle agit pour son compte. La CNIL attend un contrat qui fixe l'objet, la durée, la finalité, la confidentialité, l'authentification minimale, la restitution ou destruction des données en fin de contrat, la gestion des incidents avec notification rapide des violations, et l'aide au client pour ses obligations de sécurité [S2]. Les clients doivent vérifier les garanties (audits, certifications ISO 27001 / 27701) [S2] : une agence sans réponse claire perd des appels d'offres (estimation).
- Chaîne de sous-traitance : la CNIL demande de considérer toute la chaîne, pas seulement le sous-traitant direct [S2] → freelances et outils d'IA utilisés par l'agence sont dans le périmètre.
- Recrutement : CV et lettre d'un candidat non retenu conservés au maximum 2 ans après le dernier contact, avec information du candidat ; information obligatoire sur l'existence d'un tri algorithmique des candidatures ; CSE informé avant toute nouvelle technique d'aide au recrutement [S3].
- IA générative : risque de confidentialité (données clients ou candidats collées dans un outil gratuit), droits sur les contenus générés, transparence des contenus générés (AI Act art. 50 depuis le 2 août 2026) [S4].
- Propriété intellectuelle : cession de droits des créations, preuve d'antériorité, archives de projets (besoin de sauvegarde versionnée) (estimation).

## Obligations réglementaires et échéances

- RGPD art. 28 : contrat de sous-traitance avec chaque client dont l'agence traite les données [S2].
- AI Act : transparence (chatbots, contenus générés ou modifiés, hypertrucages identifiables) depuis le 2 août 2026, 2 décembre 2026 pour les systèmes déjà sur le marché ; maîtrise de l'IA par les salariés qui l'utilisent depuis février 2025 [S4]. Pour une agence de communication, l'étiquetage des contenus générés est un sujet de livraison client.
- AI Act, haut risque : les obligations pour les systèmes autonomes à haut risque sont reportées au 2 décembre 2027 par le règlement omnibus (UE) 2026/1744, publié au JO de l'UE le 24 juillet 2026 [S4]. Les systèmes d'IA de recrutement et de tri des candidatures relèvent de la liste des usages à haut risque (annexe III du règlement IA ; non revérifié dans le texte ce jour) → les cabinets de recrutement qui utilisent un ATS avec scoring doivent s'y préparer (à revérifier 2027-06).
- Facturation électronique : réception obligatoire depuis le 1er septembre 2026 ; émission et e-reporting pour PME et micro au 1er septembre 2027 [S5]. Cible 100 % B2B : toutes les factures clients deviennent électroniques en 2027 (estimation).
- NIS2 : transposition française non adoptée au 28/09/2026 ; secteurs cités sans mention des agences, du conseil ou du recrutement [S6] → pas d'obligation directe, mais leurs clients assujettis exigeront des garanties de leurs prestataires (estimation).

## Risques et incidents typiques

- Piratage de compte : première menace des entreprises en 2025 (21 % des demandes d'assistance entreprises/associations, +52 %) [S7] ; pour une agence, un compte compromis donne accès aux comptes publicitaires et aux sites de tous ses clients (estimation).
- Hameçonnage 16 %, faux ordres de virement 13,5 %, rançongiciels 8,1 %, violations de données 6,6 % [S7].
- Faux RIB dans la chaîne freelances / clients : changement de coordonnées bancaires par email usurpé (estimation, cohérent avec [S7]).
- Fuite de CVthèque (cabinet de recrutement) : données de milliers de candidats, notification CNIL et information des personnes potentiellement nécessaires (estimation).
- Départ d'un associé ou d'un salarié avec les fichiers clients ou les accès (estimation).

## Budget et décision d'achat

- Décideur : les associés (souvent le gérant ou le directeur associé en charge de l'administratif) ; décision collégiale rapide dans les petites structures (estimation).
- Budget IT : abonnements SaaS par utilisateur (suite bureautique, Adobe, IA, ATS) ; enveloppe significative par salarié, plus élevée en agence créative (estimation, non sourcé).
- Cycle : 2 à 6 semaines ; accéléré si un client grand compte envoie un questionnaire de sécurité ou un avenant RGPD (estimation).
- Sensibilité au prix de 490 € HT : faible ; c'est le prix d'une demi-journée de leur propre facturation. L'argument est la capacité à répondre aux questionnaires clients et aux appels d'offres (estimation).

## Déclencheurs et signaux d'achat

- Réponse à un appel d'offres public ou grand compte (questionnaire sécurité, annexe RGPD demandée).
- Lancement d'une offre « IA » par l'agence (page de services nouvelle, posts sur l'IA générative).
- Recrutement de chefs de projet, consultants, chargés de recrutement ; ouverture d'un nouveau bureau.
- Passage à un nouvel ATS ou nouvel outil d'automatisation marketing.
- Arrivée ou départ d'un associé (modification au RCS, annonce BODACC).
- Référencement d'un client dans un secteur sensible (santé, banque, collectivités) mis en avant sur le site de l'agence.

## Objections probables et réponses

- « On n'est pas concernés, ce sont nos clients qui sont responsables des données. » → Vous êtes sous-traitant : l'article 28 vous impose des obligations propres, dont la sécurité et la notification des incidents [S2].
- « On maîtrise déjà l'IA, c'est notre métier. » → Le diagnostic ne vous apprend pas l'outil ; il vérifie quelles données clients entrent dedans et ce que vos contrats en disent.
- « On a Microsoft 365 / Google Workspace, c'est sécurisé. » → La plateforme l'est ; vos réglages de partage, la double authentification et les comptes de freelances restent de votre côté.
- « Pas le temps, on facture à la journée. » → Une demi-journée, rapport court, 3 actions ; utile à la prochaine réponse d'appel d'offres.
- « Le haut risque de l'AI Act, c'est pour les gros éditeurs. » → Le report va à décembre 2027 [S4] ; les cabinets qui utilisent un scoring de candidats auront aussi des devoirs d'utilisateur (à préciser au cas par cas).
- « On a un prestataire informatique. » → Parfait : le rapport lui donne une liste claire ; le diagnostic porte aussi sur RGPD et IA, rarement couverts par un prestataire matériel.

## Accroches email

1. « Quand vous gérez les données d'un client, l'article 28 du RGPD exige un contrat précis. Vos contrats sont-ils à jour ? » (21 mots) [S2]
2. « Depuis août, les contenus générés par IA doivent être identifiables. Vos livrables clients le prévoient-ils ? » (16 mots) [S4]
3. « Un CV non retenu se conserve deux ans maximum, candidat informé. Votre logiciel de recrutement purge-t-il automatiquement ? » (18 mots) [S3]

## Angle de l'offre Diagnostic IA, RGPD et sauvegardes

Ce que le diagnostic regarde en priorité :
- Gestion des accès clients (coffre-fort de mots de passe, comptes nominatifs, retrait des freelances partis) et double authentification.
- Contrats de sous-traitance (art. 28) avec les clients et avec ses propres sous-traitants (freelances, outils SaaS, IA) [S2].
- Usage de l'IA générative : outils utilisés, versions payantes ou gratuites, données injectées, mention des contenus générés [S4].
- Recrutement : durées de conservation de la CVthèque, information des candidats, tri automatisé [S3].
- Sauvegarde versionnée des projets et des livrables (preuve de propriété intellectuelle).

3 actions types recommandées :
1. Déployer un gestionnaire de mots de passe d'équipe pour les accès clients, avec revue trimestrielle des comptes.
2. Rédiger une charte d'usage de l'IA (outils autorisés, données interdites, étiquetage des contenus) et un modèle d'annexe RGPD art. 28 pour les contrats clients.
3. Mettre en place une sauvegarde externe versionnée des espaces de travail (M365/Google) et une purge automatique de la CVthèque à 2 ans.

## Saisonnalité et moments d'envoi

- À éviter : mi-juillet à fin août (fermetures), décembre (bouclage et fêtes) ; pour les agences, les périodes de lancement de campagnes de rentrée (septembre) ; pour l'intérim, les pics de missions saisonnières (estimation).
- Meilleurs moments : janvier-février (budgets et plans de l'année), mars-juin, octobre-novembre (estimation).
- Jours et heures : mardi à jeudi, 8 h 30-10 h ou 13 h 30-14 h 30 (estimation).

## Où trouver les entreprises

- Annuaire des entreprises (annuaire-entreprises.data.gouv.fr) et API Recherche d'entreprises : NAF 70.21Z, 70.22Z, 73.11Z, 73.20Z, 78.10Z, 78.20Z ; tranche d'effectif 03 (6-9), 11 (10-19), 12 (20-49) ; département ; ignorer la diffusion partielle (voir schema-fiche-entreprise). Attention : 70.22Z contient beaucoup de sociétés holding ou d'indépendants sans salariés → filtrer sur la tranche d'effectif.
- Sites des agences : page « équipe » (fonctions seulement, jamais de nom stocké), mentions légales (SIREN), adresse générique.
- Annonces d'offres d'emploi publiques (signal de croissance).
- Règle : écrire à l'adresse générique (contact@, hello@, agence@) ou à l'adresse professionnelle publiée pour la fonction (associé, directeur) ; intérêt légitime B2B ; « répondre STOP » dans chaque email ; opposition définitive (voir legal-prospection-b2b).

## Sources

[S1] INSEE — Caractéristiques des secteurs marchands par activité, données annuelles 2023 — https://www.insee.fr/fr/statistiques/2498421 — publié 2025-09-18 — consulté 2026-10-11
[S2] CNIL — Sécurité : gérer la sous-traitance — https://www.cnil.fr/fr/securite-gerer-la-sous-traitance — publié 2024-03-14 — consulté 2026-10-11
[S3] CNIL — Recrutement et données personnelles dans les TPE/PME : cinq questions incontournables à se poser — https://www.cnil.fr/fr/recrutement-et-donnees-personnelles-dans-les-tpepme-cinq-questions-incontournables-se-poser — publié 2023-01-30 — consulté 2026-10-11
[S4] Blog du Modérateur — IA Act : ce qui change le 2 août 2026 (source secondaire) — https://www.blogdumoderateur.com/ia-act-2-aout-2026/ — publié 2026-07-29 — consulté 2026-10-11
[S5] Ministère de l'Économie — Tout savoir sur la facturation électronique pour les entreprises — https://www.economie.gouv.fr/tout-savoir-sur-la-facturation-electronique-pour-les-entreprises — date non indiquée (actualité à la une du 2026-09-01) — consulté 2026-10-11
[S6] Legiscope — Transposition NIS2 en France (source secondaire) — https://www.legiscope.com/blog/transposition-nis2-france.html — publié 2026-07-02, mis à jour 2026-09-28 — consulté 2026-10-11
[S7] Le Monde Informatique — Les demandes d'aide face aux cybermenaces explosent en France (rapport 2025 Cybermalveillance.gouv.fr, source secondaire) — https://www.lemondeinformatique.fr/actualites/lire-les-demandes-d-aide-face-aux-cybermenaces-explosent-en-france-99756.html — publié 2026-03-27 — consulté 2026-10-11
