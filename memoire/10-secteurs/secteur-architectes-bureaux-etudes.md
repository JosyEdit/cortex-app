---
id: secteur-architectes-bureaux-etudes
type: secteur
titre: Architectes et bureaux d'études techniques, 6-49 salariés (NAF 7111Z, 7112B)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [secteur, architectes, bureaux-etudes, ingenierie, NAF7111Z, NAF7112B, CAO, BIM, sauvegarde, archivage, responsabilite-decennale, ordre-des-architectes, facturation-electronique, M1_Prospection]
---

# Architectes et bureaux d'études techniques (NAF 7111Z, 7112B)

Cible : agences d'architecture et bureaux d'études (structure, fluides, thermique, VRD, économistes) de la tranche d'effectif cible JOSY EI (6-49 personnes). Sujets clés : fichiers lourds CAO/BIM, sauvegarde et archivage sur 10 ans, collaboration avec les autres intervenants, accès à distance, propriété intellectuelle.

## Identité du secteur

- Codes NAF : 71.11Z (activités d'architecture), 71.12B (ingénierie, études techniques).
- Architectes : 29 521 inscrits au tableau de l'Ordre (données 2023), nombre stable depuis une dizaine d'années [S1] [S2]. Statuts : 15 266 associés de sociétés d'architecture (contre 5 322 en 2000) et 11 658 libéraux (contre 17 398) [S2] → la profession se structure en sociétés.
- 61 % des architectes exercent dans les départements des 12 plus grandes métropoles [S2] ; hors métropoles (cas de la Vienne), les agences sont moins nombreuses (estimation).
- Exemple de ratio : au 31/12/2024, le conseil régional de l'Ordre Grand Est comptait 1 773 architectes personnes physiques et 818 sociétés d'architecture [S3].
- Nombre d'agences de 6-49 salariés et nombre de bureaux d'études 71.12B : non sourcés (non vérifié). La plupart des agences ont moins de 5 personnes ; une agence de 6-20 personnes est déjà une agence importante en région (estimation).
- Structure typique : 1 à 3 architectes associés, architectes salariés, dessinateurs-projeteurs, économiste, assistante ; bureau d'études : ingénieurs, techniciens, projeteurs (estimation).

## Organisation type et outils numériques

- Logiciels métier : Archicad (Graphisoft), Revit et AutoCAD (Autodesk), Vectorworks, SketchUp, Allplan ; rendu (Twinmotion, Lumion) ; bureaux d'études : logiciels de calcul thermique et structure (exemples d'éditeurs non vérifiés quant aux parts de marché).
- Fichiers : maquettes BIM et plans de plusieurs centaines de Mo à quelques Go par projet ; serveur NAS au bureau (Synology, QNAP) ou partage cloud ; échanges via plateformes collaboratives et WeTransfer (estimation).
- Postes : stations graphiques puissantes, licences en abonnement liées à un compte éditeur (estimation).
- Qui gère l'informatique : un associé ou un projeteur passionné, avec un revendeur ou intégrateur CAO pour les licences ; le NAS est souvent installé une fois et jamais vérifié (estimation).
- Point faible typique : NAS unique au bureau sans copie hors site, ou copie sur un disque USB branché en permanence (chiffré en même temps que le reste en cas de rançongiciel) (estimation).

## Besoins IT, IA, RGPD et cybersécurité

- Archivage long : l'Ordre recommande de conserver 10 ans les dossiers de chantier (comptes rendus, ordres de service, PV de réception, DOE, DIUO), durée pendant laquelle la responsabilité décennale peut être engagée (art. 1792-4-1 du code civil) [S4] ; 10 ans à compter de la réception pour les contrats, avenants et correspondances avec le maître d'ouvrage (art. 1792-4-3) [S4] ; 10 ans après résiliation pour l'assurance professionnelle [S4]. Les plans et maquettes restent liés au droit moral imprescriptible de l'auteur [S4].
- Conséquence IT : il faut pouvoir **relire** dans 10 ans des fichiers produits par des logiciels qui auront changé de version → formats d'archive ouverts (PDF, IFC) en plus des formats natifs (estimation).
- Sauvegarde : règle 3-2-1 avec copie hors ligne, tests de restauration de gros volumes, temps de restauration compatible avec un rendu de concours (estimation).
- Accès distant et collaboration : VPN ou accès au NAS depuis l'extérieur, souvent ouvert sans double authentification (estimation).
- RGPD : données des maîtres d'ouvrage particuliers (coordonnées, budget, plans de leur logement) ; durées de prospection CNIL non spécifiques (voir fiche legal) ; honoraires : conservation 5 ans (maître d'ouvrage professionnel), 2 ans (particulier) selon l'Ordre [S4].
- IA : rendus et images générés, aide à la rédaction des CCTP et notices, recherche réglementaire ; usage encore limité et regard ambivalent de la profession selon l'Archigraphie [S1].

## Obligations réglementaires et échéances

- Ordre des architectes : formation continue de 20 heures par an, à déclarer avant le 31 mars de l'année suivante ; webinaires et colloques comptent comme formations complémentaires [S3]. Un webinaire « sauvegarde et cybersécurité des agences » peut s'inscrire dans ce cadre (estimation).
- Archivage et responsabilité : durées ci-dessus [S4].
- Facturation électronique : réception obligatoire depuis le 1er septembre 2026 ; émission et e-reporting pour PME et micro au 1er septembre 2027 [S5]. Les honoraires facturés aux promoteurs, entreprises et collectivités passent en facture électronique (estimation).
- AI Act : transparence des contenus générés ou modifiés (images de projet) depuis le 2 août 2026 ; maîtrise de l'IA par les salariés depuis février 2025 [S6].
- NIS2 : transposition non adoptée au 28/09/2026 ; secteurs cités sans mention de l'architecture ou de l'ingénierie [S7] → pas d'obligation directe ; un bureau d'études travaillant pour l'énergie ou les transports pourra recevoir des exigences contractuelles de ses clients (estimation).

## Risques et incidents typiques

- Rançongiciel sur le NAS : perte des projets en cours et des archives si pas de copie hors ligne (estimation ; pas de statistique sectorielle sourcée).
- Statistiques nationales 2025 (entreprises et associations) : piratage de compte 21 %, hameçonnage 16 %, faux ordres de virement 13,5 %, rançongiciels 8,1 %, violations de données 6,6 % des demandes d'assistance [S8].
- Faux RIB sur les appels d'honoraires ou dans la chaîne entreprises / maître d'ouvrage : usurpation d'une adresse de l'agence pendant un chantier (estimation, cohérent avec [S8]).
- Panne de station de travail ou de NAS la veille d'un rendu (estimation).
- Perte d'accès aux licences ou au compte éditeur (compte lié à l'email d'un salarié parti) (estimation).

## Budget et décision d'achat

- Décideur : l'architecte gérant ou les associés ; dans un bureau d'études, le dirigeant ingénieur (estimation).
- Revenus de référence : un architecte libéral de 45-64 ans gagne en moyenne environ 54 000 € par an, moins de 35 ans environ 25 000 € [S2] → marges serrées, chaque dépense est pesée.
- Budget IT : licences CAO/BIM (poste le plus lourd), matériel graphique, NAS ; la sauvegarde et la sécurité sont rarement budgétées à part (estimation, non sourcé).
- Cycle : 2 à 8 semaines ; décision accélérée après une panne, un vol de portable ou un incident chez un confrère (estimation).
- Sensibilité au prix de 490 € HT : moyenne ; à comparer au coût de reconstitution d'un projet perdu ou d'une semaine sans serveur (estimation). Insister sur la demi-journée et le caractère concret du rapport.

## Déclencheurs et signaux d'achat

- Création ou transformation en société d'architecture (nouvelle inscription au tableau, immatriculation).
- Déménagement ou agrandissement de l'agence ; ouverture d'une seconde agence.
- Recrutement de projeteurs BIM ou d'architectes (offres publiques), passage annoncé au BIM.
- Lauréat d'un concours ou d'un marché public important (projets plus lourds, exigences des maîtres d'ouvrage publics).
- Départ en retraite d'un associé ou cession d'agence (question des archives sur 10 ans).
- Incident médiatisé dans le BTP ou chez un confrère dans la région.

## Objections probables et réponses

- « On a un NAS avec RAID, on est sauvegardés. » → Le RAID protège d'une panne de disque, pas d'un rançongiciel ni d'une erreur de suppression ; il faut une copie hors site et hors ligne.
- « Nos fichiers sont dans le cloud de l'éditeur. » → Le diagnostic vérifie ce qui est réellement copié, combien de versions sont conservées et si vous pouvez tout récupérer en quittant l'éditeur.
- « Le RGPD ne nous concerne pas, on fait des plans. » → Vos dossiers contiennent les coordonnées et les plans de logement de particuliers ; et la question principale reste la conservation sur 10 ans [S4].
- « On n'a pas le budget. » → Une demi-journée ; on priorise ce qui protège les projets en cours et les archives décennales.
- « Notre revendeur CAO s'occupe de l'informatique. » → Il gère les licences ; le diagnostic couvre sauvegarde, accès distants, messagerie et RGPD, et lui laisse une liste d'actions.

## Accroches email

1. « L'Ordre recommande dix ans de conservation des dossiers de chantier. Pourriez-vous rouvrir aujourd'hui une maquette de 2016 ? » (19 mots) [S4]
2. « Un RAID ne protège pas d'un rançongiciel. Vos projets ont-ils une copie hors ligne, testée récemment ? » (17 mots)
3. « Factures d'honoraires électroniques en septembre 2027 pour les PME : votre logiciel de facturation est-il prêt ? » (16 mots) [S5]

## Angle de l'offre Diagnostic IA, RGPD et sauvegardes

Ce que le diagnostic regarde en priorité :
- Sauvegarde des projets : NAS, cloud, copies hors site et hors ligne, versions, test de restauration d'un projet complet, durée de restauration.
- Archivage décennal : où sont les dossiers de chantier et les échanges, dans quels formats, lisibles dans 10 ans [S4].
- Accès distants (VPN, NAS exposé), double authentification sur messagerie et comptes éditeurs, comptes des anciens salariés.
- Procédure contre le faux RIB sur les honoraires et les situations de travaux.
- Usage de l'IA (rendus, rédaction) et mention des images générées [S6].

3 actions types recommandées :
1. Ajouter une copie de sauvegarde externe immuable ou hors ligne et planifier un test de restauration trimestriel d'un projet entier.
2. Créer une procédure d'archivage de fin de chantier (export PDF/IFC + natif, classement par date de réception, conservation 10 ans).
3. Fermer l'accès direct au NAS depuis internet, passer par un VPN avec double authentification, et rattacher les licences à des comptes génériques de l'agence.

## Saisonnalité et moments d'envoi

- À éviter : semaines de rendus de concours et de dépôts de permis (variables, visibles sur les sites des agences), août (fermeture), fin décembre (estimation). La déclaration de formation continue avant le 31 mars [S3] est un bon prétexte pour proposer un contenu court sur la sauvegarde en janvier-février (estimation).
- Meilleurs moments : septembre-octobre, janvier-février, mai-juin (estimation).
- Jours et heures : mardi à jeudi, 9 h-10 h ou 14 h-15 h ; éviter le lundi (réunions de chantier fréquentes) (estimation).

## Où trouver les entreprises

- Annuaire des entreprises (annuaire-entreprises.data.gouv.fr) et API Recherche d'entreprises : NAF 71.11Z et 71.12B, tranche d'effectif 03 (6-9), 11 (10-19), 12 (20-49), département ; ignorer la diffusion partielle (voir schema-fiche-entreprise).
- Tableau de l'Ordre des architectes (annuaire public des inscrits, personnes physiques et sociétés) : sert à vérifier l'inscription d'une société ; ne stocker que la société et la fonction, jamais le nom de l'architecte (non vérifié quant aux conditions de réutilisation de l'annuaire → ne pas extraire en masse).
- Sites des agences (références, page contact, mentions légales).
- Règle : adresse générique de l'agence (contact@, agence@) ou adresse professionnelle publiée pour la fonction ; intérêt légitime B2B ; « répondre STOP » dans chaque email ; opposition définitive (voir legal-prospection-b2b).

## Sources

[S1] Conseil national de l'Ordre des architectes — Archigraphie 2024, synthèse — https://prod.architectes.ows.fr/sites/cnoa/files/2024-12/ARCHIGRAPHIE_SYNTHESE-03decembre_corr_0.pdf — date non indiquée (édition 2024, données 2023) — consulté 2026-10-11
[S2] Batiweb — Métier d'architecte : le CNOA livre son baromètre 2024-2026 (source secondaire, chiffres Archigraphie) — https://www.batiweb.com/actualites/architecture/metier-d-architecte-le-cnoa-livre-son-barometre-2024-2026-45652 — publié 2024-12-17 — consulté 2026-10-11
[S3] Conseil régional de l'Ordre des architectes Grand Est — Rapport d'activités 2024 — https://www.architectes.org/sites/cnoa/files/2025-05/Rapport%20activites%202024.pdf — publié 2025-04 — consulté 2026-10-11
[S4] Ordre des architectes — Cahier des professions n° 33 : le délai de conservation des archives — https://architectes.org/sites/cnoa/files/2023-09/field_media_document/484-cdp_33_le_delai_de_conservation_des_archives.pdf — date non indiquée (postérieur à la loi du 17 juin 2008) — consulté 2026-10-11
[S5] Ministère de l'Économie — Tout savoir sur la facturation électronique pour les entreprises — https://www.economie.gouv.fr/tout-savoir-sur-la-facturation-electronique-pour-les-entreprises — date non indiquée (actualité à la une du 2026-09-01) — consulté 2026-10-11
[S6] Blog du Modérateur — IA Act : ce qui change le 2 août 2026 (source secondaire) — https://www.blogdumoderateur.com/ia-act-2-aout-2026/ — publié 2026-07-29 — consulté 2026-10-11
[S7] Legiscope — Transposition NIS2 en France (source secondaire) — https://www.legiscope.com/blog/transposition-nis2-france.html — publié 2026-07-02, mis à jour 2026-09-28 — consulté 2026-10-11
[S8] Le Monde Informatique — Les demandes d'aide face aux cybermenaces explosent en France (rapport 2025 Cybermalveillance.gouv.fr, source secondaire) — https://www.lemondeinformatique.fr/actualites/lire-les-demandes-d-aide-face-aux-cybermenaces-explosent-en-france-99756.html — publié 2026-03-27 — consulté 2026-10-11
