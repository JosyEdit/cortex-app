---
id: secteur-sante-liberale
type: secteur
titre: Santé libérale et ambulatoire — cabinets de groupe, centres de santé, dentistes, kinés, paramédicaux (NAF 8621Z, 8622*, 8623Z, 8690*)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [sante, donnees-de-sante, hds, segur, dmp, mssante, pro-sante-connect, secret-medical, rgpd, cybersecurite, facturation-electronique]
---

## Identité du secteur

- Codes NAF visés : 86.21Z (médecine générale), 86.22A/B/C (radiodiagnostic, chirurgie, autres spécialistes), 86.23Z (pratique dentaire), 86.90A à 86.90F (ambulances, laboratoires, infirmiers/sages-femmes, rééducation-appareillage, psychologues et autres activités de santé humaine).
- Nombre d'unités légales actives de **6 à 49 salariés** (tranches Sirene 03, 11, 12), tous codes ci-dessus confondus : **7 750** en France [S1]. Dont 86.21Z : **788** [S2] ; 86.23Z (dentaire) : **1 850** [S3] ; 86.90E (rééducation, appareillage, podologie) : **45** [S4]. Dans la Vienne (86) : **38** [S5].
- Sans filtre d'effectif, l'API plafonne à 10 000 résultats : la grande majorité des structures de santé libérales ont moins de 6 salariés [S6]. La cible 6-49 se concentre donc sur : centres et cabinets dentaires, centres de santé, cabinets de radiologie, laboratoires, sociétés d'ambulances, grosses maisons ou cabinets de groupe employant secrétaires et assistants (estimation).
- Effectif typique d'une structure 6-49 : 2 à 8 praticiens associés (souvent non salariés, en SEL/SCM/SCP), plus 4 à 20 salariés (secrétariat médical, assistantes dentaires, manipulateurs radio, ambulanciers) (estimation).
- Attention : le code NAF 86.21Z ou 86.23Z d'une SCM (société civile de moyens) peut masquer un cabinet bien plus gros que son effectif salarié déclaré (estimation).

## Organisation type et outils numériques

- **Logiciel métier (LGC / logiciel de cabinet)** : pour les médecins, les éditeurs visibles sont Weda, Doctolib Médecin, MLM, Maiia, Libellia, TAMM, Odaiji (en ligne), Crossway, AlmaPro, DrSanté (installés localement), HelloDoc et AxiSanté (les deux modes), MediStory, Médimust, Medilink (Mac) [S7]. Prix publics relevés : de 58 € TTC/mois (DrSanté) à 229-489 € TTC/mois par praticien (Doctolib Médecin, plus frais d'installation de 499 à 2 000 €) ; HelloDoc et AxiSanté à partir de 75 €/mois ; MediStory 91 €/mois [S7].
- Dentistes, kinés, radiologues, laboratoires : logiciels spécialisés distincts (noms non vérifiés ici), souvent serveur local au cabinet (non vérifié).
- **Où sont les données** : soit sur un serveur ou un poste « maître » dans le cabinet (logiciel installé), soit chez l'éditeur en mode SaaS. Dans ce second cas, l'hébergeur doit être certifié HDS [S8][S9].
- **Outils périphériques** : prise de RDV en ligne, messagerie sécurisée de santé (MSSanté), lecteur de carte Vitale/CPS, télétransmission, imagerie (PACS en radiologie), messagerie classique (souvent Gmail/Outlook grand public, non vérifié).
- **Qui gère l'informatique** : pas de service informatique. Un associé « référent » ou la secrétaire gère au quotidien ; un prestataire local ou le revendeur du logiciel intervient sur appel (estimation). C'est l'angle d'attaque : personne n'a de vue d'ensemble sur sauvegardes, accès et comptes.

## Besoins IT, IA, RGPD et cybersécurité

- **Secret médical** : il couvre l'ensemble des informations connues du professionnel et s'impose à tous les professionnels du système de santé [S8]. Toute fuite (email mal adressé, poste volé, compte piraté) engage le praticien.
- **Hébergement HDS** : si les données sont hébergées chez un prestataire, il faut un hébergeur agréé ou certifié et un contrat conforme à l'article L.1111-8 du code de la santé publique [S8]. Le référentiel HDS v2.0 impose un hébergement exclusivement dans l'Espace économique européen ; les hébergeurs certifiés en v1.1 avaient jusqu'au 16 mai 2026 pour basculer [S9] ; les obligations de souveraineté prennent effet en septembre 2026 [S9][S7].
- **Durée de conservation** : le Conseil national de l'Ordre des médecins recommande 20 ans après la dernière consultation, puis suppression [S8]. Il n'existe pas de durée légale fixée pour le médecin libéral [S7]. Conséquence : des sauvegardes fiables sur 20 ans, lisibles après changement de logiciel.
- **Registre et information** : registre des traitements à tenir, information des patients (affiche en salle d'attente), AIPD avant une étude interne à risque élevé [S8].
- **Messagerie** : utiliser une messagerie sécurisée de santé pour échanger avec d'autres professionnels ; chiffrer les pièces jointes sinon ; ne pas stocker d'informations médicales sur le téléphone [S8].
- **Comptes et accès** : en 2025, la compromission de comptes est la menace n°1 relevée par le CERT Santé ; vecteurs : messagerie (50 %), comptes applicatifs ou de maintenance (25 %), Active Directory (8 %), VPN (5 %) [S10].
- **IA** : demande croissante d'outils de transcription de consultation, d'aide à la rédaction de courriers, de secrétariat IA ; tout outil qui traite des données patients doit être hébergé HDS et cadré par contrat (estimation, à vérifier outil par outil).

## Obligations réglementaires et échéances

- **Ségur / dotation numérique** : le forfait structure a pris fin le 31 décembre 2025 et est remplacé par la dotation numérique (Donum), jusqu'à 2 940 € par an selon l'Assurance maladie (chiffre rapporté par une source secondaire) [S7]. Premier indicateur socle : logiciel référencé Ségur avec LAP certifié HAS et dernières spécifications SESAM-Vitale [S7]. La mise à jour Ségur « vague 2 » est financée par l'État si commandée avant mi-juillet 2027 [S7] (à revérifier 2027-03).
- **HDS** : localisation EEE et passage au référentiel v2.0 (voir section précédente) [S9].
- **Facturation électronique** : depuis le 1er septembre 2026, toute entreprise doit pouvoir recevoir des factures électroniques ; émission et e-reporting au 1er septembre 2027 pour les petites et micro-entreprises [S11]. Concerne surtout les achats (fournitures, prothésistes, éditeurs) et l'e-reporting des opérations avec des particuliers assujetties à la TVA ; beaucoup d'actes de soins sont exonérés de TVA, le périmètre exact est à vérifier avec l'expert-comptable (estimation).
- **NIS2** : le secteur santé (prestataires de soins) figure dans l'annexe I de la directive, mais le seuil « entité importante » est d'au moins 50 salariés ou plus de 10 M€ de CA ou de bilan [S12]. Une structure de 6-49 salariés est donc a priori hors champ, sauf CA élevé (radiologie, laboratoires) (estimation). La loi française de transposition (projet de loi Résilience) n'est toujours pas adoptée : retirée de l'ordre du jour de l'Assemblée le 6 octobre 2026 [S13].
- **AI Act** : obligations des systèmes à haut risque de l'annexe III reportées au 2 décembre 2027 et de l'annexe I (produits réglementés, dont dispositifs médicaux) au 2 août 2028 [S14] (source secondaire).

## Risques et incidents typiques

- **Volume** : 764 incidents de sécurité déclarés au CERT Santé en 2025 (749 en 2024, 581 en 2023), par 606 structures [S10].
- **Impact sur les soins** : 288 signalements (38 %) ont entraîné un mode dégradé ou une interruption de la prise en charge ; seuls 25 % de ceux-ci étaient malveillants, le reste venant de pannes télécom, bugs de logiciel, pannes d'infrastructure locale ou défaillances de prestataires [S10]. Argument fort : la continuité est d'abord une question de pannes et de sauvegardes.
- **Rançongiciels** : 28 attaques en 2025, en baisse de 30 % [S10]. Les établissements de santé représentent 61 % des incidents déclarés [S10] ; les libéraux déclarent peu (sous-déclaration probable, estimation).
- **Tous secteurs** : l'hameçonnage est en tête des menaces touchant les professionnels (+45 %) ; la fraude au virement a progressé de 170 % et s'étend à la facturation électronique et à la paie [S15].
- **ANSSI** : la santé représente 11 % des incidents traités par l'ANSSI en 2025 [S16].
- Scénarios typiques en cabinet (estimation) : messagerie du secrétariat piratée puis envoi de faux mails aux patients ; serveur local sans sauvegarde externe qui tombe en panne ; ancien associé ou ancienne secrétaire dont le compte reste actif ; faux RIB d'un fournisseur ou d'un prothésiste.

## Budget et décision d'achat

- **Qui décide** : les associés, souvent en assemblée de la SCM ou de la SEL ; un associé référent prépare le dossier. Le gérant de centre de santé décide seul sous contrainte budgétaire de l'association ou de la mutuelle gestionnaire (estimation).
- **Budget IT habituel** : abonnement logiciel métier 75 à 489 € TTC/mois par praticien [S7], plus matériel et prestataire ; ordre de grandeur 300 à 1 500 € par praticien et par an hors logiciel (estimation).
- **Cycle** : 1 à 3 mois (estimation), car il faut l'accord de plusieurs associés.
- **Sensibilité au prix de 490 € HT** : faible à moyenne. Montant inférieur à un mois de logiciel pour 2 praticiens ; la dotation numérique (jusqu'à 2 940 €/an) crée une perception de « budget numérique » (estimation). Frein principal : temps des praticiens, pas l'argent.

## Déclencheurs et signaux d'achat

- Changement de logiciel métier ou migration Ségur vague 2 (annonces de l'éditeur, offres d'emploi « secrétaire maîtrisant X »).
- Création ou extension d'un cabinet de groupe, maison de santé, centre dentaire ; déménagement ; nouvel associé (annonces légales BODACC, modification de SEL/SCM).
- Recrutement de secrétaires ou d'assistants (offres sur France Travail).
- Incident médiatisé dans un établissement de santé de la région ou fuite chez un éditeur.
- Échéances : localisation EEE HDS (septembre 2026), dotation numérique (indicateurs à remplir), réception des factures électroniques (depuis septembre 2026).
- Lancement d'un outil IA (transcription, secrétariat virtuel) : besoin de vérifier HDS et RGPD.

## Objections probables et réponses

- « Notre éditeur s'occupe de tout, c'est hébergé HDS. » — L'hébergement du logiciel oui ; mais la messagerie, les postes, les comptes Windows, les sauvegardes locales et les scans ne sont pas couverts. Le diagnostic regarde justement ce qui reste hors du logiciel.
- « Pas le temps, on a des patients. » — Une demi-journée, organisée sur un créneau sans consultations ; la plupart des points se vérifient avec la secrétaire ou l'associé référent.
- « Nous sommes trop petits pour être visés. » — 764 incidents déclarés en 2025 par 606 structures, et 38 % ont dégradé la prise en charge ; la majorité de ces interruptions venaient de pannes, pas d'attaques [S10].
- « On a déjà un prestataire informatique. » — Le diagnostic est indépendant : il vérifie ce qui est fait, il ne remplace pas le prestataire. Le rapport peut lui être remis.
- « L'IA, ce n'est pas pour la médecine. » — Le diagnostic ne pousse aucun outil ; il indique quels usages sont compatibles avec le secret médical et l'HDS, et lesquels ne le sont pas.
- « Le RGPD, on a mis une affiche. » — L'affiche est une des obligations ; il reste le registre, les durées de conservation (20 ans recommandés) et les accès [S8].

## Accroches email

1. « Localisation HDS dans l'Espace économique européen : depuis septembre 2026, savez-vous où sont hébergées toutes vos données patients, messagerie comprise ? » [S9]
2. « En 2025, 38 % des incidents en santé ont dégradé la prise en charge, surtout à cause de pannes. Vos sauvegardes sont-elles testées ? » [S10]
3. « Messagerie du secrétariat, comptes d'anciens salariés, sauvegarde du serveur : trois points simples à vérifier avant qu'un incident ne bloque l'agenda. »

## Angle de l'offre Diagnostic IA, RGPD et sauvegardes

- **Regarde en priorité** : localisation et contrats des données (HDS, EEE) pour le logiciel, la messagerie, la prise de RDV et les outils IA ; sauvegarde du serveur local et test de restauration ; comptes et accès (secrétariat, anciens salariés, comptes de maintenance du prestataire, VPN) ; registre des traitements et durée de conservation 20 ans ; usage de MSSanté.
- **3 actions types recommandées** :
  1. Mettre en place une sauvegarde 3-2-1 chiffrée du serveur et des postes avec un test de restauration trimestriel documenté.
  2. Activer la double authentification sur la messagerie et les comptes distants, supprimer les comptes inactifs, cloisonner le compte de maintenance du prestataire.
  3. Remplacer les échanges de données patients par messagerie classique par MSSanté et cadrer par écrit tout outil IA (hébergeur HDS, contrat, information des patients).

## Saisonnalité et moments d'envoi

- **À éviter** : épidémies hivernales (décembre à février, pic de consultations en médecine générale), semaine de Noël, août (congés et remplacements) (estimation).
- **Meilleures périodes** : fin septembre à mi-novembre, mars à juin (estimation).
- **Jours et heures** : mardi à jeudi ; envoi tôt le matin (7 h-8 h) ou en fin de journée, quand le praticien ou l'associé gérant lit ses mails ; le secrétariat filtre souvent l'adresse générique (estimation).

## Où trouver les entreprises

- **annuaire-entreprises.data.gouv.fr** et API Recherche d'entreprises (recherche-entreprises.api.gouv.fr) : filtre `activite_principale` (86.21Z, 86.22A/B/C, 86.23Z, 86.90A-F) + `tranche_effectif_salarie=03,11,12` + `etat_administratif=A` + `departement` [S1][S5].
- **Annuaire santé (RPPS, annuaire.sante.fr)** et annuaires ordinaux (médecins, chirurgiens-dentistes, masseurs-kinésithérapeutes) pour identifier les structures (non vérifié pour les conditions de réutilisation ; ne jamais en extraire de données personnelles).
- **Règle** : écrire uniquement à l'adresse générique de la structure (contact@, secretariat@) ou à l'adresse professionnelle d'une fonction (gérant, associé référent). Pas de nom de praticien en cible du Cortex (I4). Intérêt légitime B2B, message en lien avec l'activité, mention d'opposition simple (« répondre STOP ») dans chaque envoi. Ne jamais utiliser les adresses MSSanté pour prospecter (réservées aux échanges de santé, estimation).

## Sources

[S1] API Recherche d'entreprises — NAF 86.21Z à 86.90F, tranches 03/11/12, actives — https://recherche-entreprises.api.gouv.fr/search?activite_principale=86.21Z,86.22A,86.22B,86.22C,86.23Z,86.90A,86.90B,86.90C,86.90D,86.90E,86.90F&tranche_effectif_salarie=03,11,12&etat_administratif=A&per_page=1 — date non indiquée (données Sirene) — consulté 2026-10-11
[S2] API Recherche d'entreprises — NAF 86.21Z, 6-49 salariés — https://recherche-entreprises.api.gouv.fr/search?activite_principale=86.21Z&tranche_effectif_salarie=03,11,12&etat_administratif=A&per_page=1 — date non indiquée — consulté 2026-10-11
[S3] API Recherche d'entreprises — NAF 86.23Z, 6-49 salariés — https://recherche-entreprises.api.gouv.fr/search?activite_principale=86.23Z&tranche_effectif_salarie=03,11,12&etat_administratif=A&per_page=1 — date non indiquée — consulté 2026-10-11
[S4] API Recherche d'entreprises — NAF 86.90E, 6-49 salariés — https://recherche-entreprises.api.gouv.fr/search?activite_principale=86.90E&tranche_effectif_salarie=03,11,12&etat_administratif=A&per_page=1 — date non indiquée — consulté 2026-10-11
[S5] API Recherche d'entreprises — santé humaine 6-49 salariés, Vienne (86) — https://recherche-entreprises.api.gouv.fr/search?activite_principale=86.21Z,86.22A,86.22B,86.22C,86.23Z,86.90A,86.90B,86.90C,86.90D,86.90E,86.90F&tranche_effectif_salarie=03,11,12&etat_administratif=A&departement=86&per_page=1 — date non indiquée — consulté 2026-10-11
[S6] API Recherche d'entreprises — santé humaine sans filtre d'effectif (plafond 10 000) — https://recherche-entreprises.api.gouv.fr/search?activite_principale=86.21Z,86.22A,86.22B,86.22C,86.23Z,86.90A,86.90B,86.90C,86.90D,86.90E,86.90F&etat_administratif=A&per_page=1 — date non indiquée — consulté 2026-10-11
[S7] La Fabrique du Net, comparatif logiciels médicaux 2026 (source secondaire) — https://www.lafabriquedunet.fr/logiciels/tech/logiciel-medical — mis à jour 2026-10-02 — consulté 2026-10-11
[S8] Conseil national de l'Ordre des médecins, « Protéger les données de santé » — https://www.conseil-national.medecin.fr/medecin/devoirs-droits/proteger-donnees-sante — publié 2019-03-22 — consulté 2026-10-11
[S9] Squire Patton Boggs, « Certification des hébergeurs de données de santé (HDS) : date limite pour la mise en conformité selon le nouveau référentiel » (source secondaire, cabinet d'avocats) — https://larevue.squirepattonboggs.com/certification-des-hebergeurs-de-donnees-de-sante-hds-date-limite-pour-la-mise-en-conformite-selon-le-nouveau-referentiel.html — publié 2026-04-01, mis à jour 2026-05-18 — consulté 2026-10-11
[S10] Caducee.net, « Cybersécurité en santé 2025 : les rançongiciels reculent, les comptes compromis progressent » (synthèse du rapport CERT Santé du 2026-05-11) — https://www.caducee.net/actualite-medicale/16900/cybersecurite-en-sante-2025-les-rancongiciels-reculent-les-comptes-compromis-progressent.html — publié 2026-05-21 — consulté 2026-10-11
[S11] Ministère de l'Économie, « Tout savoir sur la facturation électronique pour les entreprises » — https://www.economie.gouv.fr/tout-savoir-sur-la-facturation-electronique-pour-les-entreprises — date non indiquée (actualité du 2026-09-01) — consulté 2026-10-11
[S12] Tech-Insider, « NIS 2 : 15 000 entités visées, loi bloquée » (source secondaire) — https://tech-insider.org/fr/directive-nis-2-transposition-france-2026/ — publié 2026-07-05 — consulté 2026-10-11
[S13] Leto, « Transposition NIS 2 : le projet de loi Résilience de nouveau reporté » (source secondaire) — https://www.leto.legal/news/assemblee-nationale-report-projet-loi-resilience-nis2-octobre-2026 — date non indiquée (statut au 2026-10-06) — consulté 2026-10-11
[S14] Donneespersonnelles.fr, « Omnibus numérique IA » (source secondaire) — https://donneespersonnelles.fr/omnibus-numerique-ia — publié 2026-08-01, mis à jour 2026-09-12 — consulté 2026-10-11
[S15] Cybermalveillance.gouv.fr, communiqué rapport d'activité 2025 — https://www.cybermalveillance.gouv.fr/medias/2026/03/CP-RA2026.pdf — publié 2026-03-26 — consulté 2026-10-11
[S16] Le Monde Informatique, « Un niveau de menaces toujours très élevé en 2025 selon l'ANSSI » (source secondaire) — https://www.lemondeinformatique.fr/actualites/lire-un-niveau-de-menaces-toujours-tres-eleve-en-2025-selon-l-anssi-99602.html — publié 2026-03-11 — consulté 2026-10-11
