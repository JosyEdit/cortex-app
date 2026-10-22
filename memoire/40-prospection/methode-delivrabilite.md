---
id: methode-delivrabilite
type: methode
titre: Délivrabilité des emails de prospection (Gmail, Workspace, domaine propre, exigences Google/Yahoo/Microsoft)
mis_a_jour: 2026-10-11
confiance: moyenne
revoir_avant: 2027-04-11
tags: [methode, delivrabilite, spf, dkim, dmarc, gmail, workspace, outlook, yahoo, warm-up, spam, postmaster]
---

# Délivrabilité des emails de prospection

But : que chaque email validé par JOSY arrive en **boîte de réception**, pas en spam. JOSY EI envoie peu (quelques dizaines par semaine au plus). Les seuils « gros expéditeurs » (5 000/jour) ne s'appliquent pas, mais les règles de base s'appliquent à **tous** les expéditeurs.

## Exigences Google pour tous les expéditeurs (depuis février 2024)

Applicables à tout envoi vers des adresses Gmail personnelles, depuis le **1er février 2024** [S1] :
- Configurer **SPF ou DKIM** pour le domaine d'envoi [S1].
- DNS direct et inverse (**PTR**) valides pour les IP d'envoi [S1] (géré par Google si l'on envoie via Gmail/Workspace, estimation).
- Envoi en **TLS** [S1].
- Taux de spam dans Postmaster Tools **sous 0,3 %** ; Google recommande de rester **sous 0,10 %** [S1].
- Messages conformes à la RFC 5322 [S1].
- Ne pas usurper l'en-tête « From » de gmail.com : Gmail applique une mise en quarantaine DMARC [S1]. Conséquence : un outil tiers ne peut pas envoyer « au nom » d'une adresse @gmail.com (estimation fondée sur [S1]).
- Clés DKIM d'au moins **1 024 bits**, **2 048 bits** recommandés [S1].

## Exigences Google pour plus de 5 000 messages par jour

- **SPF et DKIM** tous les deux, plus **DMARC** (politique « none » acceptée) [S1].
- Alignement : le domaine du « From » doit correspondre au domaine SPF ou DKIM [S1].
- Messages marketing et d'abonnement : **désinscription en un clic** (en-têtes List-Unsubscribe et List-Unsubscribe-Post) et lien visible dans le corps [S1].
- JOSY EI est loin de ce seuil, mais applique quand même SPF + DKIM + DMARC sur son domaine : c'est le standard attendu et c'est gratuit (estimation).

## Exigences Yahoo (février 2024)

- Tous expéditeurs : SPF **ou** DKIM, taux de plainte **< 0,3 %**, DNS direct/inverse valides, RFC 5321/5322 [S2].
- Expéditeurs en volume : SPF **et** DKIM, DMARC au minimum `p=none` qui passe, alignement du From, tag `rua` fortement recommandé [S2].
- Désinscription en un clic (POST RFC 8058 recommandé, mailto accepté), lien visible, désinscriptions traitées **sous 2 jours** [S2].
- Le taux de plainte est calculé sur les messages **livrés en boîte de réception** [S2].

## Exigences Microsoft Outlook (mai 2025)

- À partir du **5 mai 2025**, Outlook.com, Hotmail.com et Live.com appliquent de nouvelles règles aux expéditeurs de **5 000 emails par jour ou plus** depuis un domaine [S3].
- Exigences : SPF qui passe, DKIM qui passe, DMARC au moins `p=none` aligné avec SPF ou DKIM [S3].
- Non-conformes : d'abord dossier **indésirables**, puis rejet possible avec le code « 550; 5.7.515 Access denied… » [S3].
- Bonnes pratiques recommandées : adresse From ou Reply-To réelle, désinscription fonctionnelle, nettoyage des adresses invalides, objets non trompeurs [S3].
- Source : synthèse Twilio (secondaire) ; l'annonce Microsoft n'a pas pu être lue directement.

## Limites d'envoi : Gmail personnel vs Google Workspace

| Compte | Limite | Source |
|---|---|---|
| Gmail personnel | Erreur au-delà de **500 destinataires** au total pour un message, ou plus de **500 emails par jour** ; reprise sous 1 à 24 h | [S4] |
| Gmail personnel | Trop de messages non distribuables (rebonds) : reprise après **24 h** | [S4] |
| Google Workspace | **2 000 emails/jour** et **10 000 destinataires/jour** par utilisateur ; **3 000 destinataires uniques/jour** dont **2 000 externes** | [S5] (secondaire) |
| Les deux | Fenêtre glissante de 24 h, pas le jour calendaire | [S5] (secondaire) |

Ces limites sont des plafonds techniques, pas des volumes recommandés. Pour de la prospection, rester très en dessous (voir échauffement).

## Pourquoi un domaine séparé (et pourquoi pas une adresse @gmail.com)

- Une adresse **@gmail.com** n'a pas de SPF/DKIM/DMARC propres à JOSY EI : impossible d'aligner un domaine à soi, et aucun outil tiers ne peut envoyer en son nom sans quarantaine DMARC [S1] (estimation sur les conséquences).
- Un email de prospection depuis une adresse gratuite paraît moins professionnel à un gérant de PME (estimation).
- **Domaine séparé** : si la prospection dégrade la réputation, le domaine principal (josyei.com, utilisé pour les clients et les factures) reste protégé (estimation, pratique courante non sourcée sur primaire).
- Recommandation JOSY EI (estimation) :
  1. Domaine principal josyei.com pour les clients ; Google Workspace ou équivalent.
  2. Domaine secondaire proche (ex. variante de josyei) pour la prospection, avec une vraie boîte qui reçoit les réponses et un site minimal qui redirige vers josyei.com.
  3. SPF + DKIM + DMARC (`p=none` au départ avec `rua`, puis `quarantine`) sur **les deux** domaines.
- Le domaine secondaire doit afficher la **même identité** (JOSY EI, SIREN) : masquer l'annonceur est interdit (voir `legal-prospection-b2b`).

## Échauffement (warm-up) d'une nouvelle adresse

Les éditeurs recommandent de commencer à faible volume et d'augmenter progressivement sur **2 à 4 semaines**, en gardant les plaintes sous 0,3 % [S5]. Aucune source primaire ne fixe de paliers chiffrés. Paliers JOSY EI (estimation) :

| Semaine | Envois de prospection / jour ouvré | Condition pour passer au palier suivant |
|---|---|---|
| S1 | 5 | 0 plainte, rebonds < 3 % |
| S2 | 10 | idem + au moins quelques réponses |
| S3 | 15 | idem |
| S4 et après | 20 maximum | taux de spam Postmaster < 0,1 % si disponible |

- En parallèle : utiliser la boîte normalement (échanges réels avec clients, partenaires) (estimation).
- Pas d'outil de « warm-up automatique » qui échange de faux emails : pratique non sourcée et contraire à l'esprit des règles des fournisseurs (estimation).
- Si les rebonds dépassent 3 % ou si une plainte arrive : revenir au palier précédent pendant une semaine (estimation).

## Vérification des adresses avant envoi

- Un rebond massif bloque l'envoi Gmail pendant 24 h [S4]. Chaque rebond nuit à la réputation (estimation).
- Méthode gratuite JOSY EI (estimation) :
  1. Adresse **copiée depuis le site officiel** de l'entreprise (page contact, mentions légales), jamais devinée (prenom.nom@ généré).
  2. Vérifier que le domaine a un enregistrement **MX** (MXToolbox, outil gratuit en ligne).
  3. Site web actif et entreprise active (`etat_administratif = A` dans l'API Recherche d'entreprises, voir `methode-sources-donnees-entreprises`).
- Les services de vérification payants ne sont pas nécessaires au volume de JOSY EI (estimation).

## Signaux de spam à éviter

- Plaintes : rester sous 0,1 % recommandé par Google, jamais à 0,3 % [S1][S2].
- Absence de désinscription ou lien cassé [S1][S3].
- Objet trompeur, en-têtes trompeurs [S3].
- Adresses invalides ou inactives non nettoyées [S3].
- Liens multiples, raccourcisseurs d'URL, images seules, pièces jointes, majuscules et points d'exclamation (estimation, pratiques courantes non sourcées sur primaire).
- Envoi en rafale à heure fixe depuis un script : préférer un envoi espacé de quelques minutes (estimation).
- **Pixels de suivi** : à proscrire en prospection, pour des raisons juridiques (recommandation CNIL d'avril 2026) [S7] ; en bonus, moins d'éléments distants dans l'email (estimation).

## Outils gratuits de contrôle

- **Google Postmaster Tools** : suivi du taux de spam, de la réputation, de l'authentification et des erreurs de livraison, pour les messages envoyés vers des comptes Gmail personnels ; nécessite de valider le domaine ; données absentes les jours de **faible volume** [S6]. Au volume de JOSY EI, les tableaux seront souvent vides (estimation).
- **mail-tester.com** : envoyer un email de test à l'adresse fournie pour obtenir un score (SPF, DKIM, DMARC, contenu) (non vérifié : limites de la version gratuite).
- **MXToolbox** : vérification des enregistrements MX, SPF, DKIM, DMARC et des listes noires (non vérifié : détail des fonctions gratuites).
- **En-têtes de message** dans Gmail (« Afficher l'original ») : vérifier SPF=PASS, DKIM=PASS, DMARC=PASS sur un email envoyé à soi-même (estimation).

## Checklist délivrabilité avant le premier envoi

1. Domaine de prospection acheté, boîte réelle, site minimal.
2. SPF publié (un seul enregistrement SPF par domaine).
3. DKIM activé, clé 2 048 bits [S1].
4. DMARC `p=none` avec `rua`, puis `quarantine` après 4 semaines sans anomalie (estimation).
5. Test mail-tester et contrôle des en-têtes : PASS partout.
6. Postmaster Tools : domaine validé [S6].
7. Plan d'échauffement 5/10/15/20 respecté.
8. Ligne STOP dans chaque email ; STOP traité le jour même (Yahoo : 2 jours max) [S2].
9. Aucune adresse devinée ; MX vérifié.

## Sources

[S1] Google — Consignes destinées aux expéditeurs d'e-mails (Aide Google Workspace) — https://support.google.com/a/answer/81126?hl=fr — date non indiquée (exigences applicables depuis 2024-02-01) — consulté 2026-10-11
[S2] Yahoo — Sender Best Practices — https://senders.yahooinc.com/best-practices/ — date non indiquée (application depuis février 2024) — consulté 2026-10-11
[S3] Twilio — Outlook Announces New Sender Requirements (source secondaire) — https://www.twilio.com/en-us/blog/insights/outlook-new-email-sender-requirements — date non indiquée — consulté 2026-10-11
[S4] Google — Aide Gmail : limites d'envoi et erreurs (compte personnel) — https://support.google.com/mail/answer/22839?hl=fr — date non indiquée — consulté 2026-10-11
[S5] Smartlead — What is the Gmail Email Limit Per Day? (contenu éditeur, source secondaire) — https://www.smartlead.ai/blog/gmail-email-limit-per-day — publié 2026-10-09 — consulté 2026-10-11
[S6] Google — Aide Postmaster Tools (Google Workspace) — https://support.google.com/a/answer/9981691?hl=fr — date non indiquée — consulté 2026-10-11
[S7] CNIL — Pixels de suivi dans les courriers électroniques : la CNIL publie ses recommandations — https://www.cnil.fr/fr/recommandation-pixel-suivi-courriels — publié 2026-04-14 — consulté 2026-10-11
