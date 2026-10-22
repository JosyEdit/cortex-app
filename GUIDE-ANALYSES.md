# Cortex — connexion et analyses (21/10/2026)

## Connexion
- L'adresse habituelle (raccourci du Bureau, avec `?t=…`) ouvre maintenant la page de connexion.
- Compte fondateur : ton email Gmail. Mot de passe initial : dans `MOT-DE-PASSE-INITIAL.txt`
  (dossier cortex). Change-le dans l'onglet **Profil**, puis supprime ce fichier.
- Session : 12 h, cookie HttpOnly. 5 erreurs en 15 min bloquent la connexion 15 min.
  Un redémarrage de l'interface déconnecte.

## Analyses (onglet Discuter)
Tape une phrase, ou clique sur un bouton sous la zone de texte :

| Demande | Outils lancés |
|---|---|
| `Analyse la société Fruchon à Montmorillon` | registre public de l'État + concurrents (même code NAF, même code postal) + Bourse (si grande entreprise) |
| `Analyse la société X https://site-de-x.fr` | les mêmes + audit technique du site |
| `Audite le site https://exemple.fr` | audit technique (temps de réponse, balises, liens brisés, robots/sitemap, rendu Chrome, certificat) + registre (rapprochement par le nom de domaine, à confirmer) |
| `Quels sont les concurrents des garages à Montmorillon ?` | registre public (entreprises actives) |
| `Analyse OSINT de la société X` | sources publiques sur l'entreprise (registre, site si lien) |

La réponse affiche d'abord les résultats de chaque outil avec leur source, puis le croisement,
la synthèse et 3 recommandations rédigés par Groq à partir de ces seuls résultats. Une analyse
prend de 10 s à 2 min (l'audit de site est le plus long).

## Ce qui n'est pas fait, et pourquoi
- `webaudit` et `pyseoa` : non installés (paquets récents d'un seul auteur, une à quatre
  versions : risque non vérifiable). Remplacés par requests, BeautifulSoup et Playwright.
- `instaloader`, LinkedIn, réseaux sociaux : non (réseaux désactivés pour le Cortex depuis le
  13/10, extraction automatisée interdite par leurs conditions). OSINT = entreprises seulement.
- `python-nmap` : non installé (Nmap absent du PC). Un scan ne se fait que sur tes propres
  équipements, à la main : scanner un tiers sans autorisation est un délit (art. 323-1 du Code pénal).
- `yfinance` : installé, utilisé seulement pour les grandes entreprises cotées (sans objet pour
  une TPE/PME).
- Moteurs de recherche (Google) : pas aspirés ; la concurrence vient du registre public.

## Icône
Pour voir la nouvelle icône : désinstalle l'application (menu ⋮ de la fenêtre Cortex >
Désinstaller), rafraîchis la page dans Chrome ou Edge, puis réinstalle-la.
