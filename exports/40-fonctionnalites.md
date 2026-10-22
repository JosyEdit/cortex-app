# Les 40 fonctionnalités du Cortex : état au 13/10/2026

Légende : **Fait** = déjà en service avant ce tour · **Codé + testé** = module écrit, 33 vérifications passées en isolation (base temporaire), **pas encore branché dans cortex.py** (modification refusée par le garde-fou) · **Réalisable** = faisable avec Groq, SQLite, DuckDuckGo, Serper, Telegram, email, non commencé · **À décider** = demande une API, un budget, un accès ou un choix de JOSY.

| # | Fonctionnalité | État | Détail |
|---|---|---|---|
| 1 | Mémoire épisodique | Codé + testé | `memoire_avancee.py`, table `episodes`, commande `/memoire nom` |
| 2 | Mémoire sémantique | Codé + testé | table `faits` (6 décisions de JOSY préchargées, sourcées), `/fait cle = valeur` |
| 3 | Mémoire de travail | Codé + testé | table `memoire_travail`, vidée à la fin de chaque cycle |
| 4 | Mémoire de saillance | Codé + testé | score 1 à 5 par épisode (intéressé 5, stop 4…), `/important` |
| 5 | Portabilité de la mémoire | Codé + testé | export JSON de toutes les tables, import dans une base neuve, chaîne du journal revérifiée (11 lignes aller-retour) |
| 6 | Apprentissage par l'expérience | Codé + testé | taux de réponse par type d'argument, aucun principe sous 10 envois |
| 7 | Détection d'anomalies | Codé + testé | erreur répétée (≥5 en 24 h), taux de réponse récent effondré ; alerte ⚠️ |
| 8 | Décroissance de confiance | Codé + testé | demi-vie 30 jours, principe désactivé sous 0,2 (poids 0,5 à 30 j vérifié) |
| 9 | Suggestion d'amendements | Codé + testé | proposition `amelioration_regle` à valider, déclenchée sous 3 % de réponses sur 30 envois ; jamais appliquée seule |
| 10 | Historique des versions | Codé + testé | AGENTS.md et secteurs.json versionnés, `/versions`, `/rollback ID` = proposition R3 à valider |
| 11 | Telegram | Fait | chat libre, commandes, formats A à F |
| 12 | Email professionnel | Fait en partie | envoi et lecture OK ; relances J+3 et J+7 en service ; **J+14 non ajouté** (modification refusée) ; réponses : 3 propositions, choix par clic |
| 13 | Google Business | À décider | l'API Business Profile exige un accès approuvé par Google et OAuth2 |
| 14 | Site web (WordPress) | Réalisable | publication par mot de passe d'application, donné à chaque session (aujourd'hui) ; articles et SEO à coder |
| 15 | Boutique (WooCommerce) | À décider | clés API WooCommerce et confirmation que le plugin est installé |
| 16 | Enrichissement de prospects | Fait en partie | SIREN, adresse, site, email, dirigeants publics ; téléphone non utilisé (aucun appel) |
| 17 | Scoring ICP | Réalisable | règles sur secteur, effectif, manque vérifié ; non commencé |
| 18 | Signaux d'achat | Réalisable | veille par entreprise via DuckDuckGo ; fiabilité faible, non commencé |
| 19 | Analyse concurrentielle locale | Fait en partie | Serper (Google Maps) : 1er résultat, moyenne locale d'avis ; pas encore les 3 concurrents nommés |
| 20 | Personnalisation | Fait | chaque email cite un fait vérifié, sinon pas d'email |
| 21 | Articles de blog (800 à 1500 mots) | Réalisable | Groq + publication WordPress ; sans images |
| 22 | SEO en temps réel | Réalisable | titres, intertitres, alt ; non commencé |
| 23 | Analyse de mots-clés | À décider | demande un outil de mots-clés (API payante) ou une approximation par suggestions Google |
| 24 | Surveillance de position | À décider | une requête Serper par mot-clé et par jour : budget de crédits à fixer |
| 25 | Rapport de performance | À décider | trafic et conversions demandent l'accès Google Analytics / Search Console du client |
| 26 | CRM intégré | Codé + testé | fiche client depuis cortex.db, `/client nom` |
| 27 | Relances automatiques | Codé + testé en partie | notification « 📭 sans réponse après 3 relances » prête ; J+14 non branché |
| 28 | Qualification automatique | Fait | « combien », « devis », « rdv »… déclenchent le message 🔥 |
| 29 | Rapport client mensuel | Codé + testé | ne cite que les actions consignées ; sinon « Aucune action enregistrée » ; envoi après validation (envoi branché : non) |
| 30 | Enquête de satisfaction | Codé + testé | proposée après `/livree nom email`, envoi après validation (envoi branché : non) |
| 31 | Audit log inviolable | Fait + testé | chaîne SHA-256 ; contrôle à chaque cycle avec alerte (falsification simulée détectée) |
| 32 | Liste d'opposition | Fait + testé | vérifiée avant chaque envoi ; hash seulement |
| 33 | RGPD | Codé + testé | `/oubli adresse confirmer`, `/donnees adresse` ; lien de désinscription dans chaque email (fait) |
| 34 | Isolation par client | À décider | aucune application multi-clients n'existe : aucun test réalisé, le chiffre « 324 requêtes, 0 fuite » ne vient pas de ce projet |
| 35 | Authentification forte | À décider | Hostinger SMTP/IMAP n'accepte qu'un mot de passe ; Telegram : jeton ; clés dans .env, jamais dans les journaux |
| 36 | Multi-agents | À décider | version sûre proposée : tâches parallèles internes (3 audits simultanés), sans agents autonomes ; à valider |
| 37 | File d'attente robuste | Fait | file d'envoi et propositions en SQLite, reprise après redémarrage |
| 38 | Transition PC → cloud | Réalisable | chemins relatifs et secrets dans .env déjà en place ; planification et VPS à choisir |
| 39 | Monitoring | Réalisable | les jetons consommés ne sont pas enregistrés aujourd'hui (seulement le nombre d'appels) ; tableau de bord à coder |
| 40 | Budget contrôlé | Réalisable | plafond d'appels IA par jour existe ; plafonds par tâche (jetons, coût, temps) à coder |

**Bilan** : Fait 6 (11, 20, 28, 31, 32, 37) + 3 en partie (12, 16, 19) · Codé + testé 14 (1 à 10, 26, 29, 30, 33) + 27 en partie · Réalisable non commencé 8 · À décider 8 (13, 15, 23, 24, 25, 34, 35, 36).
