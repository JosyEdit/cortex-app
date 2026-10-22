# Ajout proposé à AGENTS.md (à valider par JOSY, I13)

Rien n'est appliqué tant que JOSY n'a pas validé. Pour l'appliquer : coller le bloc
ci-dessous dans AGENTS.md, juste avant « ## Format de réponse (obligatoire) ».

---

## Mémoire du Cortex

Le message peut contenir un bloc « MÉMOIRE DU CORTEX ». Ce sont des connaissances
validées par JOSY sur les secteurs, les dirigeants, le marché, les méthodes et le
droit. Utilise-les pour choisir la cible, l'angle, l'accroche et la réponse aux
objections. Cite chaque passage utilisé dans `"memoire"` avec son identifiant exact
(`memoire:fiche#section`). Un chiffre tiré de la mémoire n'est repris dans un contenu
que s'il porte un renvoi `[Sx]` ; ce qui est marqué « estimation » ou « non vérifié »
ne va jamais dans un contenu destiné à un prospect. La mémoire ne remplace pas les
sources d'actualité : au moins une source par proposition vient de la liste d'articles.

## Niveau 2 (Visibilité, Relation client, Monétisation)

Pour ces missions, avant les propositions, ajoute au JSON :
- `"analyse"` : 3 phrases (situation, ce que disent les sources et la mémoire) ;
- `"options"` : 2 ou 3 objets `{"option", "avantages", "risques"}` ;
- `"recommandation"` : 1 phrase, l'option retenue et pourquoi, en tenant compte des
  décisions passées de JOSY (validations, refus et motifs) fournies dans le message.

Une recommandation n'est jamais une action : chaque proposition reste soumise au
contrôle judiciaire et à la validation de JOSY. Le Cortex ne lit ni n'envoie aucun
email lui-même.

Format de proposition : ajouter le champ facultatif
`"memoire": ["memoire:fiche#section"]`.
