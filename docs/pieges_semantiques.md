# Pièges sémantiques Dataiku → Databricks

Repris de la section « Pièges sémantiques » de `ROADMAP.md`. Chaque piège doit avoir **au moins un test** et une règle dans le traducteur concerné. La colonne « Test » sera remplie au fil des phases.

| Piège | Dataiku | Databricks / Spark | Règle | Phase | Test |
|---|---|---|---|---|---|
| Chaîne vide et NULL | `isBlank`, `FillEmptyWithValue` et `coalesce` traitent `''` comme vide | `coalesce` ne remplace que NULL | Générer `coalesce(nullif(trim(col), ''), valeur)` ou l'équivalent | 4 | à faire |
| Arrondi des négatifs | Documenté : `round(-3.5) = -3` | `round` en HALF_UP, probablement `-4` | Tester, puis générer une expression qui reproduit Dataiku | 4 | à faire |
| Concaténation avec `+` | Concatène des chaînes (moteur DSS) | Addition numérique | Traduire en `concat()` selon le type | 4 | à faire |
| Dates et fuseau | Dates locales selon la configuration | Références de job en UTC | Paramètre de date explicite, documenter le décalage avec Paris | 6 | à faire |
| Patterns de date | — | `MM` = mois, `mm` = minutes | Table de conversion des formats testée | 4 | à faire |
| Fuzzy join | Damerau-Levenshtein (transposition = 1) | `levenshtein` simple (transposition = 2) | Classer `LLM_REVIEW` ou `MANUAL`, recalibrer les seuils | 3 | à faire |
| Top N à égalité | Ordre non déterministe | Idem | Ajouter une colonne de départage | 3 | à faire |
| Distances géographiques | — | `st_distance` est planaire (degrés) | Utiliser `st_distancesphere` pour des mètres | 4 | à faire |
| Typage | « Meanings » et inférence Dataiku | Types Spark stricts | Utiliser le schéma déclaré dans l'export, avec un `cast` explicite | 3–4 | à faire |
| Steps Prepare groupées | `metaType` différent de `PROCESSOR` | — | Lever une erreur, ne jamais filtrer en silence | 4 | à faire (fixture prête : `DEMO_COMPLEXE/prepare_events`) |
| Variables dans les noms de tables | `${projectKey}`, `${NODE_DC}` | — | Résoudre, sinon signaler | 1 | à faire (fixture prête : `DEMO_COMPLEXE/parcels_events`) |
