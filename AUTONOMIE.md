# Le Cortex sans IA : démarrer, arrêter, modifier

Ce guide sert quand aucune IA n'est disponible pour t'aider. Tout se fait avec l'Explorateur Windows, PowerShell et un éditeur de texte (Bloc-notes ou VS Code).

Dossier du Cortex : `C:\Users\JOSY EI\cortex`
Fichiers produits (rapports, sites, images…) : `C:\Users\JOSY EI\Cortex-Workspace`

## 1. Ce qui tourne sur le PC

| Programme | Rôle | Comment il démarre |
|---|---|---|
| `cortex.py` | Moteur : cycles de prospection toutes les 5 min, emails, veille, journal | Tâche planifiée « JOSY EI Cortex » |
| `app.py` | Interface web (Tableau de bord, Copilote, Mon Agent, Profil) sur http://127.0.0.1:8765 | Relancée par `veille_service.py` |
| `veille_service.py` | Surveillance : relance l'interface et le lecteur Telegram s'ils s'arrêtent | « Cortex - surveillance.vbs » (dossier Démarrage de Windows) |
| `chat_daemon.py` | Lecteur Telegram instantané | Relancé par la surveillance (tâche « JOSY EI Cortex Chat » désactivée) |
| Tailscale | Accès depuis la tablette, réseau privé uniquement | Service Windows Tailscale |

## 2. Démarrer

- **Interface** : double-clic sur `cortex-app.bat` (une fenêtre reste ouverte), ou attendre 1 minute : la surveillance la relance seule.
- **Moteur** : Planificateur de tâches, tâche « JOSY EI Cortex », clic droit, Exécuter.
- **À la main dans PowerShell** :
  ```
  cd "C:\Users\JOSY EI\cortex"
  python app.py --ouvrir
  ```
- **Adresse** : http://127.0.0.1:8765/?t=JETON. Le jeton est dans le fichier `.app-token` (ne le partage pas).

## 3. Arrêter

- **Interface** : double-clic sur `arret-interface.bat`. La surveillance la relance dans la minute ; c'est voulu.
- **Arrêter durablement** :
  1. Gestionnaire des tâches, onglet Détails : terminer les `pythonw.exe` (surveillance, interface, lecteur).
  2. Planificateur de tâches : clic droit sur « JOSY EI Cortex », puis Désactiver.
  3. Retirer « Cortex - surveillance.vbs » du dossier Démarrage (Win+R, puis `shell:startup`).
- **Accès tablette** : `tailscale serve --http=8765 off`, ou quitter Tailscale depuis l'icône près de l'horloge.

## 4. Vérifier que tout va bien

- `cortex-app.log` : démarrages et erreurs de l'interface.
- `surveillance.log` : relances faites par la surveillance.
- Interface, onglet **Mon Agent** :
  - santé du système ;
  - bloc « Évolution du Cortex » (propositions et auto-réparation) ;
  - tests : `python tests_activation.py`.
- Intégrité du journal, dans PowerShell :
  ```
  python -c "import cortex as C; print(C.Store(C.DB_PATH).verify_journal())"
  ```
  `(True, …)` = la chaîne est intacte.

## 5. Modifier sans IA

1. **Toujours sauvegarder d'abord** : copier `cortex.db` et le fichier à modifier dans `sauvegardes\avant-<sujet>-<date>\`.
2. Ouvrir le fichier `.py` dans VS Code, modifier, enregistrer en UTF-8.
3. Vérifier la syntaxe : `python -m py_compile app.py` (aucun message = OK).
4. Relancer : `arret-interface.bat` (l'interface repart seule), ou redémarrer la tâche « JOSY EI Cortex » pour le moteur.
5. En cas de problème : recopier le fichier depuis `sauvegardes\` et relancer.

Où changer quoi :

| Je veux changer… | Fichier |
|---|---|
| Les textes et pages de l'interface | `app.py` (fonctions `vue_…` et `bloc_…`) |
| Les règles d'or et le ton de l'IA | `app.py` (`CHAT_PROMPT`), `routage_telegram.py` (`BOT_SYSTEM_PROMPT`) |
| Les formules et fonctionnalités par plan | `fiabilite.py` (`PLANS`) |
| Les limites (5 demandes/min, disjoncteur 3 échecs / 5 min) | `fiabilite.py` (`LIMITE`, `SEUIL_ECHECS`, `PAUSE_S`) |
| Les plafonds d'emails et le mode auto | `mode_execution.py`, `cycle_emails.py` |
| Les clés (Groq, Hostinger, Telegram…) | fichier `.env` (jamais dans un message ni dans git) |
| Les consignes ajoutées par « Évolution » | Mon Agent, « Consignes ajoutées au Copilote », bouton Retirer |

## 6. Garde-fous à ne jamais retirer

- Le serveur écoute sur 127.0.0.1 : seul Tailscale (réseau privé) y donne accès. Pas de Funnel.
- Rien n'est envoyé ni publié sans validation, sauf les relances du Mode Automatique dans ses limites (30/jour, désinscription, aucun prix).
- Délégation (Profil) : décochée par défaut. Le Cortex ne modifie jamais son propre code.
- Le journal est chaîné (SHA-256) : ne jamais modifier la table `journal` à la main.

## 7. Mots de passe oubliés (aucun email)

- **Un client** : il clique « Mot de passe oublié » et donne son email. La demande apparaît dans Mon Agent › « Demandes d'accès en attente », et tu reçois une alerte Telegram.
  1. Vérifie son identité (rappel au téléphone connu, SIREN, adresse).
  2. Clique « Générer un code », puis donne-lui le code à 6 chiffres.
  3. Il va sur « J'ai reçu mon code » et choisit son nouveau mot de passe.
- **Toi (fondateur)** : depuis le PC, dans PowerShell :
  ```
  cd "C:\Users\JOSY EI\cortex"
  python acces.py --reinitialiser ton-email
  ```

## 8. Pannes fréquentes

| Symptôme | Cause probable | Que faire |
|---|---|---|
| Page « Refusé » | Jeton absent de l'adresse | Ajouter `?t=` + le contenu de `.app-token` |
| Bandeau rouge « Mode dégradé » | Groq a échoué 3 fois | Attendre 5 min, ou Mon Agent, Auto-réparation, « Appliquer la correction » |
| « Limite atteinte » | Plus de 5 demandes en une minute | Attendre 60 s |
| L'interface ne répond plus | Processus arrêté | Attendre 1 min (surveillance), sinon `cortex-app.bat` |
| Pastille email rouge | SMTP Hostinger refusé | Réglage côté hPanel Hostinger (pas dans le Cortex) |
