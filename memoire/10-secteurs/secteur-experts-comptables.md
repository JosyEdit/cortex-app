---
id: secteur-experts-comptables
type: secteur
titre: Cabinets d'expertise comptable (NAF 6920Z)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [secteur, experts-comptables, 6920Z, profession-reglementee, lcb-ft, facturation-electronique, secret-professionnel, rgpd, cybersecurite, ia]
---

# Cabinets d'expertise comptable (NAF 6920Z)

## Identité du secteur

- Code NAF : **69.20Z** « Activités comptables » (cabinets d'expertise comptable, mais aussi commissaires aux comptes et centres de gestion agréés relevant du même code).
- Taille de la profession : près de **21 611 experts-comptables** inscrits en 2022 et **plus de 19 000 sociétés d'expertise comptable** (+29 % depuis 2015) [S1]. 7 entreprises de la branche sur 10 sont des TPE [S1]. Répartition : Île-de-France 30 %, Auvergne-Rhône-Alpes 12 %, PACA 10 % [S1].
- Recrutement : près de **4 000 postes à pourvoir chaque année** (enquête CNOEC citée par l'Ordre de Paris) [S1].
- Cible JOSY EI (6-49 salariés) : l'API Recherche d'entreprises renvoie **6 071 unités légales actives** en 69.20Z dans les tranches d'effectif 6-9, 10-19 et 20-49 salariés, dont **31 dans la Vienne (86)** [S2][S3] (requête du 2026-10-11, ordre de grandeur : la tranche d'effectif INSEE peut dater de plusieurs années).
- En Île-de-France, la taille des cabinets se répartit ainsi : 55,4 % de 1 à 5 salariés, 15,1 % de 5 à 10, 8,9 % de 10 à 20, 4,6 % de plus de 20 [S4].
- Structure type d'un cabinet de 6-49 : 1 à 3 experts-comptables associés, des collaborateurs comptables (tenue, révision), un ou deux gestionnaires de paie, une assistante, parfois un juriste (estimation).

## Organisation type et outils numériques

- Logiciels de production comptable courants (liste d'un comparatif éditeur, source secondaire) : **Pennylane, Sage, EBP, Dext, Akuiteo, Horus, Cegid, Welyb, Inqom, Queoval, Kanta, ACD, Fulll** [S5]. La majorité des tarifs sont sur devis [S5].
- Écosystème typique (estimation) : logiciel de production + paie + GED/portail client (dépôt de pièces, signature électronique de lettres de mission) + suite bureautique Microsoft 365 ou Google Workspace + outil de lettre de mission et LCB-FT.
- Où sont les données : de plus en plus en SaaS chez l'éditeur, mais il reste souvent un serveur local ou un NAS (anciens dossiers, GED, fichiers Excel de révision) (estimation).
- Qui gère l'informatique : rarement un salarié dédié dans un cabinet de 6-49 ; le plus souvent un associé « référent » plus un prestataire informatique local ou l'éditeur (estimation).
- Facturation électronique : **98 %** des experts-comptables répondants ont choisi une plateforme agréée pour leur propre cabinet, **92 %** ont fait signer le mandat de délégation à leurs clients [S6]. Le cabinet devient un nœud d'échange entre ses clients et les plateformes (estimation).

## Besoins IT, IA, RGPD et cybersécurité

- Concentration de données sensibles de centaines de clients : comptes bancaires, bulletins de paie (NIR, salaires, arrêts maladie), liasses fiscales, identité des dirigeants et bénéficiaires effectifs. Une fuite touche tous les clients d'un coup.
- Secret professionnel : il ne peut pas être opposé à Tracfin, mais il s'applique vis-à-vis des tiers [S7]. Toute IA générative « grand public » utilisée sur des pièces clients pose donc une question de confidentialité et de sous-traitance RGPD (estimation).
- Menaces citées pour les cabinets : vol de données clients, piratage de messagerie, rançongiciel, fraude au paiement, usurpation d'identité, attaque sur logiciel métier ou espace partagé [S8] (source secondaire assureur). La RC Pro ne couvre pas systématiquement une cyberattaque [S8].
- Interruption = retards de déclarations fiscales et de paie pour tous les clients [S8].
- Besoins concrets (estimation) : MFA sur messagerie et portails éditeurs ; sauvegarde 3-2-1 avec copie hors ligne des données locales et export des données SaaS ; registre RGPD et contrats de sous-traitance avec éditeurs ; politique d'usage de l'IA (quelles données peuvent aller dans quel outil) ; procédure de vérification des changements de RIB (clients et fournisseurs).
- IA : l'Ordre de Paris note une forte affluence aux réunions sur l'IA en 2024 et la nécessité de « revoir ses tarifs » et de développer des missions à plus forte valeur [S4]. Le CNOEC a publié une synthèse « Parlons data et IA » [S9].

## Obligations réglementaires et échéances

- **Facturation électronique** : depuis le **1er septembre 2026**, toutes les entreprises doivent pouvoir recevoir des factures électroniques ; émission obligatoire au **1er septembre 2026** pour GE et ETI, au **1er septembre 2027** pour PME et micro-entreprises ; e-reporting aux mêmes dates [S10]. Au 31 août 2026, 73 % des clients en tenue étaient opérationnels, 85 % attendus fin septembre [S6]. 32 % des TPE-PME citent le manque d'information comme premier frein [S6].
- **LCB-FT** : les experts-comptables sont assujettis (art. L561-2 12° du Code monétaire et financier) ; l'Ordre est l'autorité de contrôle [S7][S11]. Obligation de déclaration de soupçon à Tracfin [S7].
- **AI Act** : depuis le **2 août 2026**, obligations de transparence (informer l'utilisateur qu'il échange avec une IA, par exemple un chatbot) [S12]. Concerne un cabinet qui déploie un assistant IA client.
- **RGPD** : obligations générales de sécurité et de notification de violation à la CNIL dans certains cas [S8].
- **NIS2** : un cabinet de 6-49 salariés n'est en principe pas entité essentielle ou importante (estimation, à vérifier selon la transposition française).

## Risques et incidents typiques

- Cas public : en avril 2021, le groupe In Extenso (5 000 collaborateurs, 250 bureaux, plus de 100 000 clients) a été paralysé par un rançongiciel ; arrêt complet du système pour limiter la propagation [S13].
- Tendance nationale 2025 : hameçonnage et piratage de comptes en ligne sont les premières menaces pour les professionnels (+45 %) ; la fraude au virement progresse de 170 % et **s'étend à la facturation électronique et à la gestion de la paie** [S14].
- Scénarios typiques (estimation) : boîte mail d'un collaborateur compromise puis faux RIB envoyé aux clients ; fausse facture électronique ou faux mail de « plateforme agréée » ; rançongiciel sur le serveur local la semaine de la liasse ; départ d'un collaborateur avec un export de fichiers clients.

## Budget et décision d'achat

- Décideur : l'associé gérant ou le collège des associés ; le collaborateur « référent informatique » prescrit (estimation).
- Budget IT : surtout des abonnements éditeurs par utilisateur ; un diagnostic à 490 € HT représente moins d'une journée facturée d'un associé (estimation).
- Cycle : court si la demande arrive hors période fiscale et répond à une obligation (facturation électronique, LCB-FT, cyber) ; plusieurs semaines si plusieurs associés (estimation).
- Sensibilité au prix : faible sur 490 € HT ; forte sur l'abonnement mensuel, car les cabinets comparent avec leur prestataire actuel (estimation).
- Attention : les experts-comptables sont aussi prescripteurs. Un cabinet satisfait peut recommander JOSY EI à ses clients TPE (estimation).

## Déclencheurs et signaux d'achat

- Offres d'emploi publiées (collaborateur comptable, gestionnaire de paie) : croissance, nouveaux postes à équiper.
- Création d'un bureau secondaire, fusion ou rachat de cabinet (nouvel associé, migration de logiciels).
- Changement de logiciel de production annoncé, passage au SaaS, choix de plateforme agréée.
- Incident cyber médiatisé dans la profession ou chez un éditeur.
- Lancement d'une offre « facturation électronique » ou « conseil IA » à destination de leurs clients sur leur site.
- Rentrée de septembre 2026 et préparation de l'échéance émission PME du 1er septembre 2027 [S10].

## Objections probables et réponses

- « Notre éditeur gère la sécurité. » → L'éditeur sécurise son service, pas vos postes, vos boîtes mail ni le serveur local. Le diagnostic vérifie la frontière entre les deux.
- « Nous avons déjà un prestataire informatique. » → Le diagnostic est un regard indépendant ; il ne remplace pas le prestataire et peut lui servir de feuille de route.
- « Pas le temps, nous sommes en période fiscale. » → D'accord ; proposer une date après la mi-mai ou en été.
- « L'IA, nous verrons plus tard. » → Vos collaborateurs l'utilisent peut-être déjà. Une règle simple sur les données autorisées protège le secret professionnel.
- « Nous connaissons le RGPD mieux que vous. » → Sur le plan juridique, oui. Le diagnostic regarde la mise en œuvre technique : accès, sauvegardes, journaux, sous-traitants.
- « 490 €, c'est encore un coût. » → Le rapport donne 3 actions priorisées ; vous les réalisez avec qui vous voulez.

## Accroches email

1. « La fraude au virement s'étend désormais à la facturation électronique et à la paie, selon Cybermalveillance.gouv.fr. Vos procédures de changement de RIB ont-elles suivi ? »
2. « Vos collaborateurs utilisent-ils une IA générative sur des pièces clients ? Une règle écrite protège le secret professionnel du cabinet. »
3. « Si votre serveur était chiffré la semaine de la liasse, combien de jours pour repartir ? Je vérifie vos sauvegardes en une demi-journée. »

## Angle de l'offre Diagnostic IA, RGPD et sauvegardes

Ce que le diagnostic regarde en priorité :
- Messageries et portails éditeurs : MFA, comptes partagés, droits des anciens collaborateurs.
- Données hors SaaS : serveur, NAS, postes ; existence d'une copie hors ligne testée ; export régulier des données SaaS.
- Flux de RIB et de paiements : procédure de vérification par second canal.
- Usage de l'IA : outils utilisés, données envoyées, paramètres de réutilisation des données.
- Registre RGPD et contrats avec éditeurs (localisation, sous-traitance).

Trois actions types :
1. Activer la MFA partout et supprimer les comptes partagés ou orphelins.
2. Mettre en place une sauvegarde hors ligne testée tous les trimestres, plus l'export des données SaaS critiques.
3. Rédiger une charte IA d'une page (outils autorisés, données interdites) et une procédure anti-faux-RIB.

## Saisonnalité et moments d'envoi

- À éviter : janvier-février (clôtures, paie de début d'année, déclarations sociales), de mars à mi-mai (liasses fiscales et bilans au 31 décembre) (estimation, calendrier fiscal à revérifier sur impots.gouv.fr).
- Début septembre 2026 : surchargé par la facturation électronique [S6].
- Meilleures fenêtres : fin mai-juillet, puis octobre-novembre (préparation de l'échéance septembre 2027) (estimation).
- Jours : mardi-jeudi, en milieu de matinée (estimation, pas de source sectorielle).

## Où trouver les entreprises

- annuaire-entreprises.data.gouv.fr et l'API Recherche d'entreprises : filtre `activite_principale=69.20Z`, `tranche_effectif_salarie=03,11,12` (codes INSEE 6-9, 10-19, 20-49 salariés, nomenclature non revérifiée ici), `departement=86`, `etat_administratif=A` [S2][S3].
- Annuaire de l'Ordre des experts-comptables (inscription obligatoire au tableau) pour vérifier qu'un cabinet est bien inscrit (non vérifié : URL de l'annuaire à confirmer).
- Règles : écrire uniquement à l'adresse générique du cabinet (contact@, accueil@) ou à l'adresse professionnelle d'une fonction (associé, responsable) ; base légale intérêt légitime B2B ; message en lien avec l'activité ; lien ou mention « répondre STOP » pour s'opposer ; aucun nom de personne dans les fiches du Cortex.

## Sources

[S1] Chiffres-clés et grandes tendances : radiographie de la profession (Le Francilien, OEC Paris) — https://lefrancilien.oec-paris.fr/attractivite/chiffres-cles-et-grandes-tendances-radiographie-de-la-profession/ — publié 2024-12-06 — consulté 2026-10-11
[S2] API Recherche d'entreprises, requête 69.20Z, tranches 03,11,12, actives — https://recherche-entreprises.api.gouv.fr/search?activite_principale=69.20Z&tranche_effectif_salarie=03,11,12&etat_administratif=A&per_page=1 — date non indiquée — consulté 2026-10-11
[S3] API Recherche d'entreprises, même requête, Vienne (86) — https://recherche-entreprises.api.gouv.fr/search?activite_principale=69.20Z&tranche_effectif_salarie=03,11,12&etat_administratif=A&departement=86&per_page=1 — date non indiquée — consulté 2026-10-11
[S4] Ordre des experts-comptables Paris IDF, rapport moral 2024 — https://www.oec-paris.fr/wp-content/uploads/2025/07/rapport-moral-2024.pdf — publié 2025-07 — consulté 2026-10-11
[S5] Quel est le meilleur logiciel pour expert-comptable en 2026 ? (Obat, source secondaire éditeur) — https://www.obat.fr/blog/logiciel-expert-comptable/ — publié 2025-09-15 — consulté 2026-10-11
[S6] Facturation électronique : 73 % des entreprises accompagnées par un expert-comptable opérationnelles au 1er septembre (CNOEC) — https://www.experts-comptables.fr/sic-emissions-evenements-presse/sic-webzine/facturation-electronique-73-des-entreprises — publié 2026-09-03 — consulté 2026-10-11
[S7] Tracfin, Les professions du chiffre — https://www.economie.gouv.fr/tracfin/les-professions-du-chiffre — date non indiquée — consulté 2026-10-11
[S8] Expert-comptable et cyber (Assurup, source secondaire assureur) — https://www.assurup.com/blog/articles/expert-comptable-cyber — publié 2026-06-01 — consulté 2026-10-11
[S9] Parlons data et IA, synthèse des travaux du CNOEC — https://www.experts-comptables.fr/sites/default/files/assets/files/PARLONS%20DATA%20&%20IA%20-%20A4_p%C3%A0p.pdf — date non indiquée — consulté 2026-10-11 (titre vu en résultat de recherche, contenu non lu)
[S10] Tout savoir sur la facturation électronique pour les entreprises (economie.gouv.fr) — https://www.economie.gouv.fr/tout-savoir-sur-la-facturation-electronique-pour-les-entreprises — date non indiquée — consulté 2026-10-11
[S11] Article L561-2 du Code monétaire et financier (Légifrance) — https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000050361172 — date non indiquée — consulté 2026-10-11 (page non chargée, numéro 12° confirmé par [S7])
[S12] Règlement européen sur l'IA : des mesures concrètes pour informer et protéger les internautes (economie.gouv.fr) — https://www.economie.gouv.fr/actualites/reglement-europeen-sur-lia-des-mesures-concretes-pour-informer-et-proteger-les-internautes — publié 2026-08-25 — consulté 2026-10-11
[S13] Le groupe d'experts-comptables In Extenso bloqué par une cyberattaque (Solutions Numériques / AFP) — https://www.solutions-numeriques.com/le-groupe-dexperts-comptables-in-extenso-250-bureaux-en-france-bloque-par-une-cyberattaque-la-comptabilite-de-ses-100-000-clients-est-impactee — publié 2021-04-14 — consulté 2026-10-11
[S14] Communiqué de presse, rapport d'activité 2025 de Cybermalveillance.gouv.fr — https://www.cybermalveillance.gouv.fr/medias/2026/03/CP-RA2026.pdf — publié 2026-03-26 — consulté 2026-10-11
