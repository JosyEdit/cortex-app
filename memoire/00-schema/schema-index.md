---
id: schema-index
type: schema
titre: Index de la Mémoire du Cortex (JOSY EI)
mis_a_jour: 2026-10-11
confiance: haute
revoir_avant: 2027-01-11
tags: [index, schema, sommaire, memoire]
---

# Mémoire du Cortex — index

Bibliothèque de connaissances que le Cortex consulte (en lecture seule) pour
connaître ses cibles, choisir l'angle d'un email, répondre aux objections et
rester dans la loi. 31 fiches, 378 sections indexées, 293 sources citées
(URL + date), construite le 2026-10-11 par recherche web réelle.
Format et marqueurs : `schema-format-fiche`. Accès technique : `spec-acces-memoire`.

## Comment s'en servir

- **Humain** : ouvrir la fiche du secteur visé, puis `objections-reponses` et `methode-email-froid`.
- **Cortex** : `python outils/memoire.py search "notaire fraude virement"` ou `Memoire().contexte_pour_prompt(...)` dans `cortex.py`. Chaque passage renvoyé porte `memoire:fiche#section`, sa confiance et ses sources.
- **Contrôle qualité** : `python outils/memoire.py check` (en-têtes, renvois [Sx] résolus, motifs interdits, lignes chiffrées sans renvoi).
- Règle d'or : un chiffre ne va dans un email que s'il porte un `[Sx]` ; « estimation » et « non vérifié » restent internes.

## 1. Secteurs (10-secteurs) — 15 fiches, 13 sections chacune

Chaque fiche : identité et nombre de cibles 6-49 salariés (comptage API Recherche d'entreprises du 2026-10-11, France et Vienne), outils métier, besoins IT/IA/RGPD/cyber, obligations datées, incidents typiques, budget et décideur, signaux d'achat, objections, 3 accroches, angle du diagnostic 490 €, saisonnalité, où trouver les entreprises.

| Segment | Fiches |
|---|---|
| T1 professions réglementées | `secteur-experts-comptables`, `secteur-notaires`, `secteur-avocats`, `secteur-agences-immobilieres`, `secteur-courtiers-agents-assurance` |
| T2 | `secteur-sante-liberale`, `secteur-enseignement-formation-prive`, `secteur-industrie-pme` |
| Autres | `secteur-btp-artisans`, `secteur-transport-logistique`, `secteur-commerce-detail`, `secteur-hotellerie-restauration`, `secteur-services-aux-entreprises`, `secteur-architectes-bureaux-etudes`, `secteur-associations-medico-social` |

## 2. Dirigeants et objections (20-profils)

- `profils-dirigeants` : 8 personas (gérant artisan, associé libéral, responsable administratif, repreneur, office manager, directeur associatif…), priorités, peurs, mots à employer ou éviter. Confiance basse : comportements surtout estimés.
- `objections-reponses` : 23 objections avec ce qu'elles cachent, réponse écrite honnête, donnée sourcée et seuil d'abandon.

## 3. Marché (30-marche)

- `marche-chiffres-cles-tpe-pme` : taille, maturité numérique, adoption IA (France Num 2026 : 40 % des TPE/PME utilisent une IA), cyber (baromètre Cybermalveillance 2025, ANSSI).
- `marche-concurrents-et-prix` : typologie des concurrents, prix publics observés, positionnement du 490 € HT.
- `marche-tendances-ia-cyber-2026` : IA générative, omnibus AI Act, facturation électronique, NIS2, fraudes.
- `marche-aides-et-financements` : diagnostics Bpifrance, région, OPCO, France Num ; comment en parler honnêtement.

## 4. Prospection écrite (40-prospection)

`methode-email-froid` (structure, 3 exemples), `methode-sequences-relances` (relances, arrêt, réponses types), `methode-delivrabilite` (SPF/DKIM/DMARC, règles Google/Yahoo/Microsoft, échauffement), `methode-sources-donnees-entreprises` (API Recherche d'entreprises, Sirene, BODACC, annuaires, limites légales).

## 5. Droit (50-legal)

- `legal-prospection-b2b` : L34-5 CPCE, CNIL (page du 10 juin 2026), RGPD 6.1.f / 14 / 21, conservation 3 ans, scraping (sanction KASPR 240 000 €), checklist en 14 points, pied d'email type.
- `legal-obligations-clients-2026-2027` : obligations qui créent le besoin client, chacune avec « ce que ça change » et un argument écrit.

## 6. Fiche entreprise (60) et accès (70)

- `schema-fiche-entreprise` : 6 niveaux (identité, taille, présence en ligne, signaux, relation, score/prochaine action), score déterministe sur 90, minimisation, liste d'opposition, SQL prêt à ajouter dans `cortex.db`.
- `spec-acces-memoire` : lecture seule, FTS5, garde-fous secrets, 8 étapes d'intégration dans `cortex.py`, texte proposé pour AGENTS.md, 8 tests d'acceptation.

## Faits datés qui changent le discours (vérifiés au 2026-10-11)

- Facturation électronique : réception obligatoire pour toutes les entreprises depuis le 1er septembre 2026, émission pour PME et micro-entreprises au 1er septembre 2027 (`legal-obligations-clients-2026-2027`).
- NIS2 : **pas transposée** en France ; le projet de loi Résilience a été retiré de l'ordre du jour le 6 octobre 2026. Ne jamais écrire qu'une TPE est « soumise à NIS2 ».
- AI Act : omnibus (règlement UE 2026/1744) en vigueur le 27 juillet 2026 ; haut risque annexe III reporté au 2 décembre 2027 ; transparence art. 50 depuis le 2 août 2026.
- Prospection : décision du Conseil constitutionnel 2026-1210 QPC du 25 juin 2026 sur le cumul des sanctions L34-5 ; recommandation CNIL du 14 avril 2026 sur les pixels de suivi (aucun pixel dans nos emails).

## Limites connues (à compléter)

- Budgets, cycles de décision, saisonnalité : surtout des estimations, marquées comme telles.
- Non trouvés : part des TPE avec sauvegarde testée, coût moyen d'un incident pour une TPE (source primaire), parts de marché des logiciels métier, nombre exact d'entreprises 6-49 par secteur au niveau INSEE (remplacé par les comptages API).
- Légifrance n'a pas pu être lu depuis le cloud : plusieurs articles (L561-2 CMF, LCEN art. 20, montants L34-5) sont sourcés via des pages secondaires et marqués « non vérifié ».
- Le comptage 69.10Z mélange notaires et avocats ; les codes NAF 2025 commencent à apparaître (ex. 68.32H).
