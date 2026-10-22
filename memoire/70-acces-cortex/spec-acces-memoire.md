---
id: spec-acces-memoire
type: acces
titre: Spécification technique — accès du Cortex à sa mémoire (lecture seule, FTS5, citation obligatoire)
mis_a_jour: 2026-10-11
confiance: haute
revoir_avant: 2027-04-11
tags: [acces, sqlite, fts5, securite, integration, cortex.py, I3, I5, I6, I12]
---

# Accès du Cortex à sa mémoire

Objectif : que chaque proposition du Cortex s'appuie sur la bibliothèque
(secteurs, profils, marché, méthodes, légal) **en citant la fiche et ses sources**,
sans que le Cortex puisse modifier cette mémoire ni approcher un secret.
Le code de référence est `outils/memoire.py` (bibliothèque standard Python, aucune
dépendance ; testé avec SQLite FTS5 de Python 3.11).

## Place dans la séparation des pouvoirs

| Pouvoir | Rôle vis-à-vis de la mémoire |
|---|---|
| **Législatif** (JOSY) | Écrit et valide les fiches Markdown (commit / PR ou dépôt dans le dossier). Seul à pouvoir les changer (I13). |
| **Exécutif** (cortex.py + modèle) | **Lit** l'index via `Memoire` en lecture seule, insère les passages dans le prompt. Peut *proposer* une nouvelle fiche ou une correction via une proposition `amelioration_regle` (R2), jamais l'écrire. |
| **Judiciaire** (classe `Judiciaire`) | Vérifie que les citations `memoire:` existent dans l'index et que les URL citées viennent soit des articles du cycle, soit des sources des passages fournis. Rejette sinon. |

## Arborescence sur le PC

```
C:\Users\JOSY EI\cortex\
  cortex.py, AGENTS.md, cortex.db, .env          (existant)
  memoire\                                       (= copie de cortex-memoire/)
    00-schema\ 10-secteurs\ 20-profils\ 30-marche\ 40-prospection\ 50-legal\
    60-fiches-entreprise\ 70-acces-cortex\
    outils\memoire.py
    memoire.db                                   (généré par build, jamais à la main)
```

`memoire.db` est **séparé de `cortex.db`** : l'index est jetable et reconstructible,
alors que `cortex.db` porte le journal chaîné (I1) et les fiches entreprise.

## Construction de l'index

- Commande : `python memoire\outils\memoire.py build` (≈ 1 s pour 30 fiches).
- Quand : au démarrage de la tâche planifiée si un `.md` est plus récent que `memoire.db`, ou à la main après une mise à jour validée.
- Écriture atomique : l'index est construit dans `memoire.db.tmp` puis renommé ; un Cortex en cours de lecture n'est jamais perturbé.
- Découpage : une ligne FTS par section `##` (≈ 250-400 sections pour la mémoire complète) ; tokeniseur `unicode61 remove_diacritics 2` (recherche insensible aux accents : « securite » trouve « sécurité ») ; classement `bm25` avec poids section 3, titre 2, tags 2, texte 1.
- Tables : `fiches` (métadonnées, sha256), `sections`, `sections_fts` (FTS5), `sources` (ref, URL, dates par fiche), `meta` (date de construction, fichiers rejetés).

## Garde-fous de sécurité (non négociables)

1. **Lecture seule** côté Cortex : connexion `file:...memoire.db?mode=ro` + `PRAGMA query_only=ON`. Toute tentative d'écriture lève une erreur SQLite.
2. **Périmètre de lecture** : l'indexeur ne lit que des `*.md` situés **sous** le dossier `memoire\` (chemins résolus, liens symboliques refusés, dossiers cachés et `outils\` exclus). Il ne lit jamais `..\.env`, `cortex.db`, ni aucun autre fichier.
3. **Noms interdits** : `.env*`, `*secret*`, `*token*`, `*credential*`, `*.key`, `*.pem`, `id_rsa` → ignorés.
4. **Contenu interdit** : une fiche contenant un motif de clé (Groq `gsk_`, OpenAI `sk-`, token Telegram, AWS, Google), un « mot de passe : … », un email nominatif ou un numéro de téléphone est **rejetée en entier** et listée dans `meta.rejets` (et affichée au build). Elle n'entre pas dans l'index.
5. **Aucune variable d'environnement** n'est lue par `memoire.py`. Les secrets restent dans `.env`, chargés uniquement par `cortex.py` pour Telegram/Groq.
6. **Requêtes sûres** : le texte libre est converti en jetons entre guillemets reliés par `OR` (`Memoire.fts_query`) ; aucun opérateur FTS5 ni SQL ne peut être injecté par un article RSS ou une réponse du modèle.
7. **Pas d'accès réseau** dans `memoire.py`.

## Intégration dans cortex.py (à faire par la session PC)

Étapes minimales, dans cet ordre :

1. **Import et ouverture** (après `AGENTS_PATH`) :
   ```python
   MEMOIRE_DB = Path(__file__).resolve().parent / "memoire" / "memoire.db"
   sys.path.insert(0, str(MEMOIRE_DB.parent / "outils"))
   try:
       from memoire import Memoire, build as build_memoire
   except ImportError:
       Memoire = None
   ```
2. **Reconstruction si besoin** au début de `run()` : si un `.md` sous `memoire\` est plus récent que `memoire.db`, appeler `build_memoire(src, MEMOIRE_DB, verbose=False)` et journaliser `self.s.log("SYSTEME", "memoire_reindexee", details={"rejets": len(rejets)})`. Si des fiches sont rejetées, notifier JOSY sur Telegram (sans le contenu).
3. **Récupération dans `analyze()`** : construire la requête à partir des titres + résumés des articles (et, pour M1, du secteur ciblé), puis
   ```python
   mem = Memoire(MEMOIRE_DB) if Memoire and MEMOIRE_DB.exists() else None
   passages = mem.search(requete, k=4) if mem else []
   contexte = mem.contexte_pour_prompt(requete, k=4, max_chars=6000) if mem else ""
   ```
   et ajouter au message utilisateur : `"\n\nMÉMOIRE DU CORTEX (connaissances validées, à citer) :\n" + contexte`.
   Budget : 6 000 caractères ≈ 1 500-2 000 jetons, compatible avec le quota gratuit Groq et avec Ollama qwen2.5:3b (contexte 32 k).
4. **Sources connues du Judiciaire** : fusionner `mem.sources_connues(passages)` dans le dictionnaire passé à `Judiciaire(...)`. Ainsi une URL citée par une fiche (ex. CNIL, Légifrance) est acceptée comme source vérifiable, au même titre qu'un article du cycle.
5. **Règle I5 conservée** : au moins **une** des deux sources d'une proposition doit être un article du cycle (actualité) — sinon le Cortex recyclerait éternellement la même fiche. À coder dans `Judiciaire.review` : `if not any(u in articles_du_cycle for u in urls): rejet("aucune source d'actualité")`.
6. **Champ `memoire`** dans le format de proposition (optionnel, ajouté dans AGENTS.md par JOSY) : `"memoire": ["memoire:secteur-notaires#objections-probables-et-reponses"]`. Le Judiciaire vérifie que chaque citation correspond à une ligne `sections` existante (`fiche_id` + `ancre`) ; une citation inexistante = proposition rejetée (I6).
7. **Journalisation** (I1) : `self.s.log("EXECUTIF", "memoire_consultee", details={"citations": [p["citation"] for p in passages]})` — les citations seulement, pas le texte.
8. **Fiches périmées** : si un passage a `perime = True` (date `revoir_avant` dépassée), le préfixe « FICHE À REVÉRIFIER » est ajouté dans le prompt ; le Cortex doit alors proposer une `note_veille` (R0) de mise à jour plutôt qu'un email fondé sur cette fiche.

## Ajout à AGENTS.md (texte proposé, à valider par JOSY — I13)

> **Mémoire du Cortex.** Le message peut contenir un bloc « MÉMOIRE DU CORTEX ».
> Ce sont des connaissances validées par JOSY sur les secteurs, les dirigeants, le
> marché, les méthodes et le droit. Utilise-les pour choisir la cible, l'angle,
> l'accroche et la réponse aux objections. Cite chaque passage utilisé dans
> `"memoire"` avec son identifiant exact (`memoire:fiche#section`). Un chiffre tiré
> de la mémoire n'est repris dans un email que s'il porte un renvoi `[Sx]` ; ce qui
> est marqué « estimation » ou « non vérifié » ne va jamais dans un contenu destiné
> à un prospect. La mémoire ne remplace pas les sources d'actualité : au moins une
> source par proposition vient de la liste d'articles.

## Mise à jour de la mémoire (boucle M5 contrôlée)

1. Le Cortex détecte un écart (loi modifiée, chiffre plus récent, fiche périmée) → proposition `amelioration_regle` (R2) avec la fiche visée, le passage, la nouvelle donnée et ses 2 sources.
2. JOSY valide sur Telegram → la modification est appliquée **par une session Claude Code ou à la main**, par commit, jamais par le Cortex.
3. Rebuild de l'index ; la date `mis_a_jour` et la ligne `[Sx]` de la fiche sont mises à jour.
4. `python memoire\outils\memoire.py check` doit rester propre (en-têtes complets, renvois résolus, aucun motif interdit).

## Tests d'acceptation (à exécuter sur le PC après intégration)

| # | Test | Attendu |
|---|---|---|
| 1 | `memoire.py build` | « Index : N fiches, M sections », 0 rejet |
| 2 | `memoire.py search "notaire cybersécurité"` | passages de `secteur-notaires` en tête, avec URL |
| 3 | `memoire.py search "securite"` (sans accent) | trouve « sécurité » |
| 4 | Créer `memoire\test.md` contenant `gsk_` + 30 caractères, rebuild | fiche rejetée, signalée |
| 5 | Ouvrir `Memoire` puis exécuter `INSERT` via `m.db` | `sqlite3.OperationalError` (lecture seule) |
| 6 | Requête contenant `" OR 1=1 --` ou `NEAR(` | aucune erreur, résultats normaux |
| 7 | Cycle complet du Cortex | journal `memoire_consultee`, prompt < 6 000 caractères de mémoire |
| 8 | Proposition citant `memoire:inexistant#x` | rejetée par le Judiciaire |
