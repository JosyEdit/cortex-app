---
id: methode-sources-donnees-entreprises
type: methode
titre: Sources légales et gratuites pour constituer la liste de prospects (API Recherche d'entreprises, Sirene, BODACC, annuaires)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [methode, sources, prospects, sirene, api-recherche-entreprises, bodacc, annuaire-entreprises, orias, google-maps, pages-jaunes, signaux, non-diffusion]
---

# Sources de données pour constituer la liste de prospects

Principe JOSY EI : liste construite **à la main ou par API publique**, entreprise par entreprise, à partir de sources officielles. Aucun fichier acheté, aucun scraping de plateforme dont les CGU l'interdisent. La donnée d'entreprise (SIREN, NAF, effectif, adresse du siège) n'est pas une donnée personnelle ; la donnée d'une personne (dirigeant, entrepreneur individuel, adresse nominative) l'est (voir `legal-prospection-b2b`).

## API Recherche d'entreprises (recherche-entreprises.api.gouv.fr)

**Ce qu'elle donne** : recherche d'entreprises françaises par texte (nom, adresse, dirigeants, élus) ou par zone géographique ; pour chaque résultat dénomination, SIREN, SIRET, code NAF [S1]. Champs secondaires disponibles : `complements`, `dirigeants`, `finances`, `matching_etablissements`, `siege`, `score`, `tva` [S2].

**Paramètres utiles de `/search`** [S2] :
- `activite_principale` : code NAF/APE de l'unité légale, liste séparée par des virgules acceptée.
- `tranche_effectif_salarie` : tranche d'effectif, liste acceptée.
- `departement` (2 ou 3 chiffres) et `code_postal` : filtrent les **établissements**.
- `etat_administratif` : `A` active, `C` cessée.
- `categorie_entreprise` : PME, ETI, GE.
- `nature_juridique` : catégorie juridique.
- `per_page` : **25 maximum** (10 par défaut) ; `page`.
- `minimal=true` + `include=...` : réponse allégée avec seulement les champs choisis.

**Limites de débit** : **7 requêtes/seconde par IP** et 30/seconde par ASN, non garanties ; au-delà, HTTP 429 avec en-tête `Retry-After` [S2]. L'administration peut baisser la limite en cas de surcharge [S1].

**Exemple de requête Cortex** (cible : TPE/PME actives de 6 à 49 salariés dans la Vienne, NAF à adapter) :
`https://recherche-entreprises.api.gouv.fr/search?departement=86&tranche_effectif_salarie=03,11,12&etat_administratif=A&per_page=25&page=1&minimal=true&include=siege,complements`

**Limites légales** : les entreprises **non diffusibles** ne sont **pas** accessibles via l'API [S1][S2]. Ne pas demander le champ `dirigeants` sauf besoin réel : JOSY EI écrit à une **fonction**, pas à une personne (règle I4).

## Codes de tranche d'effectif Sirene

| Code | Effectif | Cible JOSY EI |
|---|---|---|
| NN | Unité non employeuse | Non |
| 00 | 0 salarié au 31/12 (en a eu dans l'année) | Non |
| 01 | 1 ou 2 | Non |
| 02 | 3 à 5 | Non (hors cible) |
| **03** | **6 à 9** | **Oui** |
| **11** | **10 à 19** | **Oui** |
| **12** | **20 à 49** | **Oui** |
| 21 | 50 à 99 | Non (hors cible) |

Source : [S3]. L'effectif est mesuré au 31 décembre d'une année, en général **n-2** ; lire avec la date de validité (dernière mise à jour) [S3]. Conséquence : une entreprise peut avoir grandi ou réduit depuis ; vérifier sur son site si l'écart compte (estimation).

## Base Sirene INSEE et statut de diffusion

- Base Sirene en open data sous **Licence Ouverte 2.0** [S4].
- Obligation du réutilisateur : respecter **le statut de diffusion le plus récent** de chaque personne physique. Selon l'art. A123-96 du code de commerce, une personne peut demander que ses informations ne soient pas utilisées par des tiers à des fins de **prospection**, notamment commerciale [S4].
- Les **entrepreneurs individuels** (y compris micro-entrepreneurs) et les représentants légaux de sociétés peuvent demander la non-diffusion. Seuls restent publics la **commune**, la **dénomination** et, le cas échéant, nom commercial et enseigne [S5].
- Depuis le **25 août 2025**, les dirigeants et associés de SNC et de sociétés civiles peuvent demander l'occultation de leur adresse personnelle au RCS [S5].
- Règle JOSY EI : une entreprise au statut de diffusion **partiel** (non-diffusion demandée) est **exclue** de la prospection, même si une adresse email est trouvée ailleurs (estimation prudente fondée sur [S4]).
- Le traitement des données Sirene reste soumis à la loi Informatique et Libertés [S4].

## Annuaire des entreprises (annuaire-entreprises.data.gouv.fr)

- Service public gratuit (Service Public / DINUM) pour consulter les informations légales des entreprises, associations et organismes publics [S6].
- Recherche par SIREN/SIRET, nom de dirigeant, dénomination ou localisation (commune, département, région) [S6].
- Données : forme juridique, date de clôture, chiffre d'affaires, justificatif d'immatriculation au RNE [S6].
- Applique la non-diffusion : pour les personnes concernées, seules commune, dénomination et enseigne restent visibles [S6].
- **Usage JOSY EI** : vérifier une fiche entreprise avant envoi (activité, établissements, effectif, finances publiées). Bon signal : **nouvel établissement**, **croissance du CA** publié (estimation).
- Limite : consultation manuelle ; pour l'automatisation, passer par l'API Recherche d'entreprises (même famille de services, estimation).

## BODACC : signaux de création, cession, difficultés

- Annonces légales du code de commerce (greffes, tribunaux, mandataires) [S7] :
  - **BODACC A** : ventes et cessions, immatriculations, créations, prévention des difficultés, procédures collectives ;
  - **BODACC B** : modifications générales, radiations ;
  - **BODACC C** : dépôts des comptes annuels.
- Parution **cinq fois par semaine** ; **Licence Ouverte** ; API sur la plateforme OpenDataSoft de la DILA (jeu « annonces-commerciales ») et fichiers via HTTPS/FTPS [S7].
- La mise à disposition ne dispense pas le réutilisateur de respecter la loi Informatique et Libertés [S7].

**Signaux exploitables** (estimation) :
- **Cession / reprise** : nouveau dirigeant qui remet à plat l'informatique → angle sauvegardes et RGPD.
- **Création** d'une société de 6+ salariés (rare) ou **transfert de siège** → nouvelle installation.
- **Modification d'activité** → nouveaux outils.
- À **exclure** : procédures collectives (redressement, liquidation) et radiations. Ne jamais citer une difficulté dans un email.

## Annuaires ordinaux et ORIAS (professions réglementées)

- **ORIAS** : registre officiel des intermédiaires en assurance, banque et finance, sous tutelle de la DG Trésor ; inscription obligatoire ; **72 666 intermédiaires** et **123 083 inscriptions** au 31 décembre 2025 ; recherche publique d'un intermédiaire [S8].
- Conditions de réutilisation ORIAS : renvoyées aux mentions légales et aux CGU du web service, non lues (non vérifié).
- **Annuaires ordinaux** (experts-comptables, avocats, notaires, professions de santé) : utiles pour vérifier qu'un cabinet existe et son activité (non vérifié : conditions de réutilisation propres à chaque ordre).
- Usage JOSY EI : **vérification** et qualification uniquement, pas d'extraction en masse. Les coordonnées nominatives des professionnels inscrits sont des données personnelles (règles de [S9]).

## Pages Jaunes : CGU et limites

- Annuaire privé. Les CGU n'ont pas pu être lues (non vérifié). Une base de données structurée est en principe protégée par le **droit sui generis du producteur** (art. L342-1 CPI) contre l'extraction substantielle (non vérifié sur Légifrance).
- La CNIL rappelle que si les CGU d'un site interdisent l'aspiration à des fins commerciales, elle n'est pas permise, et que l'acceptation de CGU ne vaut pas consentement [S9].
- Règle JOSY EI : **consultation ponctuelle** pour trouver le site web d'une entreprise ; **jamais d'extraction** automatisée.

## Google Maps : CGU et risques

- Conditions Google Maps Platform (dernière modification 26 août 2026), section **3.2.3(a) « No Scraping »** : interdiction d'exporter, extraire ou aspirer le contenu Google Maps pour un usage hors des services ; notamment interdiction de **copier et enregistrer des noms d'entreprises, adresses ou avis** [S10].
- 3.2.3(b) : pas de mise en cache hors exceptions ; 3.2.3(c)(vii) : pas d'entraînement d'IA sur ce contenu ; 5.2(d) : suspension possible en cas de violation [S10].
- Les extensions « Google Maps scraper » sont donc contraires aux conditions (estimation fondée sur [S10]) et exposent à la jurisprudence KASPR côté RGPD (voir `legal-prospection-b2b`).
- Règle JOSY EI : Google Maps sert à **regarder** une fiche (avis, horaires, site web) pour qualifier un prospect déjà identifié via Sirene, **sans copier** les données dans la base.

## Sites web des entreprises : page contact et mentions légales

- Source la plus sûre pour l'**adresse email** : celle que l'entreprise publie elle-même pour être contactée.
- Privilégier l'adresse **générique** (contact@, info@) : la CNIL considère qu'elle concerne la personne morale [S9][S11].
- **Mentions légales** : dénomination, SIREN, siège, directeur de publication ; utiles pour **vérifier la correspondance** avec Sirene (estimation).
- Signaux exploitables sur le site (estimation) : chatbot (AI Act art. 50), formulaire de devis, offre d'emploi, absence de politique de confidentialité, site non sécurisé (HTTP), page « actualités » (nouvelle activité).
- Limites : enregistrer **l'URL source et la date** de collecte pour l'information art. 14 et le droit d'accès [S9] ; ne pas collecter d'adresses nominatives de salariés sans lien avec l'offre ; ne pas déduire d'adresse (prenom.nom@) non publiée (estimation).

## Sources interdites ou à risque (rappel)

| Source | Statut JOSY EI | Raison |
|---|---|---|
| Fichiers achetés / courtiers | Interdit | Sanction SOLOCAL 900 000 € (voir `legal-prospection-b2b`) |
| Extension d'extraction LinkedIn | Interdit | Sanction KASPR 240 000 € (voir `legal-prospection-b2b`) |
| Scraping Google Maps | Interdit | CGU 3.2.3(a) [S10] |
| Extraction Pages Jaunes | Interdit | CGU et droit des bases de données (non vérifié) |
| Entreprises en non-diffusion | Exclues | Art. A123-96 code de commerce [S4] |
| API Recherche d'entreprises, BODACC, Sirene | Autorisé | Licence Ouverte, données officielles [S2][S4][S7] |
| Site de l'entreprise (contact@) | Autorisé | Adresse publiée pour être contactée [S11] |

## Flux de constitution d'une liste (procédure Cortex)

1. **Requête API** Recherche d'entreprises : département, NAF, tranches 03/11/12, `etat_administratif=A` [S2].
2. **Filtre** : exclure non-diffusibles (déjà exclues par l'API [S2]), procédures collectives (BODACC), entreprises déjà prospectées ou sur la liste repoussoir.
3. **Signal** : chercher un signal récent (BODACC, site web, nouvel établissement).
4. **Adresse** : relever l'adresse générique sur le site ; noter URL + date.
5. **Fiche** : SIREN, dénomination, NAF, tranche, commune, signal, source, adresse, fonction ciblée. Aucun nom de personne.
6. **Brouillon** d'email (voir `methode-email-froid`) → validation JOSY (R2).
7. **Conservation** : purge 3 ans après dernier contact émanant du prospect.

## Sources

[S1] data.gouv.fr — API Recherche d'entreprises (fiche dataservice) — https://www.data.gouv.fr/dataservices/api-recherche-dentreprises — date non indiquée — consulté 2026-10-11
[S2] API Recherche d'entreprises — Spécification OpenAPI — https://recherche-entreprises.api.gouv.fr/openapi.json — date non indiquée — consulté 2026-10-11
[S3] INSEE (sirene.fr) — Variable tranche d'effectif salarié — https://www.sirene.fr/sirene/public/variable/tefen — date non indiquée — consulté 2026-10-11
[S4] data.gouv.fr — Base Sirene des entreprises et de leurs établissements (SIREN, SIRET), informations — https://www.data.gouv.fr/datasets/base-sirene-v3-2/informations — mis à jour 2021-05-11 — consulté 2026-10-11
[S5] Service-Public.fr — Demande de non-diffusion de données publiques (répertoire Sirene, RNE, Annuaire des entreprises) — https://www.service-public.gouv.fr/particuliers/vosdroits/R60912?lang=fr — date non indiquée — consulté 2026-10-11
[S6] justice.fr — Annuaire des entreprises : rechercher toutes les informations sur une entreprise — https://www.justice.fr/fiche/annuaire-entreprises-rechercher-toutes-informations-entreprise — mis à jour 2025-10-10 — consulté 2026-10-11
[S7] data.gouv.fr — BODACC — https://www.data.gouv.fr/datasets/bodacc — mis à jour 2026-10-10 — consulté 2026-10-11
[S8] ORIAS — Registre unique des intermédiaires en assurance, banque et finance (accueil) — https://www.orias.fr/ — date non indiquée — consulté 2026-10-11
[S9] CNIL — La réutilisation des données publiquement accessibles en ligne à des fins de démarchage commercial — https://www.cnil.fr/fr/la-reutilisation-des-donnees-publiquement-accessibles-en-ligne-des-fins-de-demarchage-commercial — publié 2020-04-30 — consulté 2026-10-11
[S10] Google — Google Maps Platform Terms of Service — https://cloud.google.com/maps-platform/terms?hl=fr — modifié 2026-08-26 — consulté 2026-10-11
[S11] CNIL — La prospection commerciale par courrier électronique, SMS-MMS et automate d'appel — https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique — publié 2026-06-10 — consulté 2026-10-11
