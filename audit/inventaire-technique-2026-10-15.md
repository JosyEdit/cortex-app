# Inventaire technique du Cortex au 15/10/2026

Source : lecture directe du disque (`C:\Users\JOSY EI\cortex`), de `cortex.db`, de `memoire.db`, du planificateur Windows et de josyei.com. Aucune clé ni aucun mot de passe dans ce document. « Non vérifiable » = je n'ai pas pu le lire ou le mesurer.

## 1. Fichiers et scripts (dossier `cortex\`)

| Fichier | Taille | Modifié | Rôle |
|---|---|---|---|
| `cortex.py` | 85 552 o | 15/10 03:53 | Moteur : cycle, Telegram (commandes, dialogue), judiciaire, missions d'analyse, prospection, journal. Contient aussi les ajouts `/historique`, `/log`, `/lancer_prospection`, `/oui`, `/non`, `/valider_edit` |
| `vente.py` | 25 714 o | 14/10 11:11 | File d'envoi SMTP (plafond 10/jour, opposition, judiciaire), lecture IMAP des réponses, relances J+3/J+7, réponses `/1 /2 /3 /r` |
| `audit.py` | 32 855 o | 15/10 03:53 | Analyse d'un prospect : site, email public, Serper (Google Maps), rédaction de l'email en 5 blocs |
| `chat_daemon.py` | 2 764 o | 13/10 00:37 | Lecteur Telegram permanent (tâche « Chat », aujourd'hui désactivée) |
| `self_edit.py` | 13 313 o | 13/10 18:45 | Modification de code par Groq sous validation (`/valider_edit`), 4 essais enregistrés : 1 simulation réussie, 3 erreurs Groq (plafond de jetons) |
| `publier_page.py` | 7 653 o | 13/10 06:16 | Publication des pages WordPress par l'API REST |
| `email_sender.py` | 2 686 o | 13/10 07:36 | Envoi SMTP Hostinger, **non branché** (a servi à un seul envoi de test) |
| `formats_telegram.py` | 3 758 o | 13/10 13:54 | Formats de messages Telegram : formats 1 (email prêt) et 3 (réponse) branchés, les autres non |
| `honnetete.py` | 4 632 o | 13/10 14:36 | Heure et état réels injectés dans le chat, `/historique`, `/log` (branché) |
| `extensions.py`, `memoire_avancee.py`, `apprentissage.py`, `clients.py`, `conformite.py` | 5 à 11 Ko | 13/10 07:3x | 14 fonctionnalités avancées, testées en isolation, **non branchées** |
| `secteurs.json` | 8 399 o | 14/10 10:30 | 11 secteurs, codes NAF, zone ; 69.10Z et 69.20Z retirés |
| `AGENTS.md`, `README.md` | 9 512 / 5 536 o | 13/10 | Constitution et documentation (sans réseaux sociaux ni vidéo) |
| `prospects.csv` | 11 879 o | 15/10 03:18 | Prospects (export local, historique) |
| `page-*.html`, `page-style.css.html` | 5 à 20 Ko | 12 à 13/10 | Sources des pages du site (accueil à jour ; les pages `diagnostic` et `de-vente` sont anciennes) |
| `AGENTS.proposition-memoire.md`, `requirements.txt`, `.gitignore`, `.github\` (1 fichier) | – | 11 à 12/10 | Reliquats du dépôt d'origine |
| `exports\`, `audit\`, `envois_simules\` | 1 fichier chacun | – | Tableau des 40 fonctionnalités, audits, 1 email simulé |
| `memoire\` | 34 fichiers | 11 à 13/10 | 31 fiches de mémoire, outil d'index, `memoire.db` |
| `cortex_v2\` (hors dossier) | 16 modules | 13 à 14/10 | Découpage abandonné par décision de JOSY, conservé tel quel |

**Synchronisation GitHub : non vérifiable depuis le PC.** Il n'y a ni `git`, ni `gh`, ni dossier `.git` sur le PC. La dernière copie connue du projet (`josy-ei-cortex`, 11/10) contient un `cortex.py` de 33 833 octets, contre 85 552 aujourd'hui : le PC a évolué sans aucune synchronisation.

Fichiers supprimés pendant ce chantier : `video.py`, `split.py`, la sauvegarde `cortex.py.bak.…`, `.env.places`. Clés présentes (noms seulement) : `.env`, `.env.serper`.

## 2. Infrastructure et connexions

| Élément | État vérifié |
|---|---|
| Tâche « JOSY EI Cortex » | Prête, lance `cortex.py` toutes les 5 min, dernier lancement 15/10 04:29, résultat 0 |
| Tâche « JOSY EI Cortex Chat » | **Désactivée** (dernier lancement 15/10 02:47, arrêtée). Pas désactivée par moi |
| Groq | Clé valide. 55 erreurs HTTP au total (JSON invalide, limite de débit), dernière le 15/10 à 04:26 (heure de Paris). Repli 120b, 20b, qwen3.8-27b ajouté le 15/10. Plafond du compte : 8 000 jetons par minute et par modèle |
| Ollama | Installé, modèle `qwen2.5:3b` présent (dernier recours) |
| Serper | Fonctionne (endpoint `places`), 41 requêtes en cache |
| Telegram | Bot actif en envoi (33 échecs d'envoi au total, dernier le 13/10 à 21:46) ; lecture assurée par le cycle puisque le démon chat est arrêté |
| SMTP Hostinger | Fonctionne : 2 emails réels, 1 test accepté par le serveur ; réception chez Gmail non vérifiable |
| IMAP Hostinger | Dernier relevé le 15/10 à 04:26, aucune erreur depuis le 12/10 à 19:05 ; 0 réponse reçue |
| Google Places | Abandonné (erreur 401 : clé non supportée) |
| Google Business Profile, WooCommerce, Stripe, PayPlug, Make | **Non branchés** (aucune clé, aucun appel). Les scénarios du dossier « tarifs » du projet n'ont pas été exécutés : non vérifiable |
| WordPress | Aucun mot de passe d'application conservé ; publication faite à chaque session puis révocation |

## 3. Bases de données

**`cortex.db`** (4,7 Mo, 16 tables) : `journal` 10 841 lignes (du 11/10 00:54 au 15/10 04:30), `articles` 793, `article_missions` 1 520, `proposals` 65, `candidates` 185, `entreprises` 137, `audits` 80, `serper_cache` 41, `chat_historique` 40, `kv` 24, `edits` 4, `envois` 2, `file_envoi` 2, `reponses` 0, `liste_opposition` 0, `signaux` 0.

**Journal chaîné SHA-256** : chaque ligne contient le hash de la précédente ; la chaîne est vérifiée sur les 10 841 lignes, **aucune rupture**. Événements les plus fréquents : `flux_lu` 7 048, `debut_cycle` 1 043, `fin_cycle` 1 039, `telegram_getupdates_echec` 261 (jeton invalide le 12/10, corrigé), `proposition_rejetee` 147, `analyse_llm` 134, `flux_erreur` 127.

**`memoire.db`** (lecture seule, index FTS5) : 31 fiches, 378 sections, 293 sources, tables `fiches`, `sections`, `sources`, `meta` et index de recherche.

## 4. Site et prospection

**josyei.com** (vérifié) : `/` 200 (4 formules Gratuit, Découverte, Starter, Pro ; essai 3 jours sur Pro ; widget date et heure ; pied de page centré), `/mentions-legales/` 200, `/politique-de-confidentialite/` 200 (mention du widget météo), `/diagnostic/` 200 (page de renvoi vers l'accueil). `/tarifs/` et `/boutique/` : 404. Le HTML et le CSS publiés viennent de `page-accueil.html` et `page-style.css.html`.

**Prospection** (lu dans la base) :
- 185 candidats : 43 avec email public, 117 sans email, 25 à traiter ; 80 audits.
- Propositions d'email : 28 `cold_email` enregistrés, dont 12 expirés sans validation, 11 refusés (non soumis), 2 remis à JOSY, 2 mis en file puis envoyés, 1 hors cible.
- **Emails réellement envoyés : 2** (12/10 à 22:15 et 13/10 à 06:24, heure de Paris), 0 relance, 0 réponse, 0 opposition.
- Autres propositions historiques du modèle : `note_veille` 10 exécutées, `article_blog` 9 notifiées, `post_linkedin` 6 (avant la suppression des réseaux sociaux), `newsletter` 5, `devis` 4 (1 encore en attente depuis le 14/10), `webinar_invite` 1, `google_post` 1.
- Test Serper du 13/10 : 5 prospects qualifiés sur 20 ; depuis le 14/10 seuls les arguments Google sont admis.

## 5. Actions bloquées ou inachevées

| Sujet | État | Cause |
|---|---|---|
| Envoi immédiat après `/valider` | Non appliqué | Refus du garde-fou de Claude Code (« Auto-Mode Bypass »). L'email part au cycle suivant |
| Format « ✅ Envoyé à … », `CLIENT CHAUD` | Non branchés | Même refus sur l'édition de `vente.py` |
| 14 fonctionnalités (mémoire, apprentissage, clients, conformité) | Codées, non branchées | Refus d'édition à plusieurs reprises |
| Relances J+14 | Non codées | Refus d'édition |
| Découpage `cortex_v2` et bascule du démon | Abandonnés par JOSY | Bascule bloquée par le garde-fou |
| Réception de l'email test chez Gmail | Non vérifiable | Boîte illisible depuis le PC |
| Google Business (publication, avis) | Non fait | Accès API Business Profile à obtenir |
| Europe | Retirée du périmètre | Décision de JOSY : France uniquement |
| Tâche « Chat » | Désactivée | Origine inconnue ; réactivation à confirmer |
| Proposition `devis` du 14/10 | En attente | Non traitée |
