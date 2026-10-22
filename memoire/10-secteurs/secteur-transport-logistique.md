---
id: secteur-transport-logistique
type: secteur
titre: Transport routier de marchandises et logistique (NAF 49.41, 49.42, 52)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [transport, logistique, trm, entreposage, chronotachygraphe, tachygraphe-intelligent, tms, ecmr, efti, nis2, continuite, vol-de-fret, hameconnage, faux-rib, facturation-electronique]
---

## Identité du secteur

- Codes NAF : 49.41A (transports routiers de fret interurbains), 49.41B (fret de proximité), 49.41C (location de camions avec chauffeur), 49.42Z (déménagement), 52.10A/B (entreposage frigorifique et non frigorifique), 52.21Z (services auxiliaires des transports terrestres), 52.24A/B (manutention portuaire et non portuaire), 52.29A/B (messagerie-fret express, affrètement et organisation des transports).
- Unités légales actives de **6 à 49 salariés** : **9 936** en transport routier de fret (49.41A/B/C) [S1] et **2 502** en entreposage, manutention et organisation des transports (52.x) [S2].
- Vienne (86), tous ces codes : **90** entreprises de 6 à 49 salariés [S3].
- Effectif typique 6-49 : dirigeant (souvent ancien conducteur ou héritier d'une entreprise familiale), un exploitant ou affréteur, une personne à l'administratif (paie, facturation, tachygraphes), 5 à 40 conducteurs ; en logistique, un chef de quai et des préparateurs (estimation).

## Organisation type et outils numériques

- **TMS (logiciel de gestion du transport)** : ordres de transport, planning, facturation ; éditeurs pour PME du transport nombreux (noms non vérifiés ici). **WMS** pour l'entreposage.
- **Télématique et tachygraphes** : boîtiers embarqués de géolocalisation, logiciels de téléchargement et d'analyse des données tachygraphes (cartes conducteurs et mémoire des appareils) ; éditeurs télématiques visibles : Geotab, Samsara, Michelin Connected Fleet, qui publient des guides sur les nouvelles obligations [S4].
- **Bourses de fret** et plateformes d'affrètement en ligne, messagerie, EDI avec les chargeurs.
- **Où sont les données** : TMS en SaaS ou sur un serveur au bureau ; fichiers tachygraphes téléchargés sur un PC dédié ; documents de transport (CMR, bons de livraison) encore largement papier ou en photo sur le téléphone du conducteur (estimation).
- **Qui gère l'informatique** : le dirigeant ou la personne administrative, avec le support des éditeurs TMS et télématique ; rarement un prestataire informatique global (estimation).

## Besoins IT, IA, RGPD et cybersécurité

- **Données tachygraphes** : télécharger les cartes conducteurs au moins tous les 28 jours et la mémoire des appareils au moins tous les 90 jours ; archiver les fichiers un à deux ans [S5]. Besoin d'une sauvegarde fiable et horodatée : en cas de contrôle, l'absence de fichiers est sanctionnée (en France jusqu'à 30 000 €, un an d'emprisonnement et immobilisation selon la source) [S5].
- **Continuité d'exploitation** : si le TMS ou la messagerie tombe, plus de planning, plus de facturation ; un rançongiciel peut paralyser des chaînes d'approvisionnement entières en quelques heures [S6].
- **Vol de fret par usurpation** : hameçonnage et usurpation d'identité d'entités légitimes pour s'emparer de chargements [S6] (fausses offres ou faux transporteurs sur bourses de fret).
- **Géolocalisation des véhicules (RGPD)** : encadrer l'usage des données de géolocalisation des conducteurs (information, finalités, durée de conservation) (non vérifié dans une source consultée ici ; référentiel CNIL à consulter).
- **IA** : optimisation de tournées, saisie automatique des documents de transport (lecture des CMR et bons de livraison), réponse aux demandes de cotation, analyse des infractions tachygraphes (estimation).

## Obligations réglementaires et échéances

- **Tachygraphe intelligent pour les utilitaires** : depuis le 1er juillet 2026, les véhicules et ensembles de 2,5 à 3,5 tonnes de PTAC utilisés en transport international ou en cabotage pour compte d'autrui doivent être équipés d'un tachygraphe intelligent de deuxième génération version 2, installé et calibré par un atelier agréé [S5]. Dérogations : « artisan » (moins de 100 km, conduite non principale, PTAC jusqu'à 7,5 t) et compte propre [S5].
- **Documents de transport électroniques (eFTI)** : à partir de mi-2027, les autorités de tous les États membres devront accepter les informations électroniques sur le transport de marchandises ; les plateformes eFTI doivent être certifiées [S7] (à revérifier 2027-03). La situation de l'e-CMR en France n'est pas confirmée par la source consultée (non vérifié).
- **Facturation électronique** : réception obligatoire depuis le 1er septembre 2026 pour toutes les entreprises ; les grandes entreprises et ETI (chargeurs, commissionnaires) émettent déjà ; émission et e-reporting au 1er septembre 2027 pour les petites et micro-entreprises [S8]. Le TMS doit produire des factures au bon format ou passer par une plateforme agréée [S8].
- **NIS2** : le secteur des transports figure dans l'annexe I et les services postaux et de messagerie (express) dans l'annexe II [S9]. Seuil entité importante : au moins 50 salariés ou plus de 10 M€ de CA ou de bilan [S9]. Les transporteurs de 6-49 salariés sont a priori hors champ direct, sauf CA supérieur à 10 M€ ; le périmètre exact des sous-secteurs du transport routier visés est à vérifier sur le texte (non vérifié). La loi de transposition n'est pas adoptée au 6 octobre 2026 [S10].
- **AI Act** : obligations des systèmes à haut risque de l'annexe III reportées au 2 décembre 2027 [S11] ; peu d'impact direct pour une PME de transport (estimation).

## Risques et incidents typiques

- **Risque n°1 du secteur** : les cyberattaques sont classées premier risque du transport et de la logistique (enquête Aon 2025, près de 3 000 répondants dans 63 pays) ; jusqu'à 17,7 % des entreprises du secteur ont subi des pertes liées à une cyberattaque sur 12 mois [S6].
- **Faillite après rançongiciel** : un transporteur britannique (KNP Logistics) a fait faillite trois mois après un rançongiciel favorisé par des mots de passe faibles et l'absence de double authentification, avec 700 emplois perdus [S6]. Cas parlant pour une PME.
- **Attaque par la chaîne d'approvisionnement** : plus de 70 % des responsables sécurité interrogés ont subi un incident majeur impliquant un fournisseur [S6] (étude citée par une source secondaire).
- **Vol de fret** : incidents graves en période de fêtes passés de 49 en 2020 à 89 en 2024 aux États-Unis (Verisk CargoNet), pics le 23 et du 26 au 30 décembre [S6].
- **Tous secteurs, France** : hameçonnage en tête des menaces touchant les professionnels (+45 %), fraude au virement +170 % s'étendant à la facturation électronique [S12]. Un transporteur qui facture des dizaines de chargeurs est une cible pour les faux changements de RIB (estimation).

## Budget et décision d'achat

- **Qui décide** : le dirigeant ; la personne administrative et l'exploitant influencent sur les outils du quotidien (estimation).
- **Budget IT habituel** : abonnements TMS et télématique par véhicule, logiciel tachygraphe, quelques PC ; l'essentiel du budget numérique part dans l'embarqué (estimation non sourcée). Marges faibles dans le secteur, achats négociés serrés (estimation).
- **Cycle** : court si lié à une obligation datée (tachygraphe, facture électronique) ou à un incident ; sinon faible priorité (estimation).
- **Sensibilité au prix de 490 € HT** : moyenne à élevée. Argument : moins que le coût d'une journée d'immobilisation de la flotte ou d'une amende tachygraphe (estimation).

## Déclencheurs et signaux d'achat

- Échéance tachygraphe des utilitaires (depuis le 1er juillet 2026) pour les entreprises de messagerie ou de fret léger international [S5].
- Bascule facture électronique (réception septembre 2026, émission septembre 2027) et changement de TMS [S8].
- Exigences d'un grand chargeur ou d'un commissionnaire (questionnaire sécurité, EDI, documents électroniques).
- Annonce d'eFTI pour mi-2027 et projets de dématérialisation des CMR [S7].
- Incident médiatisé chez un transporteur, une plateforme logistique ou un partenaire ; attaque visant La Poste en décembre 2025 [S6].
- Ouverture d'une agence ou d'un entrepôt, achat de véhicules, reprise d'entreprise (annonces légales, offres d'emploi d'exploitants).

## Objections probables et réponses

- « Notre éditeur TMS sauvegarde tout. » — Il sauvegarde le TMS ; pas forcément les fichiers tachygraphes, la messagerie, les documents scannés ni les postes. Le diagnostic vérifie l'ensemble et le délai de redémarrage.
- « On n'a pas le temps, nos camions roulent. » — Le diagnostic se fait au bureau avec l'administratif et l'exploitant, sans toucher aux véhicules.
- « La cyber, c'est pour les gros. » — Un transporteur britannique a fait faillite trois mois après un rançongiciel lié à des mots de passe faibles [S6].
- « La géolocalisation, on a le droit. » — Oui, sous conditions ; le diagnostic vérifie l'information des conducteurs et la durée de conservation, pour éviter un litige prud'homal ou une plainte (estimation).
- « Le tachygraphe, c'est le boulot du logiciel. » — Le logiciel télécharge ; il faut encore vérifier que les fichiers sont archivés hors du PC de bureau pendant la durée exigée [S5].

## Accroches email

1. « Cartes conducteurs tous les 28 jours, appareils tous les 90 jours : vos fichiers tachygraphes sont-ils sauvegardés ailleurs que sur un PC ? » [S5]
2. « Un transporteur a fait faillite trois mois après un rançongiciel. Combien de temps tiendrait votre exploitation sans TMS ? » [S6]
3. « Avec la facture électronique, les faux messages de changement de RIB se multiplient. Comment vos chargeurs vérifient-ils vos coordonnées bancaires ? » [S12]

## Angle de l'offre Diagnostic IA, RGPD et sauvegardes

- **Regarde en priorité** : sauvegarde et archivage des fichiers tachygraphes ; plan de continuité si le TMS ou la messagerie tombe (planning papier, contacts chargeurs) ; double authentification sur messagerie, TMS, bourses de fret et banque ; procédure de vérification des RIB et des nouveaux donneurs d'ordre ; cadre RGPD de la géolocalisation ; préparation facture électronique et documents électroniques.
- **3 actions types recommandées** :
  1. Automatiser l'archivage des fichiers tachygraphes vers un stockage sauvegardé, avec contrôle mensuel des téléchargements à 28 et 90 jours [S5].
  2. Activer la double authentification sur tous les comptes critiques et rédiger une fiche « fonctionnement dégradé » d'une page pour l'exploitation.
  3. Mettre en place une vérification systématique (contre-appel) des nouveaux affréteurs et de tout changement de coordonnées bancaires, et vérifier l'information des conducteurs sur la géolocalisation.

## Saisonnalité et moments d'envoi

- **À éviter** : novembre-décembre (pic de fin d'année, période de vols de fret) [S6], fin de mois (facturation), juillet-août selon l'activité (estimation).
- **Meilleures périodes** : janvier-mars, mai-juin, septembre-octobre (estimation).
- **Jours et heures** : mardi à jeudi, en milieu de matinée une fois les départs organisés (9 h-11 h) ou en début d'après-midi ; éviter le lundi matin et le vendredi après-midi (estimation).

## Où trouver les entreprises

- **annuaire-entreprises.data.gouv.fr** et API Recherche d'entreprises : `activite_principale` (49.41A, 49.41B, 49.41C, 49.42Z, 52.10A, 52.10B, 52.21Z, 52.24A, 52.24B, 52.29A, 52.29B) + `tranche_effectif_salarie=03,11,12` + `etat_administratif=A` + `departement=86` [S1][S2][S3].
- Registre électronique national des entreprises de transport par route (publié par le ministère chargé des transports, non vérifié ici pour les conditions de réutilisation).
- **Règle** : adresse générique de l'entreprise (contact@, exploitation@) ou adresse professionnelle d'une fonction (dirigeant, responsable d'exploitation, responsable administratif). Jamais de conducteur nommé ni de numéro de portable. Intérêt légitime B2B, objet lié à l'activité, opposition simple (« répondre STOP ») dans chaque envoi.

## Sources

[S1] API Recherche d'entreprises — NAF 49.41A/B/C, 6-49 salariés, actives — https://recherche-entreprises.api.gouv.fr/search?activite_principale=49.41A,49.41B,49.41C&tranche_effectif_salarie=03,11,12&etat_administratif=A&per_page=1 — date non indiquée (données Sirene) — consulté 2026-10-11
[S2] API Recherche d'entreprises — NAF 52.x, 6-49 salariés, actives — https://recherche-entreprises.api.gouv.fr/search?activite_principale=52.10A,52.10B,52.21Z,52.24A,52.24B,52.29A,52.29B&tranche_effectif_salarie=03,11,12&etat_administratif=A&per_page=1 — date non indiquée — consulté 2026-10-11
[S3] API Recherche d'entreprises — transport et logistique 6-49 salariés, Vienne (86) — https://recherche-entreprises.api.gouv.fr/search?activite_principale=49.41A,49.41B,49.41C,49.42Z,52.10A,52.10B,52.21Z,52.24A,52.24B,52.29A,52.29B&tranche_effectif_salarie=03,11,12&etat_administratif=A&departement=86&per_page=1 — date non indiquée — consulté 2026-10-11
[S4] Geotab, « Guide de conformité tachygraphe VUL » (éditeur, cité comme exemple d'acteur ; contenu non consulté) — https://www.geotab.com/fr/livre-blanc/guide-conformite-tachygraphe-vul/ — date non indiquée — consulté 2026-10-11
[S5] Trans.info, « Chronotachygraphe obligatoire pour certains utilitaires légers dès juillet 2026 » (source secondaire, presse transport) — https://trans.info/fr/chronotachygraphe-obligatoire-pour-certains-utilitaires-legers-des-juillet-2026-vehicules-concernes-derogations-et-sanctions-faq-484865 — publié 2026-06-29 — consulté 2026-10-11
[S6] Trans.info, cyberattaques dans le transport et la logistique en 2025 (source secondaire) — https://trans.info/fr/transport-cyberattaques-2025-455060 — publié 2026-03-30 — consulté 2026-10-11
[S7] Trans.info, règlement eFTI (source secondaire) — https://trans.info/fr/reglement-efti-transport-europe-451478 — publié 2026-02-03 — consulté 2026-10-11
[S8] Ministère de l'Économie, « Tout savoir sur la facturation électronique pour les entreprises » — https://www.economie.gouv.fr/tout-savoir-sur-la-facturation-electronique-pour-les-entreprises — date non indiquée (actualité du 2026-09-01) — consulté 2026-10-11
[S9] Tech-Insider, « NIS 2 : 15 000 entités visées, loi bloquée » (source secondaire) — https://tech-insider.org/fr/directive-nis-2-transposition-france-2026/ — publié 2026-07-05 — consulté 2026-10-11
[S10] Leto, « Transposition NIS 2 : le projet de loi Résilience de nouveau reporté » (source secondaire) — https://www.leto.legal/news/assemblee-nationale-report-projet-loi-resilience-nis2-octobre-2026 — date non indiquée (statut au 2026-10-06) — consulté 2026-10-11
[S11] Donneespersonnelles.fr, « Omnibus numérique IA » (source secondaire) — https://donneespersonnelles.fr/omnibus-numerique-ia — publié 2026-08-01, mis à jour 2026-09-12 — consulté 2026-10-11
[S12] Cybermalveillance.gouv.fr, communiqué rapport d'activité 2025 — https://www.cybermalveillance.gouv.fr/medias/2026/03/CP-RA2026.pdf — publié 2026-03-26 — consulté 2026-10-11
