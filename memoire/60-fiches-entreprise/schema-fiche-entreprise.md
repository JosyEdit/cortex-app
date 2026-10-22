---
id: schema-fiche-entreprise
type: schema
titre: Fiche entreprise par niveaux — schéma, score et minimisation des données
mis_a_jour: 2026-10-11
confiance: haute
revoir_avant: 2027-04-11
tags: [schema, fiche-entreprise, crm, rgpd, minimisation, score, M1_Prospection, M3_Relation_Client]
---

# Fiche entreprise par niveaux

La bibliothèque (`10-secteurs` à `50-legal`) décrit des **types** d'entreprises.
La fiche entreprise décrit **une** entreprise prospectée. Elle vit dans
`cortex.db` (table `entreprises`, pas dans les fichiers Markdown) parce qu'elle
change à chaque interaction. Elle se remplit **par niveaux** : on ne collecte le
niveau N+1 que si le niveau N justifie de continuer (minimisation, RGPD art. 5.1.c).
Les règles juridiques détaillées sont dans `legal-prospection-b2b`.

## Niveau 0 — Identité légale (source : SIRENE / API Recherche d'entreprises)

| Champ | Exemple | Source autorisée |
|---|---|---|
| `siren` (clé) | 9 chiffres | API Recherche d'entreprises / SIRENE |
| `denomination` | raison sociale | idem |
| `naf` | 6920Z | idem |
| `tranche_effectif` | code INSEE `03` (6-9), `11` (10-19), `12` (20-49) | idem |
| `departement`, `commune` | 86, Poitiers | idem (siège ou établissement) |
| `date_creation` | AAAA-MM-JJ | idem |
| `categorie_juridique` | SARL, SAS, SELARL… | idem |
| `statut_diffusion` | O / P | idem — **si `P` (diffusion partielle) : ne pas prospecter, ne pas créer de fiche** |
| `est_entrepreneur_individuel` | booléen | idem — si oui, la dénomination est le nom d'une personne : stocker seulement le SIREN et le NAF, jamais le nom dans un contenu |

Règle : **pas de niveau 1 sans niveau 0 complet et `statut_diffusion = O`**.

## Niveau 1 — Taille et contexte

- `secteur_memoire` : identifiant de la fiche secteur correspondante (ex. `secteur-experts-comptables`) → donne au Cortex les besoins, obligations et objections probables.
- `segment` : T1 / T2 / T3 (voir mémoire projet).
- `nb_etablissements`, `effectif_estime` (marquer « estimation » si déduit).
- `dirigeant_fonction` : **la fonction seulement** (« gérant », « associé », « directrice d'établissement »). Le nom du dirigeant figure dans les registres publics mais **n'est pas stocké** : le Cortex n'en a pas besoin pour écrire à la fonction.

## Niveau 2 — Présence en ligne (source : site de l'entreprise, fiche Google, pages publiques)

- `site_web` (URL), `https` (oui/non), `cms_detecte` (WordPress, Wix…), `mentions_legales_presentes`, `politique_confidentialite_presente`, `bandeau_cookies_conforme` (observation), `fiche_google` (oui/non, nombre d'avis, note).
- `email_contact_generique` : adresse **générique** publiée par l'entreprise (`contact@`, `accueil@`, `cabinet@`). Une adresse nominative professionnelle n'est stockée que si elle est publiée par l'entreprise elle-même pour la fonction ciblée, avec `email_origine` (URL de la page) et `email_collecte_le`.
- Chaque observation porte `observe_le` et `url_preuve` (I3).

## Niveau 3 — Signaux (déclencheurs d'achat)

Table `signaux` (n par entreprise) : `type` (recrutement, déménagement, création d'agence, cession BODACC, nouveau logiciel, incident public, obligation sectorielle proche, avis client mentionnant un problème informatique…), `description` courte, `url`, `date`, `poids` (1-3).
Les types de signaux utiles par secteur sont listés dans la section « Déclencheurs et signaux d'achat » de chaque fiche secteur.
Un signal ne contient **jamais** d'information sur une personne (pas de « le gérant est malade », pas de profil LinkedIn personnel).

## Niveau 4 — Relation (alimenté uniquement par les actions validées)

- `statut` : `a_qualifier` → `qualifie` → `contacte` → `relance_1` → `relance_2` → `repondu` → `rdv` → `client` | `perdu` | `opposition`.
- `historique` : liens vers les `action_id` des propositions (table `proposals`) et le journal chaîné (I1).
- `dernier_contact`, `prochaine_relance`, `canal` (email), `reponse_resume` (une phrase, sans donnée personnelle).
- `opposition` : booléen + date. **Une opposition (« STOP », refus, demande d'effacement) est définitive** : statut `opposition`, toutes les données supprimées sauf `siren` + `date_opposition` dans une liste de suppression (`liste_opposition`) pour ne jamais recontacter (pratique CNIL de liste d'opposition ; voir `legal-prospection-b2b`).

## Niveau 5 — Score et prochaine action

Score de 0 à 90, recalculé à chaque mise à jour, **déterministe** (calculé par le code, pas par le modèle) :

| Critère | Points |
|---|---|
| Secteur T1 | 25 · T2 : 15 · autre : 8 |
| Tranche 10-49 | 15 · 6-9 : 10 |
| Département 86 ou limitrophe (16, 17, 36, 37, 79, 87) | 10 · Nouvelle-Aquitaine : 6 · reste France : 3 |
| Signal récent < 30 j (par signal, max 2) | 12 |
| Site sans HTTPS, sans politique de confidentialité ou mentions légales | 8 |
| Adresse de contact générique disponible | 5 |
| Fiche Google avec avis récents (activité) | 3 |
| Malus : déjà contacté < 90 j sans réponse | −20 |
| Bloquant : opposition, diffusion partielle, particulier, entreprise fermée | score = 0, exclusion |

`prochaine_action` : `qualifier` (score < 30), `proposer_email` (≥ 50 et adresse générique), `attendre_signal` (30-49), `relancer` (date atteinte), `ne_rien_faire`. Une `prochaine_action` d'envoi produit **une proposition R2** soumise à JOSY ; elle n'envoie jamais rien seule (I2).

## Minimisation et conservation (règles appliquées par le code)

1. **Pas de données de particuliers** : aucune personne physique en dehors de sa fonction ; aucun téléphone mobile ; aucune adresse personnelle ; aucune donnée sensible (art. 9 RGPD).
2. **Collecte à la source officielle** et preuve de l'origine (`url_preuve`, date) pour pouvoir répondre à « comment avez-vous eu mon adresse ? » (art. 14 RGPD).
3. **Conservation** : 3 ans à compter du dernier contact émanant du prospect, puis suppression automatique (référentiel CNIL gestion commerciale — voir `legal-prospection-b2b` pour la source) ; fiches `a_qualifier` jamais contactées : purge après 12 mois (choix JOSY EI, plus strict).
4. **Droit d'opposition** prioritaire sur tout score.
5. **Pas d'enrichissement par outils de scraping de profils personnels** (LinkedIn personnel, extensions type Kaspr) : risque de sanction CNIL documenté dans `legal-prospection-b2b`.
6. Les fiches entreprise **ne sont jamais envoyées en entier au modèle** : le Cortex transmet seulement les champs utiles à la rédaction (dénomination, secteur, commune, signaux avec URL), jamais l'adresse email (le code l'ajoute au moment de l'envoi validé).

## Schéma SQL (à ajouter à `SCHEMA` dans cortex.py)

```sql
CREATE TABLE IF NOT EXISTS entreprises(
  siren TEXT PRIMARY KEY, denomination TEXT, naf TEXT, tranche_effectif TEXT,
  departement TEXT, commune TEXT, date_creation TEXT, categorie_juridique TEXT,
  statut_diffusion TEXT, est_ei INTEGER DEFAULT 0,
  secteur_memoire TEXT, segment TEXT, dirigeant_fonction TEXT,
  site_web TEXT, https INTEGER, cms TEXT, mentions_legales INTEGER,
  politique_confidentialite INTEGER, fiche_google INTEGER, avis_google INTEGER,
  email_contact TEXT, email_origine TEXT, email_collecte_le TEXT,
  statut TEXT DEFAULT 'a_qualifier', dernier_contact TEXT, prochaine_relance TEXT,
  reponse_resume TEXT, score INTEGER DEFAULT 0, prochaine_action TEXT,
  cree_le TEXT, maj_le TEXT, purge_le TEXT);
CREATE TABLE IF NOT EXISTS signaux(
  id INTEGER PRIMARY KEY AUTOINCREMENT, siren TEXT REFERENCES entreprises(siren),
  type TEXT, description TEXT, url TEXT, date TEXT, poids INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS liste_opposition(
  siren TEXT, email_hash TEXT, date_opposition TEXT, PRIMARY KEY(siren, email_hash));
CREATE INDEX IF NOT EXISTS idx_ent_action ON entreprises(prochaine_action, score);
```

`email_hash` = sha256 de l'adresse en minuscules : permet de bloquer un re-contact sans conserver l'adresse.

## Exemple de fiche (fictive, données inventées pour illustrer le format)

```json
{"siren": "000000000", "denomination": "CABINET EXEMPLE", "naf": "6920Z",
 "tranche_effectif": "11", "departement": "86", "commune": "Poitiers",
 "statut_diffusion": "O", "secteur_memoire": "secteur-experts-comptables", "segment": "T1",
 "dirigeant_fonction": "expert-comptable associé", "site_web": "https://exemple.invalid",
 "https": 1, "politique_confidentialite": 0, "email_contact": "contact@exemple.invalid",
 "email_origine": "https://exemple.invalid/contact", "statut": "qualifie",
 "signaux": [{"type": "recrutement", "description": "offre collaborateur comptable",
              "url": "https://exemple.invalid/emploi", "date": "2026-10-02", "poids": 2}],
 "score": 75, "prochaine_action": "proposer_email"}
```
