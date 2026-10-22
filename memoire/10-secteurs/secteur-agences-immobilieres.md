---
id: secteur-agences-immobilieres
type: secteur
titre: Agences immobilières, administrateurs de biens et syndics (NAF 6831Z, 6832A)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [secteur, immobilier, agence-immobiliere, syndic, gestion-locative, 6831Z, 6832A, loi-hoguet, lcb-ft, rgpd, dossiers-locataires, faux-rib, extranet-copropriete]
---

# Agences immobilières, administrateurs de biens et syndics

## Identité du secteur

- Codes NAF : **68.31Z** « Agences immobilières » (transaction, souvent aussi gestion locative) et **68.32A** « Administration d'immeubles et autres biens immobiliers » (administrateurs de biens, syndics de copropriété). L'API affiche déjà le futur code NAF 2025 **68.32H** pour certaines entreprises de 68.32A [S1] (calendrier de bascule non vérifié).
- Unités légales actives de **6 à 49 salariés** (tranches 03, 11, 12) : **2 571** en 68.31Z et **1 355** en 68.32A en France ; dans la Vienne, **18** en 68.31Z et **3** en 68.32A [S1][S2][S3][S4] (requêtes du 2026-10-11, ordre de grandeur).
- Branche de l'immobilier (IDCC 1527, données 2019-2021) : **29 874 entreprises** employant au moins un salarié, **147 232 salariés** ; plus de la moitié des salariés travaillent dans des entreprises de moins de 11 salariés, environ un quart dans des entreprises de 11 à 49 [S5].
- Cartes professionnelles : T (transaction), G (gestion), S (syndic), délivrées par la **CCI** du lieu de l'agence, valables **3 ans** [S6]. **5 151 cartes S** délivrées en 2022 selon CCI France [S5].
- Structure type 6-49 (estimation) : un gérant titulaire de la carte, des négociateurs (souvent agents commerciaux indépendants), des gestionnaires locatifs, des gestionnaires de copropriété, un comptable mandant, un accueil.

## Organisation type et outils numériques

- Logiciels (source secondaire) : deux groupes dominent la gestion et la comptabilité immobilière : **Septeo** (suite SPI, marque ICS) et **Orisha Real Estate** (Crypto, Powimo, Even, Gercop) ; **Vilogi** est un indépendant notable en syndic [S7].
- Par métier : transaction (module comptable du logiciel de transaction, par exemple Crypto ou SPI Transaction), gestion locative (SPI, Powimo, Crypto, ICS), syndic (SPI Syndic, Crypto, Powimo, Even, Vilogi) [S7].
- Comptabilité **par mandat sur comptes séparés** obligatoire pour les fonds des clients [S7].
- Syndics : obligation d'un **espace en ligne sécurisé** (extranet) pour les copropriétaires, dont le contenu minimal est précisé depuis le **1er juillet 2020** (règlement de copropriété, carnet d'entretien, contrats d'assurance, PV des trois dernières AG, compte individuel, appels de fonds ; documents supplémentaires pour le conseil syndical) [S8].
- Où sont les données : logiciel métier SaaS, portails d'annonces, CRM, messagerie, dossiers locataires (pièces d'identité, bulletins de salaire), signatures électroniques ; souvent aussi des fichiers locaux et des boîtes mail partagées (estimation).
- Qui gère l'informatique : le gérant, l'éditeur et parfois la tête de réseau pour les agences franchisées (estimation).

## Besoins IT, IA, RGPD et cybersécurité

- Dossiers de candidats locataires : seules certaines pièces sont autorisées (décret n° 2015-1437) ; **interdits** : livret de famille, carte Vitale, relevés de compte bancaire, contrat de mariage ou jugement de divorce, extrait de casier judiciaire [S9]. Exiger un justificatif non autorisé expose à une amende jusqu'à **3 000 €** (**15 000 €** pour une personne morale) [S9].
- Avant la visite, ne collecter que l'identité, les coordonnées et les critères de recherche ; ne pas conditionner la visite à la remise de justificatifs [S9]. La CNIL a adopté un **référentiel sur la gestion locative** en 2021 [S9].
- Outils publics à proposer aux candidats : DossierFacile et FiligraneFacile [S9].
- Fonds de tiers (loyers, dépôts de garantie, fonds de copropriété) : cible des fraudes au virement (estimation).
- IA : rédaction d'annonces, réponses aux demandes, tri des candidatures ; risque de discrimination et de données excessives si l'IA trie les dossiers (estimation). Un chatbot de site doit signaler qu'il est une IA depuis le 2 août 2026 [S10].
- Besoins concrets (estimation) : purge régulière des dossiers de candidats non retenus, boîte de réception des pièces sécurisée (pas de pièces d'identité dans les mails en clair), MFA sur logiciel et portails, procédure anti-faux-RIB pour propriétaires et fournisseurs, sauvegarde ou export des données SaaS.

## Obligations réglementaires et échéances

- **Loi Hoguet** (loi n° 70-9 du 2 janvier 1970) : carte professionnelle, garantie financière si détention de fonds, RC Pro ; renouvellement de carte tous les 3 ans avec **formation continue de 14 heures par an ou 42 heures sur 3 ans** [S6].
- **LCB-FT** : les professionnels de l'immobilier sont assujettis, contrôlés par la **DGCCRF**. Lors d'une campagne de contrôle (2020), **253** professionnels de l'immobilier contrôlés ; au total 104 avertissements, 4 injonctions et 58 procès-verbaux transmis à la Commission nationale des sanctions [S11]. Manquements typiques : pas de protocole écrit d'évaluation des risques, procédures d'identification insuffisantes, peu de traces des vérifications, registre des gels et registre des bénéficiaires effectifs non consultés, déclarations de soupçon rares [S11]. Tracfin a publié une plaquette immobilier en janvier 2026 [S12] (titre seul).
- **Facturation électronique** : réception obligatoire depuis le **1er septembre 2026** ; émission et e-reporting au **1er septembre 2027** pour PME et micro-entreprises [S13]. Les honoraires facturés à des particuliers relèvent de l'e-reporting (estimation).
- **Prospection téléphonique** : depuis le **11 août 2026**, le démarchage téléphonique des consommateurs exige leur **consentement préalable** (loi n° 2025-594 du 30 juin 2025, décret n° 2026-662 du 23 juillet 2026) ; preuve à conserver **3 ans** ; amende jusqu'à **375 000 €** pour une personne morale [S14]. Impacte la pige téléphonique des agences auprès des vendeurs particuliers (estimation).
- **AI Act** : transparence depuis le **2 août 2026** [S10].

## Risques et incidents typiques

- Fraude au virement : +170 % en 2025 (tous publics) ; fraude au faux conseiller bancaire +159 % [S15]. Scénario type : faux mail d'agence ou de syndic envoyant un nouveau RIB pour le dépôt de garantie, les loyers ou les appels de fonds (estimation).
- Fuite de dossiers de locataires (pièces d'identité, bulletins de salaire) via une boîte mail compromise ou un lien de partage public (estimation).
- Faux dossiers de candidats (documents falsifiés) (estimation).
- Indisponibilité du logiciel ou de l'extranet de copropriété en période d'assemblées générales (estimation).

## Budget et décision d'achat

- Décideur : le gérant titulaire de la carte ; en réseau franchisé, la tête de réseau impose souvent les logiciels (estimation).
- Budget IT : abonnements logiciels métiers sur devis selon lots et modules [S7] ; 490 € HT est inférieur à une commission sur une petite transaction (estimation).
- Sensibilité au prix : moyenne ; le marché de la transaction est cyclique et les agences surveillent leurs charges (estimation).
- Cycle : court pour un gérant unique, plus long pour un administrateur de biens avec plusieurs services (estimation).

## Déclencheurs et signaux d'achat

- Ouverture d'une nouvelle agence, rachat d'un portefeuille de gestion ou de syndic.
- Renouvellement de carte professionnelle (tous les 3 ans) [S6].
- Contrôle DGCCRF LCB-FT dans le secteur ou dans le département.
- Changement de logiciel (consolidation des éditeurs Septeo et Orisha) [S7].
- Recrutements de gestionnaires locatifs ou de copropriété.
- Fin de la pige téléphonique sans consentement depuis le 11 août 2026 : l'agence repense sa prospection et ses outils [S14].

## Objections probables et réponses

- « Notre réseau gère tout. » → Le réseau fournit les logiciels ; vos boîtes mail, postes et dossiers locataires restent sous votre responsabilité RGPD.
- « Nous respectons déjà la liste des pièces. » → Le diagnostic vérifie aussi la durée de conservation et l'endroit où ces pièces circulent (mails, téléphones des négociateurs).
- « Le marché est difficile, ce n'est pas le moment. » → Justement : le diagnostic est ponctuel, à 490 € HT, et priorise 3 actions sans abonnement obligatoire.
- « L'éditeur sauvegarde nos données. » → Il sauvegarde sa plateforme ; vérifions que vous pouvez exporter vos mandats et comptes si le service tombe ou si vous changez d'éditeur.
- « LCB-FT, c'est l'affaire des notaires. » → La DGCCRF relève justement cette idée reçue comme un manquement fréquent.

## Accroches email

1. « La DGCCRF relève souvent l'absence de trace des vérifications LCB-FT dans les agences. Vos dossiers gardent-ils cette preuve ? »
2. « Les dossiers locataires contiennent pièces d'identité et bulletins de salaire. Combien de temps restent-ils dans vos boîtes mail ? »
3. « Un faux RIB envoyé au nom de votre agence pour un dépôt de garantie : votre procédure de vérification est-elle écrite ? »

## Angle de l'offre Diagnostic IA, RGPD et sauvegardes

Ce que le diagnostic regarde en priorité :
- Circuit des dossiers locataires : collecte, stockage, durée de conservation, conformité à la liste des pièces autorisées.
- Comptes et accès : MFA sur logiciel métier, portails et messagerie ; comptes des agents commerciaux partis.
- Flux financiers : procédure de changement de RIB (propriétaires, locataires, copropriétés, fournisseurs).
- Réversibilité : export des données du logiciel et de l'extranet.
- Traçabilité LCB-FT dans les outils.

Trois actions types :
1. Règle de purge des dossiers de candidats non retenus et canal sécurisé de réception des pièces (ou DossierFacile).
2. MFA généralisée et procédure anti-faux-RIB avec contre-appel.
3. Modèle de fiche LCB-FT intégrée au logiciel et export mensuel des données métier.

## Saisonnalité et moments d'envoi

- Transaction et location : forte activité au printemps et à la rentrée (estimation).
- Syndics : assemblées générales concentrées d'avril à juin (exercices clos au 31 décembre) (estimation, non sourcé).
- Meilleures fenêtres : janvier-février, juillet, novembre (estimation).
- Jours : éviter le samedi et le lundi (visites et réunions) ; préférer mardi-jeudi matin (estimation).

## Où trouver les entreprises

- annuaire-entreprises.data.gouv.fr / API Recherche d'entreprises : `activite_principale=68.31Z` ou `68.32A`, `tranche_effectif_salarie=03,11,12`, `departement=86`, `etat_administratif=A` [S1][S2][S3][S4].
- Fichier des cartes professionnelles tenu par les CCI (titulaires de cartes T, G, S) (non vérifié : accès public et URL non consultés).
- Règles : adresse générique de l'agence ou adresse professionnelle d'une fonction (gérant, responsable gestion) ; intérêt légitime B2B ; message lié à l'activité ; « répondre STOP » ; aucun nom de négociateur ou de gérant dans la mémoire du Cortex.

## Sources

[S1] API Recherche d'entreprises, 68.32A, tranches 03,11,12, actives, France — https://recherche-entreprises.api.gouv.fr/search?activite_principale=68.32A&tranche_effectif_salarie=03,11,12&etat_administratif=A&per_page=1 — date non indiquée — consulté 2026-10-11
[S2] API Recherche d'entreprises, 68.31Z, tranches 03,11,12, actives, France — https://recherche-entreprises.api.gouv.fr/search?activite_principale=68.31Z&tranche_effectif_salarie=03,11,12&etat_administratif=A&per_page=1 — date non indiquée — consulté 2026-10-11
[S3] API Recherche d'entreprises, 68.31Z, Vienne (86) — https://recherche-entreprises.api.gouv.fr/search?activite_principale=68.31Z&tranche_effectif_salarie=03,11,12&etat_administratif=A&departement=86&per_page=1 — date non indiquée — consulté 2026-10-11
[S4] API Recherche d'entreprises, 68.32A, Vienne (86) — https://recherche-entreprises.api.gouv.fr/search?activite_principale=68.32A&tranche_effectif_salarie=03,11,12&etat_administratif=A&departement=86&per_page=1 — date non indiquée — consulté 2026-10-11
[S5] Panorama de la branche de l'immobilier, édition 2022 (OPCO EP) — https://www.opcoep.fr/ressources/centre-ressources/branches/immobilier/panorama-immobilier-opcoep.pdf — publié 2022 — consulté 2026-10-11
[S6] Les différents types de cartes professionnelles de l'immobilier (FNAIM) — https://www.fnaim.fr/espace-adhesion/4240-les-differents-types-de-carte-immobiliere.htm — date non indiquée — consulté 2026-10-11
[S7] Logiciel de comptabilité immobilière : agence, gestion locative ou syndic ? (La Fabrique du Net, source secondaire) — https://www.lafabriquedunet.fr/logiciels/gestion/comptabilite/comptabilite-immobilier — date non indiquée — consulté 2026-10-11
[S8] Parole d'expert : documents que le syndic doit mettre en ligne dans un espace sécurisé (ANIL) — https://www.anil.org/parole-expert-logement-copropriete-espace-securise/ — à jour au 2020-10-20 — consulté 2026-10-11
[S9] Location d'un bien immobilier : quels justificatifs peut-on demander aux candidats ? (CNIL) — https://www.cnil.fr/fr/location-dun-bien-immobilier-quels-justificatifs — publié 2025-10-10 — consulté 2026-10-11
[S10] Règlement européen sur l'IA : des mesures concrètes pour informer et protéger les internautes (economie.gouv.fr) — https://www.economie.gouv.fr/actualites/reglement-europeen-sur-lia-des-mesures-concretes-pour-informer-et-proteger-les-internautes — publié 2026-08-25 — consulté 2026-10-11
[S11] Blanchiment de capitaux et financement du terrorisme : les secteurs du luxe, de l'immobilier et de la domiciliation d'entreprises encore insuffisamment vigilants (DGCCRF) — https://www.economie.gouv.fr/dgccrf/blanchiment-de-capitaux-et-financement-du-terrorisme-les-secteurs-du-luxe-de-limmobilier-et — date non indiquée (contrôles 2020, publication probable 2022) — consulté 2026-10-11
[S12] Le dispositif de lutte contre le blanchiment, plaquette immobilier (Tracfin) — https://www.economie.gouv.fr/files/files/directions_services/tracfin/media-document/Plaquette%20Immo_012026_def_0.pdf — publié 2026-01 (d'après le nom du fichier) — consulté 2026-10-11 (titre seul)
[S13] Tout savoir sur la facturation électronique pour les entreprises (economie.gouv.fr) — https://www.economie.gouv.fr/tout-savoir-sur-la-facturation-electronique-pour-les-entreprises — date non indiquée — consulté 2026-10-11
[S14] Réforme du démarchage téléphonique : mise en pratique depuis le 11 août 2026 (Actu-Juridique) — https://www.actu-juridique.fr/affaires/droit-economique/reforme-du-demarchage-telephonique-mise-en-pratique-depuis-le-11-aout-2026/ — publié 2026-09-17 — consulté 2026-10-11
[S15] Communiqué de presse, rapport d'activité 2025 de Cybermalveillance.gouv.fr — https://www.cybermalveillance.gouv.fr/medias/2026/03/CP-RA2026.pdf — publié 2026-03-26 — consulté 2026-10-11
