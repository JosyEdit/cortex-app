---
id: secteur-associations-medico-social
type: secteur
titre: Associations employeuses et établissements médico-sociaux privés, 6-49 salariés (NAF 8710-8899, 9499Z)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [secteur, associations, medico-social, EHPAD, aide-a-domicile, SAAD, ESMS, NAF87, NAF88, NAF9499Z, donnees-de-sante, HDS, DUI, ESMS-numerique, CERT-Sante, benevoles, budgets-contraints, M1_Prospection]
---

# Associations employeuses et établissements médico-sociaux privés

Cible : associations employeuses de la tranche d'effectif cible JOSY EI (6-49 personnes) (insertion, culture, sport, éducation populaire), établissements et services sociaux et médico-sociaux privés (EHPAD associatifs ou commerciaux, foyers, services pour personnes handicapées, protection de l'enfance), services d'aide et d'accompagnement à domicile (SAAD). Sujets clés : données sensibles et de santé, budgets contraints et financés, bénévoles, messagerie partagée.

## Identité du secteur

- Codes NAF : 87.10A (hébergement médicalisé pour personnes âgées, dont EHPAD), 87.10B et 87.10C (enfants et adultes handicapés), 87.20A/B, 87.30A/B (hébergement social pour personnes âgées ou handicapées physiques), 87.90A/B ; 88.10A (aide à domicile), 88.10B et 88.10C (accueil et accompagnement sans hébergement, aide par le travail), 88.91A/B (accueil de jeunes enfants, enfants handicapés), 88.99A/B (autre action sociale) ; 94.99Z (autres organisations fonctionnant par adhésion volontaire, code de la majorité des associations).
- Associations en France : 1,6 million d'associations actives ; 9 sur 10 fonctionnent sans salarié ; 1,9 million de salariés associatifs, soit 9 % du secteur privé, pour 51 Md€ de masse salariale [S1]. Les associations concentrent plus de la moitié des emplois du sanitaire et social [S1].
- Nombre exact d'associations employeuses et part des 6-49 salariés : non indiqués dans la source consultée (non vérifié) ; environ 1 association sur 10 est employeuse (estimation dérivée de [S1]).
- Structure typique 6-49 salariés : un directeur ou une directrice salarié(e), un bureau bénévole (président, trésorier) qui signe les engagements, une équipe éducative, soignante ou d'intervenants à domicile, un ou deux postes administratifs (estimation).

## Organisation type et outils numériques

- ESMS : dossier usager informatisé (DUI), logiciel de soins et de transmissions en EHPAD, planification et télégestion des interventions en aide à domicile, logiciel de paie et de facturation aux départements et aux familles (éditeurs non vérifiés quant aux parts de marché).
- Associations hors médico-social : logiciel de gestion des adhérents et dons, comptabilité associative, outils gratuits (Google, messageries personnelles des bénévoles) (estimation).
- Données : dossiers des usagers (santé, situation sociale, handicap), dossiers du personnel, données des familles et tuteurs, listes d'adhérents et de donateurs.
- Qui gère l'informatique : le directeur, un salarié administratif ou un bénévole compétent ; parfois une fédération ou un groupement de coopération qui mutualise (estimation).
- Point faible typique : boîtes mail génériques partagées sans double authentification, postes partagés entre équipes de jour et de nuit, bénévoles utilisant leurs propres appareils (estimation).

## Besoins IT, IA, RGPD et cybersécurité

- Données de santé et hébergement : toute personne qui héberge des données de santé pour le compte d'un responsable de traitement doit présenter des garanties de sécurité ; le certificat HDS en est la preuve ; le cadre couvre les données collectées lors d'activités de suivi social et médico-social (art. R.1111-8-8 CSP) [S2]. Conséquence : le DUI ou le logiciel de soins hébergé à l'extérieur doit l'être chez un hébergeur certifié HDS (le diagnostic vérifie l'attestation).
- Durées de conservation (CNIL, secteur social et médico-social, ESMS de l'article L.312-1 CASF dont EHPAD, CHRS, SAAD, ESAT) : fixer les durées à l'avance ; sans texte, la CNIL recommande 2 ans après le dernier contact pour les structures d'inclusion sociale ; exemples : CHRS 2 ans après la sortie, services mandataires judiciaires 5 ans après la fin de la mesure ; purge automatique recommandée ; documentation dans l'analyse d'impact (AIPD) [S3].
- Archives publiques : pour une structure qui exerce une mission de service public, pas de destruction sans procédure validée avec les archives départementales, sous peine de sanctions pénales [S3].
- Bénévoles : accès limité au strict nécessaire, engagement de confidentialité, pas de données d'usagers sur appareils personnels (estimation).
- IA : comptes rendus, rédaction de demandes de subvention, traduction ; interdiction pratique de coller des données d'usagers dans une IA grand public (estimation) ; maîtrise de l'IA par les salariés exigée depuis février 2025 [S4].

## Obligations réglementaires et échéances

- HDS : hébergement des données de santé chez un hébergeur certifié (art. L.1111-8 CSP, décret 2018-137) [S2].
- Déclaration des incidents de sécurité : les établissements de santé et médico-sociaux déclarent leurs incidents au CERT Santé, qui publie un observatoire annuel [S5] (obligation réglementaire précise non revérifiée ce jour, à revérifier 2027-01).
- Programme ESMS numérique : AMI 2026 en Nouvelle-Aquitaine (publié le 22/07/2026) pour équiper d'un DUI référencé Ségur les ESMS « personnes handicapées – enfants » et « protection de l'enfance » qui n'en ont pas ; finance infrastructure, matériel, logiciels, conformité, interopérabilité et sécurité (art. L.1110-4-1 CSP) et formation [S6]. Montants et dates de clôture dans le cahier des charges, non consulté (non vérifié).
- Facturation électronique : réception obligatoire depuis le 1er septembre 2026 ; émission et e-reporting au 1er septembre 2027 pour PME et micro [S7] ; concerne les associations assujetties à la TVA (les entreprises assujetties établies en France sont visées [S7]) ; beaucoup d'associations non lucratives ne sont pas assujetties (estimation, à vérifier au cas par cas).
- NIS2 : la santé figure parmi les secteurs couverts, mais la transposition française n'est pas adoptée au 28/09/2026 et la règle générale vise les entités de taille moyenne ou plus [S8] → une structure de moins de 50 salariés n'est a priori pas assujettie (estimation, à revérifier 2027-01).
- AI Act : transparence des chatbots et contenus générés depuis le 2 août 2026 [S4].

## Risques et incidents typiques

- Observatoire CERT Santé 2025 : 764 incidents déclarés (749 en 2024, 581 en 2023) concernant 606 structures ; le nombre d'ESMS déclarants augmente de 50 % et leurs signalements de 48 % ; les rançongiciels baissent d'environ 30 % (28 attaques) mais touchent majoritairement des ESMS [S5].
- Compromission du SI = menace la plus importante en 2025 : messagerie 50 % des vecteurs, comptes applicatifs ou de maintenance 25 %, Active Directory 8 %, VPN 5 % ; pour les incidents graves, VPN 40 % et Active Directory 33 % [S5].
- Cas : EHPAD de la Manche revendiqué par le groupe Medusa en octobre 2023, rançon de 100 000 dollars, publication de pièces d'identité et certificats médicaux de résidents [S9].
- National 2025 (entreprises et associations) : piratage de compte 21 %, hameçonnage 16 %, faux ordres de virement 13,5 %, rançongiciels 8,1 % des demandes d'assistance [S10].
- Faux RIB d'un fournisseur ou d'un salarié (détournement de paie) dans une structure où le trésorier bénévole valide à distance (estimation).

## Budget et décision d'achat

- Décideurs : le directeur propose, le bureau ou le conseil d'administration valide ; en ESMS, budget encadré par les autorités de tarification (ARS, département) (estimation).
- Budget IT : faible et fléché ; dépenses informatiques souvent financées par des appels à projets (ESMS numérique [S6], fondations, fonds régionaux) (estimation).
- Cycle : long (1 à 4 mois), calé sur les réunions du bureau et les budgets prévisionnels ; accéléré après un incident ou pour monter un dossier de financement (estimation).
- Sensibilité au prix de 490 € HT : forte ; argument : le diagnostic peut servir d'état des lieux pour une demande de financement (estimation, ne jamais promettre l'obtention d'une subvention).

## Déclencheurs et signaux d'achat

- Publication d'un appel à projets ou AMI (ESMS numérique, ARS, département) [S6].
- Changement de directeur (offre d'emploi publique de direction).
- Fusion, regroupement d'associations, reprise d'un service, ouverture d'une antenne.
- Incident déclaré dans un établissement voisin ou dans la presse régionale.
- Déploiement annoncé d'un DUI ou d'un logiciel de télégestion.
- Évaluation externe de la qualité ou renouvellement d'autorisation à préparer (non vérifié quant au calendrier propre à chaque structure).

## Objections probables et réponses

- « On n'a pas de budget. » → Le diagnostic est court et le rapport peut servir de base à une demande de financement ; on priorise les actions gratuites.
- « Notre éditeur héberge, c'est son problème. » → Vérifions qu'il est certifié HDS [S2] et que vos accès (messagerie, comptes) sont protégés : c'est par là que passent la moitié des compromissions [S5].
- « On est une petite structure, personne ne nous vise. » → Les ESMS déclarants ont augmenté de 50 % en 2025 et les rançongiciels touchent majoritairement des ESMS [S5].
- « Le CA doit valider. » → Normal ; je vous envoie une présentation d'une page pour la prochaine réunion du bureau.
- « Un bénévole s'occupe de l'informatique. » → Le rapport lui donne une feuille de route claire et partageable.
- « La fédération nous accompagne déjà. » → Le diagnostic complète sur votre site, vos postes et vos comptes, sans refaire ce que la fédération fournit.

## Accroches email

1. « En 2025, les ESMS déclarant un incident de sécurité ont augmenté de 50 %. Votre messagerie a-t-elle la double authentification ? » (21 mots) [S5]
2. « Les données d'usagers hébergées à l'extérieur doivent l'être chez un hébergeur certifié HDS. Avez-vous l'attestation de votre éditeur ? » (20 mots) [S2]
3. « La CNIL demande des durées de conservation fixées et une purge des dossiers d'usagers. La vôtre est-elle documentée ? » (19 mots) [S3]

## Angle de l'offre Diagnostic IA, RGPD et sauvegardes

Ce que le diagnostic regarde en priorité :
- Messagerie et comptes : double authentification, boîtes partagées, comptes des salariés partis et des bénévoles, accès VPN et comptes de maintenance du prestataire [S5].
- Hébergement des données d'usagers : certificat HDS de l'éditeur ou de l'hébergeur [S2], lieu des sauvegardes, test de restauration du DUI.
- Durées de conservation et purge des dossiers usagers, registre et AIPD [S3].
- Procédure de validation des virements (faux RIB fournisseurs et salariés).
- Usage de l'IA par les équipes (comptes rendus, subventions) et règles interdisant les données d'usagers.

3 actions types recommandées :
1. Activer la double authentification sur la messagerie et le VPN, supprimer les comptes inactifs et donner des comptes nominatifs aux équipes de nuit et aux bénévoles.
2. Obtenir l'attestation HDS de l'éditeur du DUI et tester une restauration complète ; ajouter une copie de sauvegarde hors ligne des documents administratifs.
3. Adopter un tableau des durées de conservation inspiré du référentiel CNIL et une règle écrite d'usage de l'IA sans données d'usagers.

## Saisonnalité et moments d'envoi

- À éviter : juillet-août (congés, sous-effectif en établissement), décembre ; périodes de clôture des comptes et d'assemblées générales (souvent mars à juin) ; périodes de préparation des budgets prévisionnels (automne, variable selon les autorités) (estimation).
- Meilleurs moments : septembre après la rentrée, janvier-février, et dès la publication d'un appel à projets numérique [S6] (estimation).
- Jours et heures : mardi à jeudi, 9 h-11 h ; éviter le lundi (gestion des week-ends) (estimation).

## Où trouver les entreprises

- Annuaire des entreprises (annuaire-entreprises.data.gouv.fr) et API Recherche d'entreprises : NAF 87.xx, 88.xx, 94.99Z ; tranche d'effectif 03 (6-9), 11 (10-19), 12 (20-49) ; département ; filtre « association » disponible sur l'annuaire (non vérifié ce jour, interface non consultable) ; ignorer la diffusion partielle (voir schema-fiche-entreprise).
- Annuaires publics des établissements sanitaires et sociaux et listes des ARS et départements (non vérifiés quant aux conditions de réutilisation).
- Lauréats publiés des appels à projets ESMS numérique (structures déjà engagées dans un projet numérique) (non vérifié quant à la publication).
- Règle : écrire uniquement à l'adresse générique de la structure (contact@, direction@, accueil@) ou à l'adresse professionnelle publiée pour la fonction (direction) ; jamais à un bénévole sur une adresse personnelle ; intérêt légitime B2B ; « répondre STOP » dans chaque email ; opposition définitive (voir legal-prospection-b2b).

## Sources

[S1] Recherches & Solidarités — La France associative en mouvement 2025, communiqué de presse — https://recherches-solidarites.org/wp-content/uploads/2025/10/La_France_associative_CP_16-10-2025.pdf — publié 2025-10-16 — consulté 2026-10-11
[S2] Agence du numérique en santé (G_NIUS) — Healthcare data hosting (HDS) — https://gnius.esante.gouv.fr/en/regulations/regulation-profiles/healthcare-data-hosting-hds — publié 2020-09-22, mis à jour 2025-08-07 — consulté 2026-10-11
[S3] CNIL — Secteur social et médico-social : comment gérer les durées de conservation ? — https://www.cnil.fr/fr/secteur-social-et-medico-social-comment-gerer-les-durees-de-conservation — publié 2023-11-15 — consulté 2026-10-11
[S4] Blog du Modérateur — IA Act : ce qui change le 2 août 2026 (source secondaire) — https://www.blogdumoderateur.com/ia-act-2-aout-2026/ — publié 2026-07-29 — consulté 2026-10-11
[S5] Caducée.net — Cybersécurité en santé 2025 : les rançongiciels reculent, les comptes compromis progressent (source secondaire, observatoire CERT Santé) — https://www.caducee.net/actualite-medicale/16900/cybersecurite-en-sante-2025-les-rancongiciels-reculent-les-comptes-compromis-progressent.html — publié 2026-05-21 — consulté 2026-10-11
[S6] ARS Nouvelle-Aquitaine — Appel à manifestation d'intérêt (AMI) 2026 programme ESMS numérique en Nouvelle-Aquitaine — https://www.nouvelle-aquitaine.ars.sante.fr/appel-manifestation-dinteret-ami-2026-programme-esms-numerique-en-nouvelle-aquitaine-derniere — publié 2026-07-22 — consulté 2026-10-11
[S7] Ministère de l'Économie — Tout savoir sur la facturation électronique pour les entreprises — https://www.economie.gouv.fr/tout-savoir-sur-la-facturation-electronique-pour-les-entreprises — date non indiquée (actualité à la une du 2026-09-01) — consulté 2026-10-11
[S8] Legiscope — Transposition NIS2 en France (source secondaire) — https://www.legiscope.com/blog/transposition-nis2-france.html — publié 2026-07-02, mis à jour 2026-09-28 — consulté 2026-10-11
[S9] Infirmiers.com — Cyberattaque contre un EHPAD de la Manche : les hackers réclament 100 000 dollars — https://www.infirmiers.com/profession-ide/cyberattaque-contre-un-ehpad-de-la-manche-les-hackers-reclament-100-000-dollars — publié 2023-10-25 — consulté 2026-10-11
[S10] Le Monde Informatique — Les demandes d'aide face aux cybermenaces explosent en France (rapport 2025 Cybermalveillance.gouv.fr, source secondaire) — https://www.lemondeinformatique.fr/actualites/lire-les-demandes-d-aide-face-aux-cybermenaces-explosent-en-france-99756.html — publié 2026-03-27 — consulté 2026-10-11
