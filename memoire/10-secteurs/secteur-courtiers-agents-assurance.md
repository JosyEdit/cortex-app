---
id: secteur-courtiers-agents-assurance
type: secteur
titre: Courtiers, agents généraux d'assurance et courtiers en crédit IOBSP (NAF 6622Z)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [secteur, assurance, courtier, agent-general, iobsp, 6622Z, orias, dda, acpr, lcb-ft, dora, demarchage-telephonique, rgpd, donnees-de-sante, faux-rib]
---

# Courtiers, agents généraux d'assurance et IOBSP

## Identité du secteur

- Code NAF : **66.22Z** « Activités des agents et courtiers d'assurances ». Les courtiers en crédit (IOBSP) sont souvent classés ailleurs, probablement en 66.19B (non vérifié).
- Registre ORIAS, fin 2025 : environ **27 500 courtiers (COA)** (+2 % sur un an), **12 035 agents généraux (AGA)** (+1,3 %), près de **31 000 mandataires d'intermédiaires d'assurance (MIA)** (+4,2 %) ; nombre total d'intermédiaires en hausse de **3,85 %** [S1] (presse financière rapportant le rapport annuel ORIAS 2025). Les chiffres IOBSP ne sont pas donnés dans cette source.
- Cible JOSY EI : **1 997 unités légales actives** en 66.22Z de 6 à 49 salariés en France, **17 dans la Vienne** [S2][S3] (requêtes du 2026-10-11, ordre de grandeur). Un même intermédiaire peut cumuler plusieurs catégories ORIAS.
- Structure type 6-49 (estimation) : agence générale avec 1 à 3 agents associés et des collaborateurs (production, sinistres, back-office) ; cabinet de courtage avec un dirigeant, des chargés de clientèle particuliers et entreprises, des gestionnaires sinistres et santé collective.

## Organisation type et outils numériques

- Deux familles d'outils : un **CRM commercial** (prospection, devis, relances) et un **logiciel de gestion de courtage** (portefeuille, commissions, conformité DDA, GED, connexions aux extranets des compagnies) [S4] (source secondaire).
- Éditeurs cités : **OGGO Data** (CRM et multi-tarificateurs, 69 à 149 € HT/mois), **CourtiGo** (29,90 à 199,90 €/mois), **Custy**, **Lya Courtage** (orienté santé et prévoyance), **Modulr** et **SKY CRM** (grossistes et réseaux) ; CRM généralistes **Eudonet** ou **HubSpot** pour la seule prospection [S4].
- Agents généraux : outils et extranet fournis par la compagnie mandante (estimation).
- Où sont les données : extranets compagnies (multiples identifiants), logiciel de courtage SaaS, messagerie, tableurs de suivi des commissions, GED avec preuves du devoir de conseil (estimation).
- Qui gère l'informatique : le dirigeant ou l'agent ; la compagnie pour les agents généraux ; un prestataire local pour le reste (estimation).

## Besoins IT, IA, RGPD et cybersécurité

- Données sensibles : santé (prévoyance, emprunteur, santé collective), revenus, sinistres, RIB, pièces d'identité (estimation : les données de santé sont des données sensibles au sens du RGPD, art. 9).
- Conformité DDA : recueil des besoins, **preuve écrite du conseil**, archivage horodaté ; un CRM généraliste ne gère ni les commissions ni la preuve du devoir de conseil [S4].
- Multiplicité des accès : un courtier se connecte à de nombreux extranets ; risque de mots de passe réutilisés ou partagés entre collaborateurs (estimation).
- IA : comparaison de garanties, rédaction de comptes rendus de conseil, réponses clients ; attention aux données de santé envoyées à des outils non maîtrisés (estimation). Un chatbot doit indiquer qu'il est une IA depuis le **2 août 2026** [S5].
- Besoins concrets (estimation) : coffre-fort de mots de passe d'équipe et MFA, archivage horodaté et sauvegarde des preuves DDA, procédure de changement de RIB des assurés, preuves de consentement pour la prospection téléphonique.

## Obligations réglementaires et échéances

- **Démarchage téléphonique** : depuis le **11 août 2026**, prospection téléphonique des consommateurs interdite sans **consentement préalable** (loi n° 2025-594 du 30 juin 2025, décret n° 2026-662 du 23 juillet 2026) ; consentement nominatif (professionnel identifié), finalité précise, durée maximale **1 an** sans tacite reconduction ; preuve à conserver **3 ans** ; amendes jusqu'à **75 000 €** (personne physique) et **375 000 €** (personne morale) ; contrats issus d'une prospection illicite nuls ; les modèles de leads « ouverts » ne sont plus conformes [S6]. Sujet majeur pour les cabinets qui achetaient des leads.
- **DORA** (règlement UE 2022/2554) : les intermédiaires d'assurance sont dans le champ, **sauf** s'ils sont des microentreprises ou des PME [S7]. Un cabinet de 6-49 salariés est donc en principe exclu (estimation selon la définition de l'article 3). Les compagnies mandantes, elles, y sont soumises et peuvent répercuter des exigences sur leurs agents (estimation).
- **Formation continue DDA** : obligation d'actualiser régulièrement les compétences, applicable depuis le **23 février 2019** [S8] ; durée de 15 heures par an (non vérifié dans la source consultée).
- **ORIAS** : immatriculation obligatoire et conditions de capacité professionnelle (Code des assurances, art. R512-8 à R512-13-1) [S9].
- **LCB-FT** : les intermédiaires d'assurance sont assujettis, contrôlés par l'ACPR (art. L561-2 CMF) [S10] (numéro exact non vérifié).
- **Facturation électronique** : réception depuis le **1er septembre 2026**, émission et e-reporting au **1er septembre 2027** pour PME et micro-entreprises [S11]. Les opérations d'assurance sont largement exonérées de TVA (estimation : impact à vérifier pour les commissions).

## Risques et incidents typiques

- Tendance 2025 : hameçonnage et piratage de comptes +45 % chez les professionnels ; fraude au virement +170 % ; fraude au faux conseiller +159 % ; usurpation de numéro de téléphone +517 % [S12].
- Scénarios propres au secteur (estimation) : identifiant d'extranet compagnie volé puis souscriptions ou rachats frauduleux ; faux RIB pour le versement d'une indemnité de sinistre ; usurpation du nom du cabinet dans de fausses offres d'assurance ; fuite de questionnaires de santé.
- Le secteur assurance se mobilise sur la cyber-résilience : accord ANSSI-ACPR-Banque de France en 2026 [S13] (titre seul).

## Budget et décision d'achat

- Décideur : le dirigeant du cabinet ou l'agent général ; pour un agent, la compagnie peut imposer ou proposer des outils (estimation).
- Budget IT : abonnements logiciels de l'ordre de 30 à 100 €/mois pour un outil standard, 200 à 500 €/mois pour une offre premium [S4].
- Sensibilité au prix : moyenne ; profession commerciale habituée au retour sur investissement ; 490 € HT est acceptable si le lien avec une obligation (démarchage, DDA) est clair (estimation).
- Cycle : court, décisions rapides chez les indépendants (estimation).

## Déclencheurs et signaux d'achat

- Fin du démarchage téléphonique sans consentement le 11 août 2026 : refonte des fichiers, des formulaires et des preuves [S6].
- Changement de logiciel de courtage ou passage à un outil conforme DDA [S4].
- Rachat de portefeuille, fusion d'agences générales, ouverture d'une agence.
- Recrutement de chargés de clientèle ou de gestionnaires.
- Lancement d'une activité santé collective ou prévoyance (données de santé).
- Incident de fraude médiatisé visant des assurés.

## Objections probables et réponses

- « La compagnie s'occupe de l'informatique. » → Elle sécurise ses extranets ; vos postes, mots de passe partagés et boîtes mail restent votre responsabilité.
- « DORA ne nous concerne pas. » → C'est exact pour une PME ; le diagnostic vise plutôt la preuve DDA, le consentement au démarchage et les sauvegardes.
- « Nous avons déjà un CRM. » → Un CRM généraliste ne prouve pas le devoir de conseil ; le diagnostic vérifie où se trouve cette preuve et si elle est sauvegardée.
- « Nous ne faisons plus de téléphone. » → Alors vérifions que vos formulaires web collectent un consentement conforme pour les futurs rappels.
- « Encore un audit. » → Une demi-journée, 3 actions priorisées, aucun abonnement obligatoire.

## Accroches email

1. « Depuis le 11 août 2026, le démarchage téléphonique exige un consentement préalable prouvé trois ans. Vos formulaires et fichiers sont-ils à jour ? »
2. « Combien d'identifiants d'extranets compagnies sont partagés dans votre cabinet ? Un seul compte volé suffit pour une fraude. »
3. « Vos preuves de devoir de conseil DDA sont-elles sauvegardées hors de votre logiciel ? »

## Angle de l'offre Diagnostic IA, RGPD et sauvegardes

Ce que le diagnostic regarde en priorité :
- Gestion des accès aux extranets : coffre-fort, MFA, comptes nominatifs, départs de collaborateurs.
- Preuves DDA et consentements : où elles sont stockées, horodatage, sauvegarde, export.
- Données de santé : qui y accède, par quel canal elles arrivent, durée de conservation.
- Flux de paiement : procédure de changement de RIB des assurés et des fournisseurs.
- Usage de l'IA et données envoyées.

Trois actions types :
1. Déployer un coffre-fort de mots de passe d'équipe avec MFA et supprimer les identifiants partagés.
2. Mettre en conformité les formulaires et le registre de consentements au démarchage (preuve 3 ans, durée 1 an).
3. Sauvegarde hors ligne des preuves DDA et charte IA interdisant l'envoi de données de santé dans des outils non validés.

## Saisonnalité et moments d'envoi

- Fin d'année chargée : échéances principales et renouvellements au 1er janvier, notamment en santé collective (estimation).
- Meilleures fenêtres : février-avril et mi-septembre à octobre (estimation).
- Jours : mardi-jeudi ; éviter le lundi matin, consacré aux sinistres du week-end (estimation).

## Où trouver les entreprises

- annuaire-entreprises.data.gouv.fr / API Recherche d'entreprises : `activite_principale=66.22Z`, `tranche_effectif_salarie=03,11,12`, `departement=86`, `etat_administratif=A` [S2][S3].
- Registre public **ORIAS** (orias.fr) pour vérifier la catégorie (COA, AGA, MIA, IOBSP) d'un intermédiaire [S1] (fonctions de recherche du registre non consultées ici).
- Règles : adresse générique du cabinet ou de l'agence, ou adresse professionnelle d'une fonction (dirigeant, agent général) ; intérêt légitime B2B ; message lié à l'activité ; « répondre STOP » ; aucun nom de personne dans la mémoire du Cortex. Attention : beaucoup d'agents généraux exercent en nom propre ; leur adresse peut être nominative et doit alors être traitée comme une adresse professionnelle, avec un droit d'opposition simple.

## Sources

[S1] Intermédiaires en assurance : 2025, l'année d'une légère expansion (Option Finance, source secondaire sur le rapport ORIAS 2025) — https://www.optionfinance.fr/info-financiere-en-continu/d/2026-09-08-intermediaires-en-assurance-2025-lannee-dune-legere-expansion.html — publié 2026-09-08 — consulté 2026-10-11
[S2] API Recherche d'entreprises, 66.22Z, tranches 03,11,12, actives, France — https://recherche-entreprises.api.gouv.fr/search?activite_principale=66.22Z&tranche_effectif_salarie=03,11,12&etat_administratif=A&per_page=1 — date non indiquée — consulté 2026-10-11
[S3] API Recherche d'entreprises, 66.22Z, Vienne (86) — https://recherche-entreprises.api.gouv.fr/search?activite_principale=66.22Z&tranche_effectif_salarie=03,11,12&etat_administratif=A&departement=86&per_page=1 — date non indiquée — consulté 2026-10-11
[S4] Logiciels CRM pour l'assurance et le courtage (La Fabrique du Net, source secondaire) — https://www.lafabriquedunet.fr/logiciels/productivite/crm/crm-assurance — date non indiquée — consulté 2026-10-11
[S5] Règlement européen sur l'IA : des mesures concrètes pour informer et protéger les internautes (economie.gouv.fr) — https://www.economie.gouv.fr/actualites/reglement-europeen-sur-lia-des-mesures-concretes-pour-informer-et-proteger-les-internautes — publié 2026-08-25 — consulté 2026-10-11
[S6] Réforme du démarchage téléphonique : mise en pratique depuis le 11 août 2026 (Actu-Juridique) — https://www.actu-juridique.fr/affaires/droit-economique/reforme-du-demarchage-telephonique-mise-en-pratique-depuis-le-11-aout-2026/ — publié 2026-09-17 — consulté 2026-10-11
[S7] Règlement DORA (UE) 2022/2554, article 2 (Springlex, reproduction du JO L 333 du 27.12.2022) — https://www.springlex.eu/fr/packages/dora/dora-regulation/article-2/ — publié 2022-12-27 (texte) — consulté 2026-10-11
[S8] Mise en œuvre de la formation continue en application de la Directive sur la distribution d'assurances (ACPR) — https://acpr.banque-france.fr/mise-en-oeuvre-de-la-formation-continue-en-application-de-directive-sur-la-distribution-dassurances — mis à jour 2026-09-24 — consulté 2026-10-11
[S9] Code des assurances, conditions de capacité professionnelle, art. R512-8 à R512-13-1 (Légifrance) — https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006073984/LEGISCTA000006188316/ — date non indiquée — consulté 2026-10-11 (titre seul)
[S10] Article L561-2 du Code monétaire et financier (Légifrance) — https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000050361172 — date non indiquée — consulté 2026-10-11 (page non chargée)
[S11] Tout savoir sur la facturation électronique pour les entreprises (economie.gouv.fr) — https://www.economie.gouv.fr/tout-savoir-sur-la-facturation-electronique-pour-les-entreprises — date non indiquée — consulté 2026-10-11
[S12] Communiqué de presse, rapport d'activité 2025 de Cybermalveillance.gouv.fr — https://www.cybermalveillance.gouv.fr/medias/2026/03/CP-RA2026.pdf — publié 2026-03-26 — consulté 2026-10-11
[S13] Cyber-résilience : l'accord ANSSI-ACPR-Banque de France et le DORA (Échanges Assurances) — https://www.echangesassurances.org/actualites/cyber-resilience-anssi-acpr-banque-france-2026 — date non indiquée — consulté 2026-10-11 (titre seul)
