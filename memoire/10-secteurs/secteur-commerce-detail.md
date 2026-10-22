---
id: secteur-commerce-detail
type: secteur
titre: Commerce de détail multi-points et e-commerce, 6-49 salariés (NAF 47)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [secteur, commerce, NAF47, e-commerce, caisse, NF525, facturation-electronique, e-reporting, accessibilite, rgpd, fidelite, dsp2, M1_Prospection]
---

# Commerce de détail multi-points et e-commerce (NAF 47)

Cible : commerçants indépendants ou petits réseaux (2 à 10 points de vente) et e-commerçants de la tranche d'effectif cible JOSY EI (6-49 personnes). Sujets clés : caisse certifiée, données clients et fidélité, boutique en ligne, paiements, facturation électronique.

## Identité du secteur

- Codes NAF : division 47 « Commerce de détail, à l'exception des automobiles et des motocycles » (47.11 à 47.99). Exemples fréquents dans la cible : 47.71Z (habillement), 47.59 (meubles, équipement du foyer), 47.52 (bricolage), 47.64Z (articles de sport), 47.91 (vente à distance / e-commerce, dont 47.91B vente à distance sur catalogue spécialisé).
- Taille en France (INSEE, données 2023 publiées le 18/09/2025) : 462 465 entreprises du commerce de détail, 1,61 million de salariés EQTP, 579 Md€ de CA HT [S1].
- Répartition : 440 441 microentreprises, 21 329 PME hors micro (497 284 salariés EQTP), 695 grandes entreprises et ETI [S1].
- Cœur de cible JOSY EI : les 21 329 PME hors micro (10-249 salariés), dont l'essentiel a 10-49 salariés (estimation), plus la frange haute des micro (6-9 salariés, non chiffrée, non vérifié).
- Structure typique 6-49 salariés : un gérant-propriétaire, 2 à 6 magasins de 3 à 8 vendeurs, un responsable e-commerce ou marketing (souvent un poste unique), comptabilité externalisée chez un expert-comptable (estimation).

## Organisation type et outils numériques

- Caisse : logiciel ou système de caisse certifié (NF525 ou équivalent LNE), souvent en SaaS chez l'éditeur ; exemples d'éditeurs présents sur le marché : Lightspeed, Cashmag, Zelty (restauration), SumUp POS, Square (non vérifié quant aux parts de marché).
- Boutique en ligne : Shopify, WooCommerce (WordPress), PrestaShop, Wix (non vérifié quant aux parts de marché). Connecteurs stock caisse ↔ site souvent bricolés.
- Données : fichier clients et fidélité dans la caisse ou un CRM (Klaviyo, Brevo pour l'emailing), commandes dans le back-office e-commerce, paiements chez le prestataire (Stripe, PayPal, banque), stock dans un ERP léger ou un tableur.
- Qui gère l'informatique : le gérant lui-même ou le responsable e-commerce, avec l'éditeur de caisse pour le support ; pas de DSI ni de RSSI en dessous de 50 salariés (estimation).
- Point faible typique : comptes administrateurs partagés entre vendeurs, mots de passe identiques caisse / site / messagerie, absence de sauvegarde indépendante du site e-commerce (estimation).

## Besoins IT, IA, RGPD et cybersécurité

- RGPD fichier clients : durées de conservation CNIL — clients : durée de la relation puis 3 ans après sa fin pour la prospection ; prospects : 3 ans après collecte ou dernier contact ; comptes inactifs : 2 ans recommandés avec avertissement ; preuves d'opposition : au moins 3 ans [S2]. Le référentiel CNIL couvre aussi les programmes de fidélité [S2].
- Archivage intermédiaire séparé pour les obligations comptables et fiscales [S2] : à prévoir dans l'outil de caisse et le back-office.
- Sécurité des accès : piratage de compte = première menace déclarée par les entreprises à Cybermalveillance en 2025 (21 % des demandes entreprises/associations, +52 %) [S3] ; pour un commerçant cela vise la messagerie, le back-office Shopify/WooCommerce et les comptes marketplaces.
- Fraude au paiement et faux ordres de virement (13,5 % des demandes entreprises) [S3] : fournisseurs étrangers, faux changement de RIB.
- IA utile : fiches produits et descriptions générées, réponses aux avis et au service client, prévision de stock ; risque : données clients collées dans des IA grand public sans cadre (estimation).
- Paiements en ligne : authentification forte des paiements (DSP2) gérée par le prestataire ; le besoin pour le commerçant est surtout de sécuriser ses accès au compte prestataire (non vérifié pour les détails réglementaires, non sourcé ici).

## Obligations réglementaires et échéances

- Caisse certifiée : depuis le 1er septembre 2026, seul un certificat délivré par un organisme accrédité (AFNOR ou LNE) prouve la conformité ; l'attestation individuelle de l'éditeur a été supprimée par la loi de finances 2025 [S4]. Amende : 7 500 € par logiciel non conforme, renouvelable si pas de mise en conformité sous 60 jours [S4]. Les logiciels multifonctions qui enregistrent un paiement sont aussi concernés [S4].
- Facturation électronique : réception obligatoire pour toutes les entreprises depuis le 1er septembre 2026 ; émission et e-reporting pour les PME et micro le 1er septembre 2027 [S5]. Pour les ventes aux particuliers (B2C), la facture reste envoyée par le canal habituel et seules les données de transaction et de paiement sont transmises via la plateforme agréée [S5]. Fréquence et seuils non détaillés sur la page consultée [S5] (à revérifier 2027-03).
- Accessibilité des sites e-commerce : obligatoire depuis le 28 juin 2025 (directive européenne « Accessibilité ») ; exemption des entreprises de moins de 10 salariés ET CA ou bilan ≤ 2 M€ ; sanction : contravention de 5e classe, 7 500 € par infraction, contrôles DGCCRF depuis le 28 juin 2025 [S6]. Un site existant avant juin 2025 ne bénéficie pas de la période transitoire de 2030 [S6]. C'est l'obligation la plus directement liée à la cible 10-49 salariés.
- AI Act : obligations de transparence (chatbot, contenus générés) applicables depuis le 2 août 2026, délai au 2 décembre 2026 pour les systèmes déjà sur le marché ; obligation de maîtrise de l'IA par les salariés depuis février 2025 [S7]. Concerne un e-commerçant qui affiche un chatbot ou des visuels générés.
- NIS2 : transposition française non adoptée définitivement au 28/09/2026 [S8] ; le commerce de détail n'est pas cité parmi les secteurs couverts [S8] → non pertinent pour la cible.

## Risques et incidents typiques

- Piratage de compte (messagerie, back-office, marketplace) : 21 % des demandes d'assistance entreprises/associations en 2025 [S3].
- Hameçonnage (16 %), faux ordres de virement (13,5 %), rançongiciels (8,1 %), violations de données (6,6 %) [S3].
- Volume : 504 810 demandes d'assistance en 2025 sur Cybermalveillance (+20 %) ; demandes des entreprises et associations +73 % [S3].
- Scénarios propres au commerce : caisse SaaS indisponible un samedi (panne réseau ou éditeur) sans mode dégradé ; site e-commerce WordPress non mis à jour piraté (injection de faux formulaire de paiement) ; export du fichier fidélité envoyé à un faux prestataire ; faux RIB d'un fournisseur (estimation, pas de statistique sectorielle sourcée).

## Budget et décision d'achat

- Décideur : le gérant-propriétaire, seul ; le responsable e-commerce prescrit. Expert-comptable consulté pour la facturation électronique (estimation).
- Budget IT habituel : abonnements caisse (par poste), plateforme e-commerce, emailing, maintenance du site ; enveloppe de quelques centaines d'euros par mois pour une structure de 10-20 salariés (estimation, non sourcé).
- Cycle : court (1 à 4 semaines) si un déclencheur existe (contrôle, panne, changement de caisse), sinon reporté après les soldes ou les fêtes (estimation).
- Sensibilité au prix de 490 € HT : acceptable si présenté comme inférieur à une amende de 7 500 € (caisse ou accessibilité) [S4] [S6] ou au coût d'un samedi sans caisse (estimation). Ne jamais présenter l'amende comme une menace mais comme un repère.

## Déclencheurs et signaux d'achat

- Ouverture d'un nouveau magasin ou d'un dépôt (annonce locale, nouvel établissement SIRENE).
- Recrutement d'un responsable e-commerce, d'un webmarketeur ou d'un responsable logistique (offres d'emploi publiques).
- Changement de logiciel de caisse ou migration de site (nouvelle boutique Shopify, refonte annoncée sur les réseaux).
- Lancement d'une carte de fidélité, d'un programme de parrainage ou d'une appli.
- Site sans mentions légales, sans politique de confidentialité, bandeau cookies absent, ou déclaration d'accessibilité absente pour une entreprise de 10 salariés ou plus (observation publique) [S6].
- Avis Google mentionnant « site en panne », « paiement refusé », « jamais reçu ma commande ».
- Approche du 1er septembre 2027 (émission et e-reporting) [S5].

## Objections probables et réponses

- « Mon éditeur de caisse s'occupe de tout. » → Il garantit sa certification, pas vos accès, vos sauvegardes ni votre fichier clients ; le diagnostic vérifie ce qui reste de votre côté.
- « Je suis trop petit pour intéresser les pirates. » → Les attaques sont automatisées ; le piratage de compte est la première demande d'aide des entreprises en 2025 [S3].
- « L'accessibilité, ce n'est pas pour moi. » → Exemption seulement sous 10 salariés et 2 M€ ; au-delà, le site doit être conforme depuis juin 2025 [S6]. Le diagnostic dit en une page si vous êtes concerné.
- « Pas le temps avant les soldes / Noël. » → D'accord : une demi-journée en janvier-février ou en mai-juin, hors pics.
- « La facturation électronique, mon comptable gère. » → Il gère la comptabilité ; le choix de la plateforme et le lien avec la caisse et le site restent à décider chez vous avant septembre 2027 [S5].
- « C'est cher pour un simple rapport. » → Rapport court, 3 actions classées par ordre, sans engagement ensuite.

## Accroches email

1. « Depuis le 1er septembre, seule une caisse certifiée par un organisme accrédité est acceptée. Vos autres outils suivent-ils ? » (20 mots) [S4]
2. « Votre boutique en ligne doit être accessible depuis juin 2025 au-delà de 10 salariés. Savez-vous où vous en êtes ? » (19 mots) [S6]
3. « Piratage de compte : première demande d'aide des entreprises en 2025. Vos accès caisse, site et messagerie sont-ils séparés ? » (20 mots) [S3]

## Angle de l'offre Diagnostic IA, RGPD et sauvegardes

Ce que le diagnostic regarde en priorité :
- Certificat de la caisse (organisme accrédité), comptes utilisateurs de la caisse et du back-office, double authentification.
- Sauvegarde indépendante du site e-commerce et export régulier du fichier clients.
- Durées de conservation du fichier fidélité et de la base prospects [S2], bandeau cookies, politique de confidentialité.
- Statut accessibilité (concerné ou exempté) [S6] et préparation à la facturation électronique 2027 [S5].
- Usage d'IA par l'équipe (fiches produits, réponses clients) et données copiées dedans.

3 actions types recommandées :
1. Activer la double authentification sur messagerie, back-office e-commerce, compte de paiement et marketplace ; supprimer les comptes partagés.
2. Mettre en place une sauvegarde automatique externe du site et un export mensuel chiffré du fichier clients, avec test de restauration.
3. Purger le fichier fidélité selon les durées CNIL et rédiger une règle d'usage de l'IA (pas de données clients dans les outils gratuits).

## Saisonnalité et moments d'envoi

- À éviter : soldes d'hiver (janvier) et d'été (fin juin-juillet), Black Friday et période des fêtes (mi-novembre à fin décembre), rentrée scolaire pour les commerces concernés (fin août-début septembre) (estimation).
- Meilleurs moments : février-mars, mai-début juin, octobre (avant le pic de fin d'année) (estimation).
- Jours et heures : mardi à jeudi, avant l'ouverture (8 h-9 h 30) ; éviter le samedi et le lundi (fermeture fréquente, gestion des commandes du week-end) (estimation).

## Où trouver les entreprises

- Annuaire des entreprises (annuaire-entreprises.data.gouv.fr) et API Recherche d'entreprises : filtrer par activité principale (NAF 47.xx), département et tranche d'effectif salarié (codes INSEE 03 = 6-9, 11 = 10-19, 12 = 20-49) ; ignorer les fiches en diffusion partielle (voir schema-fiche-entreprise).
- Nombre d'établissements d'une même entreprise : indique un commerce multi-points.
- Sites e-commerce : mentions légales du site (SIREN), page « contact ».
- Fédérations et unions commerciales locales (associations de commerçants, CCI) pour repérer les enseignes indépendantes (non vérifié quant à la publication de listes).
- Règle : écrire uniquement à l'adresse générique publiée par l'entreprise (contact@, boutique@) ou à l'adresse professionnelle publiée pour la fonction ; intérêt légitime B2B ; chaque email contient un moyen simple de refuser (« répondre STOP ») ; toute opposition est définitive (voir legal-prospection-b2b).

## Sources

[S1] INSEE — Caractéristiques du commerce de détail selon la taille des entreprises, données annuelles 2023 — https://www.insee.fr/fr/statistiques/2015242 — publié 2025-09-18 — consulté 2026-10-11
[S2] CNIL — Questions-réponses sur les référentiels relatifs à la gestion des activités commerciales et des impayés — https://www.cnil.fr/fr/questions-reponses-sur-les-referentiels-relatifs-la-gestion-des-activites-commerciales-et-des — publié 2022-01-28 — consulté 2026-10-11
[S3] Le Monde Informatique — Les demandes d'aide face aux cybermenaces explosent en France (rapport d'activité 2025 Cybermalveillance.gouv.fr, source secondaire) — https://www.lemondeinformatique.fr/actualites/lire-les-demandes-d-aide-face-aux-cybermenaces-explosent-en-france-99756.html — publié 2026-03-27 — consulté 2026-10-11
[S4] Fiducial — Logiciels et systèmes de caisse : règles de conformité (source secondaire, cite BOI-TVA-DECLA-30-10-30 et actualités BOFiP) — https://www.fiducial.fr/Articles-et-dossiers/Suppression-de-l-attestation-de-conformite-des-logiciels-et-systemes-de-caisse — mis à jour 2025-12-17 — consulté 2026-10-11
[S5] Ministère de l'Économie — Tout savoir sur la facturation électronique pour les entreprises — https://www.economie.gouv.fr/tout-savoir-sur-la-facturation-electronique-pour-les-entreprises — date non indiquée (actualité à la une du 2026-09-01) — consulté 2026-10-11
[S6] DGCCRF — Professionnels : vos produits et services doivent être conformes à la directive « Accessibilité » — https://www.economie.gouv.fr/dgccrf/les-fiches-pratiques/professionnels-vos-produits-et-services-doivent-etre-conformes-la-directive-accessibilite — date non indiquée — consulté 2026-10-11
[S7] Blog du Modérateur — IA Act : ce qui change le 2 août 2026 (source secondaire) — https://www.blogdumoderateur.com/ia-act-2-aout-2026/ — publié 2026-07-29 — consulté 2026-10-11
[S8] Legiscope — Transposition NIS2 en France (source secondaire) — https://www.legiscope.com/blog/transposition-nis2-france.html — publié 2026-07-02, mis à jour 2026-09-28 — consulté 2026-10-11
