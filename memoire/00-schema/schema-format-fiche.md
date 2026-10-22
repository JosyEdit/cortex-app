---
id: schema-format-fiche
type: schema
titre: Format obligatoire d'une fiche de la Mémoire du Cortex
mis_a_jour: 2026-10-11
confiance: haute
tags: [schema, format, citation]
---

# Format obligatoire d'une fiche

Chaque fichier `.md` de `cortex-memoire/` est une **fiche** : un sujet, un fichier.
L'indexeur (`outils/memoire.py`) découpe chaque fiche en **sections** (titres `##`)
et indexe chaque section séparément dans SQLite FTS5. Le Cortex cite donc
`id#section` + les sources de la fiche.

## 1. En-tête YAML (obligatoire)

```yaml
---
id: secteur-experts-comptables        # unique, kebab-case, = nom du fichier sans .md
type: secteur                         # schema | secteur | profil | marche | methode | legal | entreprise | acces
titre: Experts-comptables (NAF 6920Z)
mis_a_jour: 2026-10-11                # date de dernière vérification
confiance: moyenne                    # haute | moyenne | basse (voir §3)
revoir_avant: 2027-04-11              # date après laquelle la fiche doit être revérifiée
tags: [T1, profession-reglementee, rgpd, facturation-electronique]
---
```

## 2. Citation des sources (obligatoire pour tout chiffre ou fait daté)

- Chaque chiffre, date, obligation légale, prix ou statistique est suivi d'un
  renvoi `[S1]`, `[S2]`… vers la section `## Sources` en fin de fiche.
- La section `## Sources` liste : `[S1] Titre — URL — publié AAAA-MM-JJ (ou « date non indiquée ») — consulté AAAA-MM-JJ`.
- URL copiées exactement. Aucune URL reconstruite de mémoire.

## 3. Marqueurs épistémiques

| Marqueur | Sens | Usage par le Cortex |
|---|---|---|
| *(aucun)* + `[Sx]` | fait vérifié dans la source citée | utilisable tel quel, avec citation |
| `(estimation)` | déduit ou calculé par JOSY EI / Claude à partir de sources | utilisable en interne, jamais présenté comme un fait à un prospect |
| `(non vérifié)` | information plausible sans source primaire trouvée | ne jamais réutiliser dans un contenu prospect |
| `(à revérifier AAAA-MM)` | fait daté susceptible d'évoluer (loi, calendrier, prix) | revérifier avant usage après la date |

Niveau `confiance` de la fiche :
- **haute** : ≥ 80 % des affirmations sourcées sur sources primaires (Légifrance, CNIL, ANSSI, INSEE, ordres professionnels, service-public, economie.gouv).
- **moyenne** : majorité sourcée, part d'estimations sur budgets ou comportements.
- **basse** : synthèse surtout qualitative ; à compléter.

## 4. Règles de contenu

- Aucune donnée personnelle (nom de particulier, email, téléphone, adresse
  personnelle). Les exemples parlent de **fonctions** (« gérant », « associé »).
- Français, phrases courtes, densité opérationnelle : chaque section doit pouvoir
  servir directement à rédiger un email, qualifier un prospect ou répondre à une objection.
- Une fiche ne contient **jamais** de secret, token, clé API, mot de passe.
