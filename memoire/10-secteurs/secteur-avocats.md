---
id: secteur-avocats
type: secteur
titre: Cabinets d'avocats (NAF 6910Z)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [secteur, avocats, 6910Z, profession-reglementee, secret-professionnel, ia-generative, rancongiciel, faux-rib, carpa, rpva, rgpd, lcb-ft]
---

# Cabinets d'avocats (NAF 6910Z)

## Identité du secteur

- Code NAF : **69.10Z** « Activités juridiques », partagé avec les notaires et commissaires de justice : filtrer sur le nom (« avocats », « SELARL d'avocats », « AARPI ») ou la forme juridique.
- Taille de la profession : **plus de 75 000 avocats en activité** (Tracfin, bilan 2024) [S1].
- Taille des cabinets (enquête CNB/Viavoice, janvier 2026, 6 083 répondants) : 1 avocat 32 %, 2-4 avocats 31 %, 5-10 avocats 18 %, 11-20 avocats 7 %, 21-30 avocats 2 %, plus de 30 avocats 10 % [S2].
- Salariés non avocats par cabinet : aucun 41 %, 1-2 30 %, 3-4 11 %, 5-9 8 %, 10-29 5 %, 30 et plus 5 % [S2]. Âge moyen des avocats : 44 ans [S2].
- Conjoncture 2026 : 35 % des cabinets en développement, 47 % stables, 15 % en recul [S2].
- Cible JOSY EI (6-49 salariés) : surtout les cabinets de 5 à 30 avocats, soit environ un quart des cabinets (estimation d'après [S2]). National 69.10Z, 6-49 salariés : **5 337 unités légales actives**, notaires et avocats confondus ; Vienne : **37** [S3][S4].
- Structure type : 2 à 6 associés, des collaborateurs libéraux, 2 à 8 assistants ou juristes, un responsable administratif dans les plus grands (estimation).

## Organisation type et outils numériques

- Logiciels de gestion de cabinet (source secondaire) : **Secib** (groupe Septeo), décrit comme référence du marché pour les structures moyennes et multi-sites ; **Kleos** (Wolters Kluwer, 59 à 99 € HT par utilisateur et par mois) ; **Jarvis Legal** ; **Lexis PolyOffice** ; **Diapaz** ; LegalProd ; Buroclic [S5].
- Fonctions clés : dossiers et délais, temps passé et facturation, comptabilité séparant fonds CARPA et honoraires, GED, connexion native au **RPVA** (réseau privé virtuel des avocats, échanges avec les juridictions) [S5].
- Le CNB recommande de transmettre les RIB via **e-Partage** [S6].
- Où sont les données : logiciel de gestion (souvent SaaS), messagerie (cible principale), GED ou serveur de fichiers, postes portables en télétravail (estimation).
- Qui gère l'informatique : la plupart des avocats exercent en petite structure, souvent **sans RSSI** [S7] ; en pratique un associé et un prestataire infogérant (estimation). L'ANSSI cite un cas où un prestataire d'infogérance compromis a permis de toucher au moins **sept cabinets** français [S7].

## Besoins IT, IA, RGPD et cybersécurité

- Secret professionnel et confidentialité des correspondances : stratégies contentieuses, informations financières, secrets d'affaires de clients [S6].
- **IA générative** (guide pratique CNB, septembre 2024) : ne jamais communiquer à une IA des données couvertes par le secret (noms de clients, informations confidentielles, éléments de stratégie, fichiers identifiants) ; pseudonymiser ; préférer une IA juridique spécialisée ; vérifier la réutilisation des données par le fournisseur ; vérifier chaque résultat (hallucinations) ; charte informatique ou guide interne et formation [S8]. Le CNB a aussi adopté un guide « La déontologie et l'intelligence artificielle » [S9].
- Recommandations cyber du CNB (août 2026) : sauvegardes hors ligne testées idéalement **tous les 3 mois**, mises à jour, **MFA** avec comptes nominatifs, antivirus et pare-feu, limitation des droits administrateurs ; vérification de tout changement de RIB par un second canal ; adresse professionnelle sécurisée ; sensibilisation du personnel [S6].
- Assurance cyber : l'indemnisation suppose notamment une **plainte dans les 72 heures** et la preuve de conformité RGPD [S6].
- Besoins concrets (estimation) : nom de domaine propre (pas d'adresse webmail grand public), MFA, sauvegarde hors ligne, charte IA, procédure RIB et CARPA, revue des accès des anciens collaborateurs et stagiaires.

## Obligations réglementaires et échéances

- **Déontologie et secret** : obligations de confidentialité issues des règles déontologiques, du RGPD et de la réglementation nationale [S8] (articles précis de la loi de 1971 et du RIN non vérifiés).
- **LCB-FT** : les avocats sont assujettis pour certaines activités (art. L561-2 CMF) ; Tracfin note **seulement 15 déclarations de soupçon** en 2024 pour plus de 75 000 avocats [S1].
- **Facturation électronique** : réception obligatoire depuis le **1er septembre 2026** ; émission au **1er septembre 2027** pour PME et micro-entreprises ; e-reporting aux mêmes dates pour les opérations avec des particuliers [S10]. Un cabinet qui facture des particuliers est concerné par l'e-reporting (estimation).
- **AI Act** : transparence depuis le **2 août 2026** (informer qu'on échange avec une IA, signaler un contenu généré) [S11]. Concerne un cabinet qui met un chatbot sur son site.
- **NIS2** : non concerné en principe à cette taille (estimation).

## Risques et incidents typiques

- ANSSI (juin 2023) : forte hausse des rançongiciels depuis 2017, avec vol puis menace de publication des données ; **une douzaine de cabinets français** compromis, surtout par Lockbit 2.0, chiffre probablement sous-évalué ; attaques via la chaîne d'approvisionnement (infogérant) ; publication de données de dossiers judiciaires sensibles [S7].
- CNB (août 2026) : hameçonnage usurpant un client, une juridiction, une CARPA, un barreau ou le CNB, de plus en plus aidé par l'IA générative ; rançongiciels qui compromettent les délais procéduraux ; **fraude au changement de RIB et aux virements CARPA**, la plupart des victimes étant des avocats **sans adresse liée à un nom de domaine professionnel** [S6].
- Tendance nationale 2025 : hameçonnage et piratage de comptes +45 % chez les professionnels, fraude au virement +170 % [S12].
- Erreur humaine et « menace de l'initié » à l'origine de nombreuses violations [S6].

## Budget et décision d'achat

- Décideur : l'associé gérant ou le comité des associés ; le responsable administratif prescrit dans les cabinets de plus de 20 personnes (estimation).
- Budget : abonnements logiciels par utilisateur (Kleos 59-99 € HT/mois [S5]) ; 490 € HT est inférieur à une à deux heures facturées par un associé (estimation).
- Cycle : rapide après un incident ou une alerte du barreau ; sinon arbitrage entre associés (estimation).
- Sensibilité : faible au prix, forte à la confidentialité ; demander la confidentialité du rapport et un engagement de non-accès aux dossiers (estimation).

## Déclencheurs et signaux d'achat

- Fusion de cabinets, arrivée d'associés, ouverture d'un bureau secondaire.
- Recrutements de collaborateurs ou d'assistants (offres publiques).
- Changement de logiciel de gestion ou migration vers le SaaS (le guide conseille de garder un accès en lecture seule à l'ancien logiciel au moins un exercice [S5]).
- Communication du barreau local ou du CNB sur une campagne d'hameçonnage [S6].
- Lancement d'une offre ou d'un outil d'IA juridique, publication du cabinet sur l'IA.
- Cabinet utilisant une adresse webmail grand public (signal de vulnérabilité au faux RIB selon [S6]).

## Objections probables et réponses

- « Secret professionnel : personne ne regarde nos dossiers. » → Le diagnostic ne lit aucun dossier ; il regarde les accès, sauvegardes et configurations. Accord de confidentialité possible.
- « Notre infogérant s'en occupe. » → L'ANSSI cite des infogérants compromis. Un regard indépendant sur ce qu'il fait réellement est utile.
- « Le CNB a déjà publié des guides. » → Oui ; le diagnostic vérifie leur application concrète dans votre cabinet (MFA, sauvegarde testée, procédure RIB).
- « Nous n'utilisons pas l'IA. » → Vérifions-le : une charte d'une page évite qu'un collaborateur colle une pièce client dans un outil gratuit.
- « Trop petit pour intéresser des pirates. » → Les fraudes au RIB et l'hameçonnage visent d'abord les petites structures sans domaine professionnel.

## Accroches email

1. « Le CNB alerte sur les fraudes au RIB et aux virements CARPA. Vos changements de coordonnées bancaires sont-ils vérifiés par un second canal ? »
2. « Le guide CNB sur l'IA générative interdit d'y verser des données couvertes par le secret. Votre cabinet a-t-il une règle écrite ? »
3. « Le CNB recommande des sauvegardes hors ligne testées tous les trois mois. Quand la vôtre a-t-elle été restaurée pour la dernière fois ? »

## Angle de l'offre Diagnostic IA, RGPD et sauvegardes

Ce que le diagnostic regarde en priorité :
- Messagerie et domaine : nom de domaine propre, MFA, DMARC, règles de transfert.
- Comptes : nominatifs, droits administrateurs limités, départs de collaborateurs traités.
- Sauvegardes : hors ligne, test de restauration, données du logiciel de gestion récupérables.
- Prestataires : accès de l'infogérant et de l'éditeur, clause de réversibilité.
- IA : outils utilisés, données envoyées, charte conforme au guide CNB.

Trois actions types :
1. Migrer vers une messagerie sur nom de domaine du cabinet avec MFA et DMARC.
2. Sauvegarde hors ligne testée tous les trimestres, avec procédure de reprise.
3. Charte IA d'une page alignée sur le guide CNB et procédure RIB/CARPA à double validation.

## Saisonnalité et moments d'envoi

- Moins favorable : août (vacations judiciaires, cabinets au ralenti) et décembre (estimation).
- Meilleures fenêtres : septembre-octobre et janvier-mars (estimation).
- Jours : éviter le lundi (audiences et urgences) ; préférer mardi-jeudi en fin de matinée (estimation).

## Où trouver les entreprises

- annuaire-entreprises.data.gouv.fr / API Recherche d'entreprises : `activite_principale=69.10Z`, `tranche_effectif_salarie=03,11,12`, `departement=86`, `etat_administratif=A`, puis tri sur les noms contenant « avocat » [S3][S4].
- Annuaire national des avocats du CNB et annuaires des barreaux locaux (Poitiers pour la Vienne) (non vérifié : URL non consultées).
- Règles : adresse générique du cabinet (contact@) ou adresse professionnelle d'une fonction (associé gérant, responsable administratif) ; intérêt légitime B2B ; message lié à l'activité ; « répondre STOP » ; aucun nom de personne dans la mémoire du Cortex.

## Sources

[S1] Tracfin, LCB-FT : activité des professions déclarantes, bilan 2024 — https://www.economie.gouv.fr/tracfin/lcb-ft-activite-des-professions-declarantes-bilan-2024 — publié 2025-06-12 — consulté 2026-10-11
[S2] Enquête emploi Avocats 2026, Viavoice pour le CNB — https://cnb.avocat.fr/medias/file/enquete-emploi-avocats-2026---viavoice-pour-le-cnb-6a10296eec05a6.15527835.pdf — publié 2026-02 — consulté 2026-10-11
[S3] API Recherche d'entreprises, 69.10Z, tranches 03,11,12, actives, France — https://recherche-entreprises.api.gouv.fr/search?activite_principale=69.10Z&tranche_effectif_salarie=03,11,12&etat_administratif=A&per_page=1&page=1 — date non indiquée — consulté 2026-10-11
[S4] API Recherche d'entreprises, même requête, Vienne (86) — https://recherche-entreprises.api.gouv.fr/search?activite_principale=69.10Z&tranche_effectif_salarie=03,11,12&etat_administratif=A&departement=86&per_page=1 — date non indiquée — consulté 2026-10-11
[S5] Logiciel pour avocats : quel logiciel de gestion de cabinet choisir ? (La Fabrique du Net, source secondaire) — https://www.lafabriquedunet.fr/logiciels/gestion/erp/erp-avocat — date non indiquée — consulté 2026-10-11
[S6] Menaces cyber : le CNB fait le point (CNB) — https://cnb.avocat.fr/actualite/menaces-cyber-le-cnb-fait-le-point — publié 2026-08-27 — consulté 2026-10-11
[S7] État de la menace informatique contre les cabinets d'avocats, CERTFR-2023-CTI-004 (ANSSI) — https://www.cert.ssi.gouv.fr/uploads/CERTFR-2023-CTI-004.pdf — publié 2023-06-27 — consulté 2026-10-11
[S8] Utilisation des systèmes d'intelligence artificielle générative, guide pratique (CNB) — https://cnb.avocat.fr/medias/cnb-guidepratique-utilisation-systemes-iag-2024-68f7b1d86e4570.98487114.pdf — publié 2024-09 — consulté 2026-10-11
[S9] La déontologie et l'intelligence artificielle (CNB, Commission des règles et usages) — https://cnb.avocat.fr/medias/guide-deontologie-ia-6a4cef5ea1d577.28126431.pdf — date non indiquée — consulté 2026-10-11 (titre seul)
[S10] Tout savoir sur la facturation électronique pour les entreprises (economie.gouv.fr) — https://www.economie.gouv.fr/tout-savoir-sur-la-facturation-electronique-pour-les-entreprises — date non indiquée — consulté 2026-10-11
[S11] Règlement européen sur l'IA : des mesures concrètes pour informer et protéger les internautes (economie.gouv.fr) — https://www.economie.gouv.fr/actualites/reglement-europeen-sur-lia-des-mesures-concretes-pour-informer-et-proteger-les-internautes — publié 2026-08-25 — consulté 2026-10-11
[S12] Communiqué de presse, rapport d'activité 2025 de Cybermalveillance.gouv.fr — https://www.cybermalveillance.gouv.fr/medias/2026/03/CP-RA2026.pdf — publié 2026-03-26 — consulté 2026-10-11
