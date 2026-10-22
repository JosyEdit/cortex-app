---
id: secteur-notaires
type: secteur
titre: Offices notariaux (NAF 6910Z, notariat)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [secteur, notaires, 6910Z, officier-public, profession-reglementee, lcb-ft, faux-rib, fraude-virement, secret-professionnel, archivage, rgpd, cybersecurite]
---

# Offices notariaux (NAF 6910Z, partie notariat)

## Identité du secteur

- Code NAF : **69.10Z** « Activités juridiques », partagé avec les avocats, commissaires de justice et autres professions juridiques. Il faut donc filtrer sur le nom (« notaire », « notaires associés », « office notarial ») ou la forme juridique.
- Effectifs au **1er janvier 2026** : **17 661 notaires** et **7 479 offices notariaux** (hors offices vacants) [S1].
- Taille moyenne d'une étude : **6,4 salariés** en 2026 (6,5 en 2025), **2 associés** en moyenne en société [S2]. Activité moyenne : **659 actes par étude** en 2026, produits moyens **1 121 586 €** par étude, résultat moyen **313 960 €** [S2] (étude d'un cabinet comptable spécialisé, source secondaire sérieuse).
- Cible JOSY EI : avec une moyenne de 6,4 salariés, une part importante des offices se situe dans la tranche 6-49 (estimation). Dans la Vienne, l'API Recherche d'entreprises compte **37 unités légales actives** en 69.10Z de 6 à 49 salariés, notaires et avocats confondus [S3].
- Structure type 6-49 : 1 à 4 notaires associés, éventuellement des notaires salariés, des clercs rédacteurs, un service formalités, un comptable taxateur, un accueil (estimation).

## Organisation type et outils numériques

- Logiciels de rédaction d'actes : marché décrit comme un « quasi-oligopole » de trois éditeurs [S4] (source secondaire) :
  - **Genapi** (groupe Septeo) : iNot, puis Kivia ; suite comptabilité, paie, immobilier [S4].
  - **Fiducial** : Signature + comptabilité notariale [S4].
  - **Fichorga** : AUTHEN.TIC (actes) et JURIS Web (comptabilité) [S4].
- Acte authentique électronique : plus de **90 %** des actes signés électroniquement et **20 millions** d'actes électroniques déposés au **MICEN** (minutier central électronique) depuis 2008 ; **85 %** des offices équipés en visioconférence ; comparution à distance possible pour les procurations depuis novembre 2020 [S5] (chiffres publiés en 2021).
- Où sont les données : minutier électronique central (MICEN) pour les actes électroniques ; logiciel de rédaction et GED de l'office (souvent hébergés par l'éditeur ou sur serveur local) ; messagerie ; archives papier pour les minutes anciennes (estimation).
- Qui gère l'informatique : l'éditeur (support) et un prestataire local ; rarement un informaticien interne dans une étude de cette taille (estimation). Un notaire associé arbitre.
- Les fonds clients transitent par la Caisse des Dépôts : un RIB de notaire porte le BIC **CDCGFRPPXXX** [S6].

## Besoins IT, IA, RGPD et cybersécurité

- Secret professionnel et données très sensibles : état civil, régimes matrimoniaux, successions, patrimoine, pièces d'identité, coordonnées bancaires.
- Point critique numéro 1 : **les flux de virement**. L'office reçoit les fonds des acquéreurs et paie les vendeurs ; il est la cible directe des fraudes au faux RIB (voir Risques).
- Recommandations publiées pour les offices (source éditeur) : ne jamais agir dans l'urgence, contre-appeler sur le numéro déjà enregistré dans le dossier, validation à plusieurs niveaux pour les virements importants, vérification titulaire du compte / pièce d'identité, traçabilité des vérifications, formation régulière et check-lists [S7].
- Archivage : les minutes sont conservées par l'office puis versées aux archives publiques ; délai de communicabilité de 75 ans pour les minutes et répertoires des notaires (non vérifié dans une source consultée, Code du patrimoine art. L213-2 à vérifier).
- IA : usages probables pour résumer des pièces, préparer des courriers, analyser des titres ; risque de confidentialité si outil grand public (estimation).
- Besoins concrets (estimation) : MFA sur messagerie, sécurisation des postes de rédaction, sauvegarde hors ligne des données locales, procédure écrite anti-faux-RIB connue de tous les clercs, sensibilisation des clients (mail type rappelant le BIC CDC).

## Obligations réglementaires et échéances

- **LCB-FT** : les notaires sont assujettis aux obligations de lutte contre le blanchiment (art. L561-2 du Code monétaire et financier) [S8] (page Légifrance non chargée, assujettissement de principe : numéro exact non vérifié).
- **Facturation électronique** : réception obligatoire depuis le **1er septembre 2026** pour toutes les entreprises ; émission au **1er septembre 2027** pour PME et micro-entreprises [S9]. L'office reçoit des factures de fournisseurs (éditeur, géomètres, diagnostiqueurs) (estimation sur l'impact précis pour les honoraires et émoluments : à vérifier).
- **AI Act** : obligations de transparence depuis le **2 août 2026** pour les chatbots et contenus générés [S10].
- **RGPD** : obligations générales ; notification des violations de données (estimation : pas de texte sectoriel consulté).
- Tarification réglementée et nouvelle carte d'installation : l'Autorité de la concurrence a émis des recommandations pour 2026-2031 [S11] (titre vu, contenu non lu) ; de nouveaux offices peuvent s'installer (déclencheur, voir plus bas).

## Risques et incidents typiques

- **Fraude au faux RIB** : un faux conseiller intercepte une demande de simulation de crédit, fait signer de faux documents et détourne l'apport vers un compte frauduleux avec un RIB falsifié au nom du notaire. Le notariat signale une « forte augmentation » des signalements [S6].
- Un notaire a été condamné après une arnaque au faux RIB de **96 400 €** (titre d'article cité par un éditeur) [S7].
- Tendance nationale 2025 : fraude au virement +170 %, fraude au faux conseiller bancaire +159 %, usurpation de numéro de téléphone +517 % [S12].
- Autres scénarios : usurpation d'identité (faux vendeurs, faux héritiers, faux documents), hameçonnage, cyberattaques [S7] ; rançongiciel sur le serveur local de l'office bloquant les signatures (estimation).

## Budget et décision d'achat

- Décideur : le ou les notaires associés ; pour une SCP ou SELARL, décision collégiale (estimation).
- Capacité financière : résultat moyen par étude de 313 960 € [S2] ; 490 € HT est un montant faible pour l'office (estimation).
- Freins : forte dépendance à l'éditeur, culture de prudence, préférence pour les prestataires recommandés par la Chambre ou le réseau (estimation).
- Cycle : court si un incident vient de toucher une étude voisine ; sinon plusieurs semaines (estimation).

## Déclencheurs et signaux d'achat

- Création ou reprise d'un office (nouvelle carte d'installation) ou arrivée d'un nouvel associé.
- Offres d'emploi de clercs ou de formalistes : croissance de l'activité.
- Hausse du volume d'actes : +4 % d'actes par étude entre 2025 et 2026 [S2].
- Alerte de fraude au RIB dans la presse locale ou communication de la Chambre départementale.
- Changement de logiciel de rédaction (migration iNot vers Kivia, par exemple) [S4].
- Déménagement ou ouverture d'un bureau annexe.

## Objections probables et réponses

- « L'éditeur et la profession gèrent la sécurité. » → Ils sécurisent leurs plateformes. La messagerie de l'office, les postes et la procédure de virement restent sous votre responsabilité.
- « Nous connaissons déjà la fraude au faux RIB. » → Oui ; le diagnostic vérifie que la procédure est écrite, appliquée par chaque clerc et testée.
- « Nos actes sont au MICEN, rien à sauvegarder. » → Les dossiers en cours, la GED, la comptabilité et les mails ne sont pas au MICEN.
- « Pas de prospection par un inconnu. » → Normal. Proposition : un échange de 15 minutes, sans engagement, et un rapport que vous gardez.
- « L'IA n'a pas sa place dans un office. » → Possible ; mais si elle est utilisée sans règle, le secret professionnel est exposé. Une charte d'une page suffit.

## Accroches email

1. « Les notaires de France alertent sur la fraude au faux RIB. Votre procédure de vérification des virements est-elle écrite et suivie par chaque clerc ? »
2. « Vos actes sont au MICEN, mais vos dossiers en cours et vos mails sont-ils sauvegardés hors ligne ? »
3. « Un clerc utilise-t-il une IA générative sur un projet d'acte ? Une règle simple protège le secret de l'office. »

## Angle de l'offre Diagnostic IA, RGPD et sauvegardes

Ce que le diagnostic regarde en priorité :
- Chaîne de virement : qui demande, qui vérifie, par quel canal, quelle trace.
- Messagerie : MFA, règles de transfert suspectes, domaine et protection contre l'usurpation (SPF, DKIM, DMARC).
- Sauvegardes : serveur local, GED, comptabilité ; copie hors ligne testée.
- Usage de l'IA et données envoyées.
- Information des clients : modèle de mail rappelant comment vérifier un RIB de notaire.

Trois actions types :
1. Procédure écrite anti-faux-RIB (contre-appel, double validation au-delà d'un seuil, contrôle du BIC CDC) et mail type aux clients.
2. MFA sur toutes les boîtes, plus configuration DMARC du domaine de l'office.
3. Sauvegarde hors ligne testée tous les trimestres et charte IA d'une page.

## Saisonnalité et moments d'envoi

- Périodes chargées : fin d'année (signatures avant le 31 décembre) et juin-juillet (ventes avant l'été) (estimation, non sourcé).
- Meilleures fenêtres : janvier-février, septembre-octobre (estimation).
- Jours : mardi-jeudi ; éviter le vendredi, souvent consacré aux signatures (estimation).

## Où trouver les entreprises

- annuaire-entreprises.data.gouv.fr et l'API Recherche d'entreprises : `activite_principale=69.10Z`, `tranche_effectif_salarie=03,11,12`, `departement=86`, puis tri manuel sur les noms contenant « notaire » ou « notarial » [S3]. Sur un échantillon de 14 résultats dans la Vienne, seuls quelques noms contenaient « notaire » : il faut croiser avec l'annuaire professionnel.
- Annuaire officiel des notaires sur notaires.fr (non vérifié : URL précise de l'annuaire non consultée).
- Règles : adresse générique de l'office ou adresse professionnelle d'une fonction (notaire associé, responsable de l'office) ; intérêt légitime B2B ; message en lien avec l'activité ; mention « répondre STOP » ; jamais de nom de personne dans la mémoire du Cortex.

## Sources

[S1] Références statistiques Justice, édition 2026, chapitre 3 (ministère de la Justice) — https://www.justice.gouv.fr/sites/default/files/2026-09/RSJ2026%203_1.pdf — publié 2026-09 — consulté 2026-10-11
[S2] L'Observatoire FIDUCIAL 2026 des notaires (source secondaire, cabinet spécialisé) — https://www.fiducial.fr/Notariat/Suivi-comptable-et-financier-de-votre-Office/L-Observatoire-FIDUCIAL-des-notaires/L-observatoire-FIDUCIAL-2026-des-notaires — date non indiquée — consulté 2026-10-11
[S3] API Recherche d'entreprises, 69.10Z, tranches 03,11,12, actives, Vienne — https://recherche-entreprises.api.gouv.fr/search?activite_principale=69.10Z&tranche_effectif_salarie=03,11,12&etat_administratif=A&departement=86&per_page=1 — date non indiquée — consulté 2026-10-11
[S4] Logiciel pour notaires : quel logiciel de gestion d'étude choisir ? (La Fabrique du Net, source secondaire) — https://www.lafabriquedunet.fr/logiciels/gestion/erp/erp-notaire — mis à jour 2026-08-24 — consulté 2026-10-11
[S5] Dépôt du 20 millionième acte authentique électronique (Actu-Juridique) — https://www.actu-juridique.fr/breves/professions/depot-du-20-millionieme-acte-authentique-electronique-la-revolution-digitale-du-notariat-saccelere/ — publié 2021-11-03 — consulté 2026-10-11
[S6] Fraude au virement ou au RIB : les notaires de France appellent à la vigilance (notaires.fr) — https://www.notaires.fr/fr/actualites/fraude-au-virement-ou-au-rib-les-notaires-de-france-appellent-la-vigilance — publié 2024-07-15 — consulté 2026-10-11
[S7] Fraude en office notarial : le guide pour sécuriser votre étude (Fiducial, source secondaire éditeur) — https://www.fiducial.fr/Notariat/Logiciel-Notaire/Actualites-Signature/Fraude-en-office-notarial-le-guide-pratique-pour-securiser-votre-etude — mis à jour 2026-07-30 — consulté 2026-10-11
[S8] Article L561-2 du Code monétaire et financier (Légifrance) — https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000050361172 — date non indiquée — consulté 2026-10-11 (page non chargée)
[S9] Tout savoir sur la facturation électronique pour les entreprises (economie.gouv.fr) — https://www.economie.gouv.fr/tout-savoir-sur-la-facturation-electronique-pour-les-entreprises — date non indiquée — consulté 2026-10-11
[S10] Règlement européen sur l'IA : des mesures concrètes pour informer et protéger les internautes (economie.gouv.fr) — https://www.economie.gouv.fr/actualites/reglement-europeen-sur-lia-des-mesures-concretes-pour-informer-et-proteger-les-internautes — publié 2026-08-25 — consulté 2026-10-11
[S11] Notaires : les nouvelles recommandations de l'Autorité de la concurrence pour 2026-2031 (Actu-Juridique) — https://www.actu-juridique.fr/breves/notaires/notaires-les-nouvelles-recommandations-de-lautorite-de-la-concurrence-pour-2026-2031/ — date non indiquée — consulté 2026-10-11 (titre seul)
[S12] Communiqué de presse, rapport d'activité 2025 de Cybermalveillance.gouv.fr — https://www.cybermalveillance.gouv.fr/medias/2026/03/CP-RA2026.pdf — publié 2026-03-26 — consulté 2026-10-11
