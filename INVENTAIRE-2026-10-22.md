# Le Cortex — inventaire et bilan au 22/10/2026

Aucun secret dans ce document : les clés restent dans `.env`, qui n'est jamais affiché.

## 1. Arborescence

### `C:\Users\JOSY EI\cortex\` (le programme)

**Cœur**
- `cortex.py` : le moteur. Cycles toutes les 5 min, prospection, journal chaîné SHA-256, base `cortex.db`.
- `fondateur.py` : les commandes du fondateur (journée, validation, décisions).
- `regles_absolues.py`, `honnetete.py`, `conformite.py` : les garde-fous (règles d'or, honnêteté, contrôle du journal).
- `mode_execution.py` : le Mode Manuel ou Automatique (relances seulement, 30 par jour).
- `veille_service.py` : la surveillance, qui relance l'interface et le lecteur Telegram.

**Interface web** (http://127.0.0.1:8765)
- `app.py` : Tableau de bord, Copilote, Mon Agent, Profil, espace client, Super Admin.
- `connexion.py` : connexion par email et mot de passe (bcrypt), sessions.
- `comptes.py` : comptes clients (SIREN), onboarding, profil, mémoire par client.
- `fiabilite.py` *(nouveau)* : limite de débit, disjoncteur Groq, anti double-clic, plans.
- `diagnostic.py` *(nouveau)* : onboarding proactif (diagnostic, site vitrine, fiche Google).
- `evolution.py` *(nouveau)* : auto-analyse, propositions à valider, auto-réparation, délégation.
- `copilote.py`, `executeur_taches.py`, `routeur_agents.py` : actions du Copilote (validées avant exécution) et les 7 agents.
- `superpouvoirs.py` : documentation (RAG local FTS5), recherche approfondie, rapports PDF, mémoire long terme.
- `analyse_entreprise.py`, `analyse_multi_outils.py`, `audit.py`, `osint_tools.py` : analyses de sociétés, de sites, de la concurrence et OSINT.
- `pwa/` : application installable (icônes, service worker, Chart.js local).
- `login.html` : la page de connexion.

**Ventes et emails**
- `vente.py`, `cycle_emails.py`, `email_sender.py` : envoi SMTP Hostinger, relances et lecture des réponses.

**Telegram**
- `routage_telegram.py`, `chat_daemon.py` : bot et lecteur instantané. Le lecteur est à l'arrêt, voir le bilan.

**Documents**
- `AUTONOMIE.md` *(nouveau)* : démarrer, arrêter et modifier sans IA.
- `DEPLOIEMENT.md` *(nouveau)* : Render en 3 étapes, avec les limites et le RGPD.
- `README.md`, `AGENTS.md`, `GUIDE-ANALYSES.md`, `OSINT_README.md`.
- `requirements.txt` (complet, nettoyé) et `requirements-serveur.txt` *(nouveau, version légère)*.

**Données**
- `cortex.db` : 11 Mo, 38 tables.
- `audit.db`, `prospects.csv`, `memoire/`, `exports/`.

**Lancement**
- `cortex-app.bat`, `arret-interface.bat`, `install_osint.bat`.

**Journaux**
- `cortex-app.log`, `surveillance.log`.

**Sauvegardes**
- `sauvegardes/` : 43 éléments, 110 Mo. La plus récente est `avant-chantier-final-20261022-143607`, avec tous les `.py` et `cortex.db.bak`.

### `C:\Users\JOSY EI\Cortex-Workspace\` (ce que le Cortex produit)

- `uploads/` (5 fichiers, 5,5 Mo) : fichiers glissés dans le Copilote.
- `rapports/` (1 PDF) : rapports d'analyse.
- `medias/` : images générées ou retouchées.
- `avatars/` : ta photo de profil.
- `documentation/u1/` : documents indexés pour le RAG (vide pour l'instant).
- `clients/` : sites vitrines et fiches Google des clients (vide ; les fichiers du test ont été retirés).
- `tests/`, `.sauvegardes/`, `.verif/` : fichiers techniques.
- `auto-reparation/` : créé à la première erreur bloquante (scripts de contournement).

## 2. Logiciels

**Python 3.12.10** : 128 paquets installés, dont les principaux :
- requests 2.34.2, feedparser 6.0.14, python-dotenv 1.2.4, ddgs 9.16.0 ;
- bcrypt 5.0.0, beautifulsoup4 4.15.0, playwright 1.64.0 ;
- pypdf 6.21.2, pdfplumber 0.11.10, python-docx 1.2.0, openpyxl 3.1.5 ;
- pandas 2.3.3, duckdb 2.0.0, fpdf2 2.8.9, icalendar 7.3.0, yfinance 1.7.0 ;
- black 26.10.1, pylint 4.1.3 ;
- pillow 12.3.0, moviepy 1.0.3, rembg 2.0.85 (onnxruntime 1.31.0) ;
- python-Wappalyzer 0.3.1, sherlock-project 0.16.2.

**Outils du PC**
- Tailscale 1.104.2 : connecté, relais HTTP actif sur le réseau privé, HTTPS pas encore activé sur le compte.
- Node.js 24.20.0, npm 11.19.0, Git 2.55.0, VS Code 1.143.0.
- Google Chrome, utilisé par Playwright (channel chrome, sans navigateur téléchargé).
- Disque C : 166 Go libres.

**Services externes**
- Groq : seul fournisseur d'IA (gpt-oss-120b, gpt-oss-20b, qwen3).
- Recherche web DuckDuckGo (Serper si une clé est présente).
- Registre public des entreprises (API de l'État).
- SMTP et IMAP Hostinger.

## 3. État de `cortex.db`

**Comptes**
- 2 utilisateurs : 1 fondateur (plan Business) et 1 client test (plan Découverte).
- 1 compte entreprise client.

**Prospection**
- 751 entreprises en base.
- 87 propositions et 4 envois.
- 0 réponse reçue.

**Journal**
- 29 558 lignes, du 11/10 au 22/10, chaîne intègre.
- L'utilisateur à l'origine de chaque action est maintenant enregistré.

**Contenus**
- 1 465 articles de veille.
- 62 messages de chat, 21 faits mémorisés, 11 actions Copilote, 6 boutons personnalisés.

**Mode d'exécution**
- Manuel. Il a été remis en Manuel depuis l'application ce matin à 10 h 30, après une période en Automatique.

**Sauvegardes**
- Dans `cortex\sauvegardes\`, avant chaque chantier.

## 4. Bilan

### Prêt (testé)
- Interface complète :
  - Tableau de bord, Copilote, Mon Agent, Profil, PWA installable ;
  - connexion sécurisée ;
  - accès depuis la tablette par Tailscale.
- Multi-clients :
  - inscription par SIREN ;
  - onboarding obligatoire, puis proactif (diagnostic, site vitrine, fiche Google, profil auto, « Passer ») ;
  - mémoire séparée par client.
- Piliers Enterprise, 21/21 tests :
  - limite de 5 demandes par minute ;
  - anti double-clic ;
  - plans avec verrous et fenêtre « Passez au plan… » ;
  - disjoncteur Groq avec mode dégradé ;
  - audit par utilisateur.
- Évolution du Cortex, 12/12 tests :
  - propositions à valider ;
  - auto-réparation par corrections prédéfinies ;
  - Délégation décochée par défaut.
- Copilote :
  - fichiers, images, vidéos, calendrier, graphiques, PDF ;
  - RAG local, recherche approfondie, mémoire long terme.
- Journal chaîné intègre, sauvegardes, guide AUTONOMIE.md.

### En cours, ou de ton côté
- **SMTP Hostinger refusé** : pastille email rouge. À régler dans hPanel ; aucun email réel ne part tant que ce n'est pas fait.
- **HTTPS Tailscale** : cliquer « Enable HTTPS » sur login.tailscale.com/admin/dns, puis je bascule le relais.
- **Lecteur Telegram** (`chat_daemon.py`) à l'arrêt : constaté avant ce chantier, pas encore corrigé. Sa tâche planifiée est désactivée.
- **Paiement en ligne** absent : les plans sont attribués à la main (colonne `plan`). Il faudra Stripe pour facturer.

### À faire avant d'accueillir de vrais clients
- **Hébergement** :
  - Render (voir `DEPLOIEMENT.md`) ou un VPS.
  - L'offre gratuite de Render a un disque éphémère : la base serait perdue à chaque redémarrage.
  - Il faut un disque persistant ou PostgreSQL, et un Workspace configurable.
- **Hostinger** : l'hébergement web mutualisé n'exécute pas un serveur Python permanent. Il convient pour le site vitrine josyei.com, pas pour le Cortex. Seul un VPS Hostinger le permettrait.
- **RGPD** :
  - contrats de sous-traitance (hébergeur, Groq) ;
  - politique de confidentialité et mentions légales ;
  - durées de conservation, sauvegardes chiffrées hors site.
- **Validation email** à l'inscription, quand le SMTP marchera.

## 5. Faisabilité : local ou cloud

| Besoin | Fait ici, en local | Ce qu'il faudrait dans le cloud |
|---|---|---|
| Limite de débit, disjoncteur | En mémoire du serveur, une seule machine | Redis (Upstash, offre gratuite) si plusieurs serveurs |
| Anti double-clic | Table SQLite `idempotence` | Même table sur PostgreSQL |
| Plans et fonctionnalités | Table `plans` + colonne `plan` | Stripe (abonnements, webhooks qui mettent à jour le plan) |
| Audit | Journal chaîné SHA-256, avec l'utilisateur | Copie externe du journal (stockage objet) |
| Alertes d'erreurs | Bandeau dans l'interface, auto-réparation | Sentry (offre gratuite) pour les erreurs serveur |
| Base de données | SQLite (11 Mo) | PostgreSQL géré (Neon ou Supabase, offre gratuite) |
| Fichiers clients | Cortex-Workspace sur le PC | Stockage objet (Cloudflare R2, offre gratuite) |
| Accès distant | Tailscale (privé, gratuit) | HTTPS public avec nom de domaine |

Recommandation : rester sur **PC + Tailscale** tant qu'il n'y a pas de client payant. La première étape cloud utile sera Stripe, puis un hébergement avec disque persistant, quand le RGPD sera réglé.
