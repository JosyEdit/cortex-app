# Le Cortex — JOSY EI

Agent autonome **supervisé** de JOSY EI (SIREN 914 113 543, Montmorillon, 86).
Il lit l'actualité IA, détecte des opportunités business pour JOSY EI
(SEO local, automatisation, IA pour TPE/PME et artisans de la Vienne),
prépare des actions et **demande la validation de JOSY sur Telegram**
(@JosyEiMasterBot) avant toute action à risque.

## Fonctionnement

GitHub Actions lance `cortex.py` **toutes les 15 minutes**. Chaque cycle :

1. lit les commandes Telegram (`getUpdates`, offset mémorisé dans `cortex.db`) ;
2. applique les timeouts : **R2 = 2 h, R3 = 24 h → refus automatique** ;
3. si le Cortex n'est pas arrêté (`/stop`), lit 3 flux RSS
   (Frandroid, TechCrunch AI, Usine Digitale IA) ;
4. quand il y a au moins 5 nouveaux articles (ou 3 h sans analyse), les
   envoie à Groq (`openai/gpt-oss-120b`) avec `AGENTS.md` comme system prompt ;
5. fait contrôler chaque proposition par le **pouvoir judiciaire** ;
6. soumet les R2/R3 à JOSY (boutons ✅/❌ + commandes), notifie les R1,
   journalise les R0.

La mémoire (`cortex.db`, SQLite) est conservée d'un cycle à l'autre via le
cache GitHub Actions.

## Séparation des pouvoirs (I12)

| Pouvoir | Où | Rôle |
|---|---|---|
| Législatif | `AGENTS.md`, constantes en tête de `cortex.py` | Règles fixées par JOSY, modifiées uniquement par commit (I13) |
| Exécutif | Groq + `Telegram`, `fetch_feeds`, `dispatch`, `execute` | Lit, analyse, propose, remet le contenu validé |
| Judiciaire | classe `Judiciaire` | Contrôle déterministe, dernier mot, peut relever le risque jamais le baisser |

## Garde-fous appliqués par le code

| Invariant | Mise en œuvre |
|---|---|
| I1 Traçabilité | Table `journal` append-only chaînée par SHA-256 ; `/etat` vérifie l'intégrité. Trace courte (sans contenu) dans les logs Actions |
| I2 Validation | R2/R3 en `en_attente_humain` ; rien n'est exécuté sans `/valider` ; si l'envoi Telegram échoue, l'action est refusée d'office |
| I3, I5, I6 | Au moins 2 sources distinctes, **uniquement** des URL réellement lues dans les flux ; date reprise des flux, pas du modèle ; toute URL inventée = rejet |
| I4 | Emails/téléphones retirés de la cible, interdits dans le contenu ; seuls des articles publics sont envoyés à Groq |
| I7 | Table `RISK_BY_ACTION` ; type inconnu = R3 |
| I8 | Champ `reversibility` obligatoire |
| I9 | `/stop` : plus aucune lecture ni proposition jusqu'à `/reprise` |
| I10 | Le Cortex n'envoie, ne publie et ne paie rien : une action validée = contenu final remis à JOSY sur Telegram. IBAN/carte = rejet |
| I11 | Pied de page légal ajouté à chaque email (identification, intérêt légitime art. 6.1.f, « répondez STOP ») |
| I13 | Le Cortex peut proposer `amelioration_regle` (R2), jamais modifier ses fichiers |
| I14 Priorité au fondateur | `fondateur.py` : profil de vie interne (jamais dans un contenu sortant), plan du jour plafonné à la capacité déclarée, créneaux retirés des plages de silence et des jours off |

Quotas : 20 appels Groq/jour, 3 propositions/cycle, 12/jour, 10 en attente max.

## Commandes Telegram

`/etat` · `/attente` · `/valider ID` · `/refuser ID [motif]` · `/stop` · `/reprise` · `/aide`

Journée (I14) : `/jour` · `/ajuste …` · `/fait n` · `/reporte n` · `/jour off` · `/profil` · `/vie …` · `/bilan`

`ID` = les 8 premiers caractères de l'`action_id`. Seul le chat `TG_CHAT` est
obéi. Le Cortex lit les commandes à chaque cycle (délai jusqu'à ~15 min).
Une commande texte compte à son **heure d'envoi** ; un bouton compte à
l'heure où le Cortex le lit (préférer `/valider` près de l'échéance).

## Déploiement

1. Pousser ces fichiers dans le dépôt `josy-ei-cortex` (branche par défaut).
2. **Settings → Secrets and variables → Actions → New repository secret** :
   - `TG_TOKEN` : jeton du bot (@BotFather) ;
   - `TG_CHAT` : `8860334549` ;
   - `GROQ_API_KEY` : clé créée sur console.groq.com/keys.
3. **Actions → Cortex → Run workflow** pour un premier cycle, puis vérifier
   `/etat` dans Telegram.

Test local : `pip install -r requirements.txt` puis
`TG_TOKEN=... TG_CHAT=... GROQ_API_KEY=... python cortex.py`
(sans `TG_TOKEN`, les messages s'affichent dans la console).

## ⚠️ Points d'attention

- **Webhook ou autre lecteur = incompatibles.** Telegram refuse `getUpdates`
  tant qu'un webhook est actif, et deux programmes qui lisent les mises à jour
  du même bot se volent les messages. Donc : **pas de webhook** sur
  @JosyEiMasterBot, et le déclencheur `checkUpdates` de l'Apps Script
  « JOSY EI — Bot Telegram » doit être retiré (`removeTrigger()`). L'Apps
  Script de capture de leads peut continuer à **envoyer** des notifications
  (`sendMessage` ne gêne pas). Si un webhook est détecté, le Cortex prévient
  sur Telegram une fois par jour et ne supprime rien lui-même.
- **Repo public ou privé.** En public, les minutes Actions sont gratuites mais
  les logs sont publics (le Cortex n'y écrit que des noms d'événements, aucun
  contenu). En privé, un cycle toutes les 15 min consomme environ
  2 900 min/mois, au-delà des 2 000 min gratuites : passer le cron à
  `*/30 * * * *`.
- **I4 (données en UE) n'est pas totalement tenu par l'hébergement** :
  GitHub Actions, Groq et Telegram traitent hors UE. Atténuation : aucune
  donnée personnelle n'est envoyée (articles publics, cibles = entreprises).
- **Mémoire en cache** : si le cache est purgé (inactivité > 7 jours), le
  journal et les actions en attente repartent de zéro. Le cron GitHub est
  indicatif (retards possibles) et GitHub suspend les crons d'un repo public
  sans commit depuis 60 jours.
- L'URL du flux Usine Digitale n'a pas pu être vérifiée lors de l'écriture :
  si les logs Actions montrent `flux_erreur` pour ce flux, corriger l'URL
  dans `FEEDS`.
