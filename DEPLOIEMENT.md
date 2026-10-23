# Déployer l'interface du Cortex sur Render

À lire en entier avant de cliquer : **héberger chez un tiers fait sortir la base (prospects, comptes clients, journal) et les clés du PC**. Ne le fais qu'après avoir réglé les points de la section 4.

## Ce qui est prêt dans le code

- `app.py` lit `PORT` (imposé par Render) et `HOST`. Sans variable, il reste sur `127.0.0.1:8765` : rien ne change sur le PC ni pour le relais Tailscale.
- `CORTEX_HOTES` liste les noms publics acceptés (ex. `cortex-josyei.onrender.com`). Sans cette variable, toute requête venant d'un autre nom est refusée.
- `requirements-serveur.txt` : version légère, sans Playwright, rembg, moviepy ni OSINT, trop lourds pour 512 Mo.

## Les 3 étapes sur Render

1. **Créer le service** : render.com, New, Web Service, connecter le dépôt GitHub qui contient le dossier `cortex` (dépôt privé), Runtime : Python 3.
2. **Commandes** :
   - Build Command : `pip install -r requirements-serveur.txt`
   - Start Command : `python app.py`
3. **Variables d'environnement** (Environment, jamais dans le code) :

   | Variable | Valeur |
   |---|---|
   | `HOST` | `0.0.0.0` |
   | `CORTEX_HOTES` | le nom donné par Render, ex. `cortex-josyei.onrender.com` |
   | `PYTHON_VERSION` | `3.12.7` |
   | `GROQ_API_KEY` | ta clé Groq |
   | `SERPER_API_KEY` | facultatif (recherche web) |

   `PORT` est fourni par Render : ne pas le créer.

Ensuite, l'adresse sera `https://<nom>.onrender.com/?t=<jeton>`. Le jeton est créé au premier démarrage dans `.app-token`. Le mieux est de le fixer toi-même : un fichier secret Render nommé `.app-token`.

## Base PostgreSQL Neon

- Si `DATABASE_URL` est défini, `cortex.py` utilise PostgreSQL via `psycopg2`; sans cette variable, le mode local reste sur SQLite (`cortex.db`).
- `psycopg2-binary` est déclaré dans `requirements-serveur.txt`, utilisé par la commande de build Render ci-dessus, et dans `requirements.txt`.
- En local, `DATABASE_URL` peut être chargé depuis `.env.local` (ou `.env`). Ces fichiers sont ignorés par Git. Sur Render, configure `DATABASE_URL` dans les variables d'environnement du service; le fichier local créé par `neon env pull` n'est pas transmis automatiquement à Render.
- Les tables applicatives sont créées au démarrage, mais le contenu existant de `cortex.db` n'est pas migré vers Neon automatiquement. Les données existantes doivent être exportées/importées séparément avant de basculer la production.
- La sauvegarde SQLite intégrée à l'interface n'est pas disponible en mode PostgreSQL; utiliser les sauvegardes du fournisseur PostgreSQL.

## Limites à connaître (offre gratuite)

- **Disque éphémère** : les sessions et le Workspace sont effacés à chaque redéploiement ou redémarrage. Une base PostgreSQL Neon conserve les données applicatives, mais pas les fichiers du Workspace.
- **Mise en veille** après 15 min sans visite : le premier accès prend environ 1 minute.
- **512 Mo de mémoire** : pas de détourage d'image (rembg), pas de vidéo, pas de lecture de sites par navigateur (Playwright).
- **Chemins Windows** : le Workspace (`C:\Users\JOSY EI\Cortex-Workspace`) devient un simple dossier relatif sous Linux ; à remplacer par une variable (`CORTEX_WORKSPACE`) avant un vrai déploiement.
- **Moteur** : seul l'interface (`app.py`) est prévue ici. Le moteur (`cortex.py`, cycles, emails) resterait sur le PC, ou demanderait un « Background Worker » Render payant.

## 4. À régler AVANT d'héberger des données clients (RGPD)

- **Contrat de sous-traitance (DPA)** avec Render (hébergeur, États-Unis : clauses contractuelles types) et avec Groq (le texte des échanges y transite). Vérifier la région : Render propose Francfort, à choisir.
- **Politique de confidentialité** et **mentions légales** publiées, registre des traitements à jour (prospects B2B : intérêt légitime, droit d'opposition, désinscription).
- **Durées de conservation** : purge des prospects inactifs et des journaux selon la durée définie.
- **Sauvegardes chiffrées** hors de l'hébergeur, et procédure en cas de fuite (CNIL sous 72 h).
- **HTTPS** : fourni par Render. Le cookie de session passe alors en `Secure` automatiquement.

Tant que ces points ne sont pas réglés, la solution recommandée reste l'actuelle : **le PC + Tailscale** (rien n'est exposé à Internet, les données ne quittent pas le PC).
