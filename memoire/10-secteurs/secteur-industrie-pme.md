---
id: secteur-industrie-pme
type: secteur
titre: PME industrielles — manufacture, mécanique, agroalimentaire (NAF 10 à 33)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [industrie, pme, agroalimentaire, mecanique, ot-it, nis2, sous-traitance, cyber-resilience-act, espionnage, continuite, rancongiciel, facturation-electronique]
---

## Identité du secteur

- Codes NAF : section C, divisions 10 à 33 (10-11 agroalimentaire et boissons, 20-22 chimie et plastique, 24-25 métallurgie et produits métalliques, 26-28 électronique, équipements électriques et machines, 29-30 matériels de transport, 31-33 meubles, autres industries, réparation et installation de machines).
- Unités légales actives de **20 à 49 salariés** dans la section C : au moins **10 000** (l'API plafonne à 10 000 résultats, le chiffre réel est supérieur) [S1].
- Vienne (86) : **364** unités légales industrielles actives de 6 à 49 salariés [S2], dont **120** de 20 à 49 salariés [S3]. C'est le plus gros vivier local de JOSY EI avec le BTP.
- Effectif typique 6-49 : dirigeant-fondateur ou repreneur, 1 à 3 cadres (production, commercial, administratif et financier), 1 responsable qualité, 5 à 40 opérateurs et techniciens (estimation).

## Organisation type et outils numériques

- **Deux mondes** : l'informatique de gestion (IT : ERP/GPAO, comptabilité, messagerie, CAO) et l'informatique industrielle (OT : automates, machines à commande numérique, robots, supervision) [S4].
- **Logiciels courants** : ERP/GPAO pour PME (Sage, Divalto, Silog, Clipper, Odoo, Microsoft Dynamics, Cegid ; non vérifié pour les parts de marché), CAO/FAO (SolidWorks, TopSolid, non vérifié), logiciel qualité et traçabilité (agroalimentaire : traçabilité des lots, HACCP).
- **Où sont les données** : serveur local dans un bureau ou un local technique (ERP, plans, programmes machines), postes d'atelier anciens, clés USB pour transférer les programmes vers les machines, de plus en plus de cloud pour la messagerie et la comptabilité (estimation).
- **Qui gère l'informatique** : le responsable administratif et financier ou le dirigeant, avec un prestataire informatique local pour l'IT ; les intégrateurs et fabricants de machines gèrent l'OT avec des accès de télémaintenance (estimation). Les systèmes industriels ont des cycles de vie bien plus longs que l'informatique de bureau et ne peuvent pas être arrêtés facilement pour des mises à jour [S4].

## Besoins IT, IA, RGPD et cybersécurité

- **Cartographier et contrôler les accès OT** (usine, bureaux, sous-traitants, fournisseurs), surveiller ou limiter chaque point d'entrée [S4]. Une faille peut être n'importe où dans l'entreprise : ordinateurs, bornes Wi-Fi, photocopieurs [S4].
- **Continuité de production** : machines ralenties ou arrêtées, réglages modifiés produisant des pièces défectueuses ou non conformes (exemple agroalimentaire) [S4]. Besoin d'un plan de reprise : sauvegarde de l'ERP et des programmes machines, procédure de fonctionnement dégradé.
- **Espionnage et propriété intellectuelle** : vol de plans et de procédés ; l'espionnage ciblé peut rester caché des mois dans les systèmes [S4].
- **Exigences des donneurs d'ordre** : questionnaires sécurité et clauses cyber dans les contrats des grands clients, appelés à se renforcer avec NIS2 (estimation).
- **RGPD** : surtout données RH (paie, badges, vidéosurveillance, géolocalisation des commerciaux) et données clients B2B ; enjeu modéré comparé à l'OT (estimation).
- **IA** : maintenance prédictive, contrôle qualité par vision, aide à la rédaction d'offres techniques, assistant de recherche documentaire sur les procédures ; frein : peur de fuite des plans et savoir-faire dans des outils grand public (estimation).

## Obligations réglementaires et échéances

- **NIS2** : la fabrication (dont dispositifs médicaux, informatique, machines, véhicules) et la production et distribution de denrées alimentaires figurent dans l'annexe II (secteurs critiques) [S5]. Seuil entité importante : au moins 50 salariés ou plus de 10 M€ de CA ou de bilan [S5]. Une PME de 6-49 salariés est hors champ direct sauf CA ou bilan supérieur à 10 M€ (fréquent en agroalimentaire ou négoce industriel, estimation). Environ 15 000 entités visées en France [S5]. La loi de transposition (projet de loi Résilience) n'est pas adoptée : retirée de l'ordre du jour de l'Assemblée le 6 octobre 2026, réinscription espérée sous quelques semaines [S6] (à revérifier 2026-12).
- **Effet indirect NIS2** : les clients soumis à NIS2 devront maîtriser la sécurité de leur chaîne d'approvisionnement et répercuteront des exigences sur leurs sous-traitants (estimation, à confirmer sur le texte définitif).
- **Cyber Resilience Act (règlement UE 2024/2847)** : depuis le 11 septembre 2026, tout fabricant qui met sur le marché européen un produit comportant au moins un élément numérique doit signaler les vulnérabilités activement exploitées et incidents graves : alerte sous 24 h à l'ENISA, rapport sous 72 h, rapport final sous 14 jours ; l'obligation vaut aussi pour les produits déjà vendus [S7]. Application complète en décembre 2027 [S7]. Concerne les PME qui fabriquent des machines ou équipements connectés, avec automate ou logiciel embarqué (estimation).
- **Facturation électronique** : réception obligatoire depuis le 1er septembre 2026 ; les grandes entreprises et ETI émettent depuis cette date, donc les sous-traitants de grands groupes reçoivent déjà des factures électroniques ; émission et e-reporting au 1er septembre 2027 pour les petites et micro-entreprises [S8].
- **AI Act** : systèmes à haut risque intégrés aux produits réglementés (annexe I, dont machines) reportés au 2 août 2028 ; annexe III au 2 décembre 2027 [S9] (source secondaire).

## Risques et incidents typiques

- **Rançongiciel** : 128 compromissions par rançongiciel traitées par l'ANSSI en 2025 ; environ 48 % des victimes sont des petites structures (TPE, PME, ETI) [S10].
- **Hameçonnage et fraude au virement** : hameçonnage en tête des menaces touchant les professionnels (+45 %) ; fraude au virement +170 %, s'étendant à la facturation électronique et à la gestion de la paie [S11]. Les industriels, qui paient de nombreux fournisseurs, sont exposés au faux changement de RIB (estimation).
- **Attaque par un fournisseur** : un constructeur automobile a dû arrêter ses usines après une cyberattaque visant un fournisseur externe de composants [S12]. Illustre le risque de propagation dans la chaîne de sous-traitance.
- **Pannes** : panne du serveur ERP ou perte des programmes machines sans sauvegarde : arrêt de production et retards de livraison (estimation).
- **Accès de télémaintenance** laissés ouverts en permanence par les fabricants de machines (estimation).

## Budget et décision d'achat

- **Qui décide** : le dirigeant, souvent sur proposition du responsable administratif et financier ; le responsable production ou qualité a un droit de veto si l'intervention touche l'atelier (estimation).
- **Budget IT habituel** : de l'ordre de 1 à 3 % du CA pour l'IT de gestion dans une PME industrielle (estimation non sourcée) ; l'OT est budgétée avec les investissements machines.
- **Cycle** : 1 à 3 mois pour une prestation de conseil sous 1 000 € ; plus long si un investissement suit (estimation).
- **Sensibilité au prix de 490 € HT** : faible. Montant inférieur à une heure d'arrêt de ligne dans beaucoup d'ateliers (estimation). Le frein est la crédibilité industrielle : un consultant IT doit montrer qu'il comprend la contrainte de production et ne touchera pas aux machines sans accord.

## Déclencheurs et signaux d'achat

- Questionnaire sécurité ou clause cyber reçu d'un donneur d'ordre (automobile, aéronautique, défense, grande distribution) ; référencement fournisseur.
- Débats sur la loi Résilience (NIS2) et entrée en application du Cyber Resilience Act (11 septembre 2026) [S6][S7].
- Incident chez un voisin industriel, un client ou un fournisseur relayé par la presse régionale.
- Investissement machine, extension de bâtiment, nouveau site, reprise d'entreprise (annonces légales, aides régionales, presse locale).
- Changement d'ERP, recrutement d'un responsable administratif et financier ou d'un responsable informatique.
- Projet IA (vision, maintenance) annoncé ou subventionné.

## Objections probables et réponses

- « Nos machines ne sont pas connectées. » — Souvent, les programmes passent par clé USB et les fabricants ont un accès de télémaintenance. Le diagnostic vérifie simplement ces points d'entrée [S4].
- « NIS2 ne nous concerne pas, on a moins de 50 salariés. » — Exact en direct si le CA reste sous 10 M€ [S5] ; mais vos clients concernés vous enverront leurs exigences. Le diagnostic prépare les réponses.
- « Notre prestataire informatique gère. » — Il gère l'IT de bureau ; l'OT et les accès des fabricants de machines restent souvent sans responsable clair. Le rapport peut lui être remis.
- « On ne peut pas arrêter la production pour un audit. » — Le diagnostic est non intrusif : entretiens et vérifications sur l'IT, aucune intervention sur les machines.
- « L'IA, ce n'est pas pour l'atelier. » — Le diagnostic identifie seulement les usages simples et sûrs (documentation, offres, qualité) et les règles pour ne pas exposer les plans.
- « Les rançongiciels visent les grands groupes. » — Près de la moitié des victimes de rançongiciel suivies par l'ANSSI en 2025 sont des petites structures [S10].

## Accroches email

1. « Depuis le 11 septembre 2026, le Cyber Resilience Act impose de signaler sous 24 h toute faille exploitée d'un produit connecté. Êtes-vous prêts ? » [S7]
2. « Vos clients soumis à NIS2 vont questionner la sécurité de leurs sous-traitants. Avez-vous déjà une réponse écrite à leur fournir ? »
3. « Si votre serveur ERP tombait demain, combien de temps faudrait-il pour relancer la production avec les bons programmes machines ? »

## Angle de l'offre Diagnostic IA, RGPD et sauvegardes

- **Regarde en priorité** : sauvegarde et restauration de l'ERP, des plans et des programmes machines ; séparation réseau bureau / atelier ; accès de télémaintenance et comptes des prestataires ; procédure de validation des changements de RIB fournisseurs ; état des questionnaires sécurité clients ; usages IA et protection du savoir-faire.
- **3 actions types recommandées** :
  1. Mettre en place une sauvegarde hors ligne de l'ERP et des programmes machines, avec un test de restauration et une procédure de fonctionnement dégradé écrite.
  2. Inventorier et fermer par défaut les accès de télémaintenance (ouverture à la demande, comptes nominatifs, double authentification) [S4].
  3. Instaurer un contre-appel systématique, à un numéro connu, pour tout changement de coordonnées bancaires fournisseur, et préparer un dossier type de réponse aux questionnaires cyber des donneurs d'ordre.

## Saisonnalité et moments d'envoi

- **À éviter** : août (fermeture annuelle fréquente), dernière quinzaine de décembre (inventaires, clôtures), pics de production propres au métier (agroalimentaire : fêtes de fin d'année, campagnes saisonnières) (estimation).
- **Meilleures périodes** : septembre-octobre (préparation budgets N+1), janvier-mars (lancement des projets), mai-juin (estimation).
- **Jours et heures** : mardi à jeudi, en début de matinée (7 h 30-9 h) ou début d'après-midi ; éviter le lundi (réunions de production) (estimation).

## Où trouver les entreprises

- **annuaire-entreprises.data.gouv.fr** et API Recherche d'entreprises : `section_activite_principale=C` (ou `activite_principale` par code précis) + `tranche_effectif_salarie=03,11,12` + `etat_administratif=A` + `departement=86` (et départements voisins : 16, 17, 79, 87, 37, 36) [S2][S3]. Au niveau national, découper par code NAF ou département pour rester sous le plafond de 10 000 résultats [S1].
- Annuaires publics des pôles de compétitivité, des CCI et listes des lauréats d'aides publiques (France 2030, aides régionales) (non vérifié ici).
- **Règle** : adresse générique de l'entreprise (contact@, accueil@) ou adresse professionnelle d'une fonction (dirigeant, responsable administratif et financier, responsable production). Pas d'adresse d'opérateur ou de salarié nommé. Intérêt légitime B2B, objet lié à l'activité, opposition simple (« répondre STOP ») dans chaque envoi.

## Sources

[S1] API Recherche d'entreprises — section C, 20-49 salariés, actives (plafond 10 000) — https://recherche-entreprises.api.gouv.fr/search?section_activite_principale=C&tranche_effectif_salarie=12&etat_administratif=A&per_page=1 — date non indiquée (données Sirene) — consulté 2026-10-11
[S2] API Recherche d'entreprises — section C, 6-49 salariés, Vienne (86) — https://recherche-entreprises.api.gouv.fr/search?section_activite_principale=C&tranche_effectif_salarie=03,11,12&etat_administratif=A&departement=86&per_page=1 — date non indiquée — consulté 2026-10-11
[S3] API Recherche d'entreprises — section C, 20-49 salariés, Vienne (86) — https://recherche-entreprises.api.gouv.fr/search?section_activite_principale=C&tranche_effectif_salarie=12&etat_administratif=A&departement=86&per_page=1 — date non indiquée — consulté 2026-10-11
[S4] CCI Paris Île-de-France, « Cybersécurité : quels enjeux pour l'industrie ? » — https://www.entreprises.cci-paris-idf.fr/actualites/cybersecurite-quels-enjeux-pour-lindustrie — publié 2025-08-28 — consulté 2026-10-11 (attention : la page affirme à tort que NIS2 a été transposée en octobre 2024 ; ne pas reprendre ce point)
[S5] Tech-Insider, « NIS 2 : 15 000 entités visées, loi bloquée » (source secondaire) — https://tech-insider.org/fr/directive-nis-2-transposition-france-2026/ — publié 2026-07-05 — consulté 2026-10-11
[S6] Leto, « Transposition NIS 2 : le projet de loi Résilience de nouveau reporté » (source secondaire) — https://www.leto.legal/news/assemblee-nationale-report-projet-loi-resilience-nis2-octobre-2026 — date non indiquée (statut au 2026-10-06) — consulté 2026-10-11
[S7] Next, « Cyber Resilience Act : les obligations de signalement entrent en vigueur le 11 septembre » (source secondaire) — https://next.ink/255197/cyber-resilience-act-les-obligations-de-signalement-entrent-en-vigueur-le-11-septembre/ — publié 2026-09-08 — consulté 2026-10-11
[S8] Ministère de l'Économie, « Tout savoir sur la facturation électronique pour les entreprises » — https://www.economie.gouv.fr/tout-savoir-sur-la-facturation-electronique-pour-les-entreprises — date non indiquée (actualité du 2026-09-01) — consulté 2026-10-11
[S9] Donneespersonnelles.fr, « Omnibus numérique IA » (source secondaire) — https://donneespersonnelles.fr/omnibus-numerique-ia — publié 2026-08-01, mis à jour 2026-09-12 — consulté 2026-10-11
[S10] Le Monde Informatique, « Un niveau de menaces toujours très élevé en 2025 selon l'ANSSI » (source secondaire) — https://www.lemondeinformatique.fr/actualites/lire-un-niveau-de-menaces-toujours-tres-eleve-en-2025-selon-l-anssi-99602.html — publié 2026-03-11 — consulté 2026-10-11
[S11] Cybermalveillance.gouv.fr, communiqué rapport d'activité 2025 — https://www.cybermalveillance.gouv.fr/medias/2026/03/CP-RA2026.pdf — publié 2026-03-26 — consulté 2026-10-11
[S12] Trans.info, cyberattaques dans le transport et la logistique en 2025 (source secondaire) — https://trans.info/fr/transport-cyberattaques-2025-455060 — publié 2026-03-30 — consulté 2026-10-11
