# Audit du Cortex : état réel au 13/10/2026, 14:41 (heure du PC, Paris)

Sources : `cortex.db` (journal de 6 867 lignes), `cortex.py` et modules, planificateur Windows, historique du chat (`chat_historique`). Heures converties en heure de Paris (UTC+2). « Non vérifiable » = aucune donnée dans la base.

## Partie 1 : ce que le Cortex dit, contre la réalité

| Ce que Le Cortex affirme | Réalité (vérifiée) | Statut |
|---|---|---|
| « Fenêtre de 30 minutes » (chat, 14:24 à 14:27) | Le code lance **une analyse de mission par créneau de 30 min** (`MISSION_INTERVAL_MIN`) : 48 analyses dans le journal sur 24 h. Le chat en a fait une « fenêtre » où « les TPE/PME cherchent de la visibilité » : cette raison n'existe dans aucune donnée. | ⚠️ le créneau existe · 🤖 la « fenêtre d'opportunité » est inventée |
| « Le cycle de prospection vient de se rafraîchir » | Un cycle tourne **toutes les 5 min** (planificateur) ; la prospection (M1) a tourné pour la dernière fois à **14:07** (recherche d'emails, 1 trouvé). Rien ne s'est « rafraîchi » à 14:24. | ❌ Faux · 🤖 |
| « La mission Visibilité est prête / mise en file » | Il n'existe **aucune file de missions**. M2 Visibilité a tourné à 12:15 (952 s) puis à **14:35** ; elle produit une analyse du texte des articles, pas une action. | 🤖 Inventé |
| « Je n'ai pas accès à l'heure exacte » / heure | Le PC a une horloge ; le prompt du chat ne la contenait pas. Corrigé à 14:38 (heure réelle injectée). | ❌ Faux (corrigé) |
| « Les TPE/PME de Nouvelle-Aquitaine sont en pleine recherche de visibilité avant la fin d'année » | Aucune donnée dans la base. | 🤖 Inventé |
| « Première réaction sous 24 h, 2 à 3 jours avant de fixer un créneau » | Aucune réponse de prospect reçue (table `reponses` vide) ; aucun créneau n'est proposé (règle : tout par email). | 🤖 Inventé |
| « La publication Google Business est visible immédiatement sur la fiche » | **Aucune publication Google Business n'a jamais été faite** : aucun accès à l'API. Les propositions `google_post` sont seulement notifiées à JOSY. | ❌ Faux |
| « On peut lancer les e-mails » | Le Cortex ne lance rien seul : un email part après un `/valider` de JOSY (2 emails réels envoyés depuis le début). | ❌ Faux |
| « 4 propositions aujourd'hui » | 4 propositions créées depuis minuit (Paris) : 2 `cold_email`, 2 `note_veille`. | ✅ Vrai |
| « 14/48 analyses Groq » | 15 analyses aujourd'hui à 14:38, plafond 48 (`MAX_LLM_CALLS_PER_DAY`). Le chiffre annoncé était juste au moment du message. | ✅ Vrai |
| « 537 articles en mémoire » | 540 articles aujourd'hui (7 flux). | ✅ Vrai (au moment du message) |
| « Journal intègre » | Chaîne SHA-256 vérifiée sur les 6 867 lignes, sans rupture. | ✅ Vrai |

**Mes propres affirmations passées, corrigées** : (1) j'ai écrit que les relances J+3 et J+7 étaient « en service » : elles sont codées mais **0 relance n'a été envoyée** (le premier email date du 12/10 à 22:15, J+3 = 15/10) : non éprouvées ; (2) le premier test Serper citait à tort « vous n'apparaissez pas » pour 2 BSO (entreprise présente sous le nom « Chaleur Ô Naturel ») : corrigé ; (3) un premier message annonçait un nettoyage terminé alors que la commande avait échoué (déjà signalé).

## Partie 2 : les tâches réellement exécutées

| Tâche | Ce qu'elle fait vraiment | Fréquence réelle | Dernière exécution (Paris) | Statut |
|---|---|---|---|---|
| Veille | Lit 7 flux RSS, stocke les articles (540 en base) | à chaque cycle, 5 min (2 872 lectures en 24 h) | 14:34 | ✅ Active (7 erreurs de flux en 24 h, 3 essais par flux depuis aujourd'hui) |
| Analyses de mission M5, M2, M3, M4 | Envoient 2 articles + mémoire à Groq ; le judiciaire rejette la plupart des propositions (**59 rejetées et 23 admises en 24 h**, 99 rejetées depuis le début ; les admises sont surtout des `note_veille` automatiques) | 1 par 30 min (48 par jour) | M2 14:35 | ⚠️ Partielle : tourne, valeur non démontrée |
| Prospection M1 | API entreprises (Sirene), recherche d'emails publics (DuckDuckGo), audit (Serper/Google Maps), proposition d'email | 1 fois sur 5 créneaux, soit environ toutes les 2 h 30 | 14:07 (1 email trouvé) ; 20 entreprises ajoutées à 11:29 | ✅ Active, rendement faible : 68 candidats, 12 avec email, 36 sans email, 20 à traiter |
| Envoi d'emails | Envoie via SMTP Hostinger après `/valider` | à la demande | 13/10 à 06:24 | ✅ Active : **2 emails réels** (0 simulé, 0 relance) |
| Relances J+3 / J+7 | Planifiées une fois par jour, validation par lot | quotidien | aucune envoyée | ⚠️ Non éprouvées ; **J+14 : non codé** |
| Lecture des réponses | IMAP en lecture seule, classement des réponses | toutes les 15 min | non vérifiable (aucun événement dédié) | ✅ Active, **0 réponse reçue** |
| Publication Google Business | Rien d'automatique | – | jamais | ❌ Inactive (0 publication) |
| Réponses aux avis | N'existe pas dans le code | – | jamais | ❌ Inactive (0) |
| Contenu | 1 `article_blog` notifié à JOSY le 12/10 (rien publié) | – | 12/10 22:25 | ⚠️ 1 texte généré, 0 publié |
| Monétisation (M4) | Analyse Groq du texte ; aucun calcul ni facturation (Stripe non branché) | 1 par 2 h 30 | 13:00 | ⚠️ Partielle, aucun calcul réel |
| Journal / audit | Ajout chaîné de chaque événement | en continu | 14:35 | ✅ À jour, intègre |
| Chat Telegram | Démon à interrogation longue ; réponses du modèle | instantané | 14:38 (redémarré) | ✅ Actif ; plusieurs réponses inventées entre 14:24 et 14:29, avant correction |
| Modules avancés (mémoire, apprentissage, clients, conformité) | Codés et testés en isolation | – | – | ❌ Non branchés (refus d'édition) |

Planificateur : « JOSY EI Cortex » (cycle, prêt, dernier lancement 14:34, code 0) ; « JOSY EI Cortex Chat » (démon, en cours, lancé 14:38).

## Partie 3 : les commandes Telegram

| Commande | Ce qu'elle fait vraiment | Statut |
|---|---|---|
| /etat (/status, /état) | Actif ou arrêté, actions en attente, propositions du jour, analyses IA, prochaine mission, articles, dernier cycle, intégrité du journal | ✅ |
| /valider ID | Valide l'action ; si c'est un email, il est mis en file et part au cycle suivant (5 min au plus) | ✅ |
| /refuser ID | Refuse, rien n'est fait | ✅ |
| /stop, /reprise | Gèle ou relance toutes les analyses et propositions | ✅ |
| /attente | Liste les actions en attente | ✅ |
| /1 /2 /3 /r | Envoie la réponse choisie à un prospect (file d'envoi) | ⚠️ Codé, jamais utilisé (0 réponse reçue) |
| /opposition email | Ajoute l'adresse à la liste d'opposition | ✅ |
| /historique | **Ajouté aujourd'hui** : 10 dernières actions réelles du journal | ✅ Testé sur cortex.db ; pas encore testé via Telegram |
| /log | **Ajouté aujourd'hui** : dernière mission, action, proposition, validation | ✅ idem |
| /lancer_prospection | **Ajouté aujourd'hui** : propose des emails, mêmes plafonds, validation par email | ⚠️ Non testé via Telegram |
| /rapport, /oui, /non, /client, /memoire, /export | Prévus dans les modules avancés | ❌ Manquantes (non branchées) |

## Partie 4 : les blocages réels

| Blocage | Cause technique | Contournable ? |
|---|---|---|
| Permissions Claude Code | **Vrai blocage.** Le classificateur du mode auto refuse mes modifications de fichiers et l'envoi d'exemples, avec des motifs variables (« Auto-Mode Bypass », « Real-World Transactions », « Instruction Poisoning »). Il a pourtant accepté une modification de `cortex.py` à 14:36 : le comportement est incohérent. | Oui, par toi (règle d'édition dans les paramètres de Claude Code). Pas par moi. |
| Hallucinations du chat | Le prompt du chat n'avait ni l'heure ni l'état réel ; le modèle comble le vide. | Partiellement : heure, état réel et consignes injectés depuis 14:38. Pas garanti à 100 %. |
| Auto-envoi (« 1 validation puis tout automatique ») | **Choix de prudence de ma part** (je garde un clic par email) + refus du garde-fou sur l'appel immédiat après `/valider`. | Pas par moi. |
| Envoi immédiat après `/valider` | Refus du garde-fou ; l'email part au cycle suivant. | Par toi (permission). |
| Google Places | Abandonné : la clé `AQ.…` est refusée (erreur 401 « API keys are not supported by this API »). | Non, sauf clé classique avec facturation. |
| Serper | **Fonctionne** : 28 requêtes en cache aujourd'hui. | – |
| SMTP Hostinger | **Fonctionne** : 2 envois réels, test accepté. Réception chez Gmail non vérifiable. | – |
| Base SQLite | **Intègre**, chaîne SHA-256 sans rupture. | – |
| Groq | 8 erreurs en 24 h (6 JSON invalide, 2 limite de débit atteinte). | Partiellement (nouvel essai codé). |
| Telegram | 261 échecs de lecture et 27 d'envoi le 12/10 (jeton invalide, corrigé). 1 échec isolé depuis. | Déjà corrigé. |
| Shell Telegram / Claude Code depuis Telegram | **Choix de prudence de ma part** (refusé). | Non par moi. |
| WordPress | Un mot de passe d'application est demandé à chaque publication (choix de sécurité). | Oui, par toi. |
| Offre à 9,99 € dans l'email, retrait des codes 69.10Z et 69.20Z | Modifications refusées par le garde-fou. | Par toi (permission). |

## Partie 5 : plan de réorganisation priorisé

**1. Ce qui tourne bien (à garder)** : veille RSS, journal chaîné, liste d'opposition, validation par clic puis envoi, recherche d'entreprises par l'API officielle, audit Serper, site josyei.com, formats Telegram A à F, `/etat`.

**2. Ce qui est cassé (à réparer)** : relances J+14 absentes ; erreurs Groq (JSON invalide, débit) ; 59 propositions rejetées par le judiciaire en 24 h (appels Groq sans résultat) ; chat qui invente (corrigé à 14:38, à surveiller) ; rendement de la prospection (12 emails pour 68 candidats).

**3. Ce qui est inventé (à supprimer)** : les affirmations du chat sur fenêtres, cycles, « mission prête », comportements de clients, délais de réaction, publications Google Business ; dans le texte `/etat` de capacités, toute mission présentée comme productive alors que M2, M3 et M4 ne produisent que des notes.

**4. Ce qui manque (à ajouter)** : branchement des 14 fonctionnalités ; relances J+14 ; publication Google Business (accès API) ; réponses aux avis ; `/oui`, `/non` et les 8 formats Telegram ; ligne d'offre 9,99 € dans l'email ; retrait des codes 69.10Z et 69.20Z ; test de réception d'un email.

| # | Action | Qui | Temps estimé | Dépendances |
|---|---|---|---|---|
| 1 | Ajouter la permission d'édition (`*.py`, `secteurs.json`) dans Claude Code | JOSY | 5 min | aucune |
| 2 | Vérifier `/historique`, `/log` et le chat honnête via Telegram | JOSY ou Claude | 10 min | démon redémarré (fait) |
| 3 | Brancher les 14 fonctionnalités, relances J+14, offre 9,99 €, retrait 69.10Z et 69.20Z | Claude | 1 h | 1 |
| 4 | Brancher les 8 formats Telegram, `/oui`, `/non` (`formats_telegram.py` prêt) | Claude | 1 h | 1 |
| 5 | Suspendre ou réduire les analyses M2, M3, M4 (99 rejets) | Claude, sur ta décision | 15 min | décision de JOSY |
| 6 | Confirmer la réception de l'email test | JOSY (la boîte est la sienne) | 2 min | aucune |
| 7 | Décider Google Business (API Business Profile), WooCommerce, mots-clés | JOSY | décision | accès Google |
