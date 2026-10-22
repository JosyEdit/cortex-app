# Module OSINT du Cortex

`osint_tools.py` enrichit un dossier d'audit avec des données publiques et professionnelles sur une entreprise.
Chaque appel est consigné dans `audit.db` (table `audit_log`, lignes chaînées par sha256).

## Outils

| Fonction | Source | Ce qu'elle renvoie |
|---|---|---|
| `get_legal_data` | API officielle recherche-entreprises.api.gouv.fr (sans clé) | raison sociale, SIREN, siège, code NAF, adresse, dirigeants déclarés, date de création, effectifs |
| `scan_technologies` | python-wappalyzer | technologies visibles du site (CMS, frameworks, analytics), HTTPS |
| `find_social_profiles` | Sherlock | plateformes où l'identifiant de la marque existe |
| `scrape_website_emails` | requests (+ BeautifulSoup si installé) | emails génériques du domaine du site |
| `run_full_osint_audit` | les quatre ci-dessus | un résultat consolidé, erreurs comprises |

Google Maps n'est pas scrapé. La position et les avis Google Maps viennent de Serper (`audit.py`).

## Limites légales appliquées dans le code

- **Pas de scan de vulnérabilités.** Sonder les failles d'un site sans l'accord écrit de son propriétaire est une
  atteinte à un système de traitement automatisé de données (art. 323-1 du Code pénal). Seule la détection des
  technologies visibles est faite. Un audit de sécurité ne se fera qu'à la demande écrite d'un client, dans un
  module séparé.
- **RGPD et minimisation.** Seules les adresses génériques du domaine sont gardées (contact@, info@, accueil@,
  direction@, bonjour@, hello@, admin@). Une adresse nominative ou contenant un chiffre n'est jamais conservée.
  Sherlock refuse tout nom qui ressemble à une personne physique.
- **robots.txt.** Il est lu avant toute page. S'il interdit l'accès, rien n'est lu.
- **Conditions de Google.** Pas de scraping de Google Maps ; aucun contournement de CAPTCHA ni de protection.
- **Conservation.** Les données OSINT brutes sont purgées après 90 jours ; seules les conclusions restent.
- **Exclusion.** Un domaine ou un SIREN de la table `exclusion` (ou une adresse de la liste d'opposition)
  bloque tout contact.

## Installation

Rien n'est installé automatiquement. Sans les paquets, chaque outil concerné renvoie une erreur et l'audit
continue. Après l'accord de JOSY : `install_osint.bat` (Windows) ou `install_osint.sh` (Linux, Mac). Le script
vérifie Python 3.10+, demande confirmation, puis installe python-wappalyzer, sherlock-project et beautifulsoup4.
