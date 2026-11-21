# ROADMAP — `dku2dbx`, usine de migration Dataiku → Databricks

Ce plan découpe la construction en 11 phases (0 à 10). Chacune a un objectif, des tâches, des livrables et des critères de fin (« terminé quand… »). Claude Code doit les réaliser **dans l'ordre, une à la fois**, et s'arrêter à la fin de chaque phase pour validation humaine (voir `CLAUDE.md`).

Vue d'ensemble :

| Phase | Nom | Étape du parcours | Résultat |
|---|---|---|---|
| 0 | Socle du dépôt | — | Projet Python outillé, CI, fixtures |
| 1 | Lecteur d'export | Analyser | Export ZIP → modèle interne |
| 2 | Analyse et inventaire | Analyser | Rapport par projet et portefeuille, score, vagues |
| 3 | Recettes visuelles relationnelles | Migrer | Join, Group, Window… → Spark SQL testé |
| 4 | Recette Prepare et formules | Migrer | Registre de processeurs + traducteur de formules |
| 5 | Simplification du Flow | Simplifier | Chaînes de recettes fusionnées en étapes |
| 6 | Générateurs et bundle | Migrer | Notebooks SQL, pipeline, job, bundle déployable |
| 7 | Branchement des sources | Brancher | Sources Dataiku → tables Unity Catalog |
| 8 | Résidu assisté par LLM | Migrer | Recettes Python et cas non couverts, à relire |
| 9 | Réconciliation | Migrer | Preuve d'équivalence des sorties |
| 10 | Interface (optionnelle) | Tout | Databricks App au-dessus de la CLI |

**Hors périmètre de la v1 (inventoriés mais non convertis) :** modèles ML (Visual ML, saved models), API node, webapps, dashboards, plugins, recettes R/Shell/Scala, objets GenAI (LLM Mesh, Knowledge Banks, agents), Dataiku Govern. Ces objets sont comptés et classés `MANUAL` dans le rapport de la phase 2.

---

## Phase 0 — Socle du dépôt

**Objectif :** un projet Python propre, testable et outillé, avant toute logique métier.

Tâches :
1. Créer l'arborescence décrite dans `CLAUDE.md`, le `pyproject.toml` (dépendances listées dans `CLAUDE.md`), le `.gitignore` (`exports/`, `out/`, `.env`, `*.zip` hors `tests/fixtures/`) et la configuration `ruff`, `mypy` et `pre-commit`.
2. Créer une CLI `dku2dbx` (typer) avec des sous-commandes vides : `analyze`, `simplify`, `translate`, `generate`, `connect`, `reconcile`.
3. Écrire un **générateur de fixtures** (`tests/fixtures/make_fixture.py`) qui fabrique un faux export ZIP Dataiku conforme au format décrit dans `CLAUDE.md`. Il doit contenir 2 projets synthétiques :
   - `DEMO_SIMPLE` : 5 recettes (Prepare, Join, Group, Window, Stack), sans partition ;
   - `DEMO_COMPLEXE` : environ 20 recettes, dont un dataset partitionné par jour, une recette Python, une recette SQL, un scénario step-based et une recette de plugin.
4. Mettre en place la CI (GitLab CI ou GitHub Actions selon le dépôt) : `ruff`, `mypy` et `pytest`.
5. Créer `docs/journal.md`, `docs/hypotheses.md` et `docs/pieges_semantiques.md` (avec le contenu de la section « Pièges sémantiques » en fin de document).

Terminé quand : `uv run pytest` passe, `uv run dku2dbx --help` liste les commandes, la CI est verte et les deux fixtures ZIP sont générées.

---

## Phase 1 — Lecteur d'export → modèle interne

**Objectif :** transformer un export ZIP Dataiku en un modèle interne (IR) typé, indépendant du format Dataiku.

Tâches :
1. Définir le modèle pydantic dans `model/` : `Project`, `Zone`, `Dataset` (connexion, table résolue, partitionnement, schéma, checks), `Recipe` (type, moteur, entrées, sorties, mode append, payload brut et parsé), `PrepareStep`, `Scenario` (steps, triggers), `PluginUsage`, `ExposedObject`.
2. Écrire `reader/zip_reader.py` :
   - lire `export-manifest.json`, `params.json`, `datasets/*.json`, `recipes/*.json` et les payloads (`.shaker`, `.grouping`, `.join`…) ;
   - résoudre les variables (`${projectKey}`, `${NODE_DC}`, variables de projet) dans les noms de tables, et lister celles qui restent non résolues ;
   - construire le graphe du Flow (dataset → recette → dataset) avec `networkx` ;
   - conserver tout type inconnu tel quel, avec `status = UNKNOWN`, sans planter.
3. Prévoir un second lecteur, `reader/api_reader.py`, sur la même interface. Il utilisera l'API `dataikuapi` (`list_projects`, `get_flow().get_graph()`, `get_settings()`, `get_payload()`, `get_json_payload()`, `get_status().get_selected_engine_details()`). En phase 1, seule l'interface est définie ; l'implémentation viendra quand un accès API sera disponible.
4. Ajouter la commande `dku2dbx analyze <export.zip> --dump-ir`, qui écrit l'IR en JSON.

Terminé quand : les deux fixtures sont lues sans erreur, l'IR sérialisée est stable (snapshot), un test vérifie le graphe de `DEMO_SIMPLE` (nœuds, arêtes, ordre topologique) et un test vérifie qu'un type inconnu est conservé et signalé.

Si un vrai export La Poste est disponible dans `exports/`, le lire aussi. Chaque écart avec le format supposé est noté dans `docs/hypotheses.md` et une fixture est ajoutée pour le reproduire.

---

## Phase 2 — Analyse, inventaire, score et vagues

**Objectif :** produire, pour chaque projet et pour tout le portefeuille, la vue « Analyser » : ce qui se migre automatiquement, ce qui passe par le LLM, ce qui est manuel, et l'effort.

Tâches :
1. Compter les recettes par type, les datasets, les zones, les partitions, les scénarios, les plugins et les recettes de code.
2. **Catalogue des processeurs Prepare.** Scanner tous les `.shaker` de tous les exports et compter chaque `type` de processeur. Ce catalogue fixe l'ordre de développement de la phase 4 : on traite d'abord les processeurs les plus fréquents.
3. Classer chaque recette :
   - `AUTO` : traducteur déterministe disponible ;
   - `LLM_REVIEW` : le résidu passera par le LLM avec relecture ;
   - `MANUAL` : objets hors périmètre, plugins, R, ML.

   La classification se met à jour automatiquement à mesure que les traducteurs arrivent.
4. Calculer un score de complexité configurable (`config/scoring.yaml`), inspiré de la grille Lakebridge : 4 niveaux, de LOW à VERY HIGH, et un niveau est atteint dès qu'une seule de ses conditions est remplie. Critères : nombre de recettes, part de code, Prepare riches en formules, partitions, scénarios Python, plugins, webapps, modèles.
5. Estimer l'effort en jours, avec des coefficients par classe dans `scoring.yaml`, marqués « à calibrer sur le pilote ».
6. Construire le graphe entre projets (`exposedObjects` côté producteur, entrées préfixées `PROJET.dataset` côté consommateur) et proposer des **vagues** : composantes fortement connexes regroupées, producteurs avant consommateurs.
7. Produire les sorties :
   - `out/<projet>/analyse.md` et `analyse.json` ;
   - `out/portefeuille.csv` (une ligne par projet) et `out/vagues.md`.

Terminé quand : `dku2dbx analyze exports/ --out out/` produit tous ces fichiers pour les fixtures, les chiffres de `DEMO_SIMPLE` sont vérifiés par test et le catalogue des processeurs est généré.

---

## Phase 3 — Traducteurs des recettes visuelles relationnelles

**Objectif :** convertir de façon déterministe les recettes visuelles « SQL-friendly » en Spark SQL (dialecte Databricks).

Ordre : Sync/Filter → Distinct → Stack (`.vstack`) → Join → Group → Window → Split → Sort → Top N → Pivot.

Pour chaque recette :
1. Lire le payload parsé de l'IR et générer une requête `SELECT` (ou une CTE) formatée avec `sqlglot` (`dialect="databricks"`).
2. Gérer les `preFilter` et `postFilter`, les colonnes sélectionnées et les renommages.
3. Points d'attention :
   - **Join** : types de jointure, conditions multiples, options `caseInsensitive` et `normalizeText`, égalité des NULL ;
   - **Top N** : ajouter une colonne de départage pour rendre le résultat déterministe, et le signaler dans le rapport ;
   - **Pivot** : valeurs explicites ou dynamiques. Les valeurs dynamiques sont signalées, car elles exigent soit une liste figée, soit du code ;
   - **Split** : une requête par sortie, plus la sortie par défaut.
4. Tests pour chaque traducteur :
   - snapshot du SQL ;
   - exécution sur PySpark local avec un DataFrame synthétique, et comparaison avec un résultat attendu calculé à la main ;
   - cas d'erreur : une option non gérée lève `UnsupportedConstruct`.

Terminé quand : les 10 types sont couverts avec leurs tests, toutes les recettes relationnelles de `DEMO_SIMPLE` et `DEMO_COMPLEXE` sont traduites et la commande `dku2dbx translate` écrit un fichier `.sql` par recette dans `out/`.

---

## Phase 4 — Recette Prepare et langage de formules

**Objectif :** traduire les recettes Prepare, qui représentent souvent la moitié des recettes d'un projet (42 sur 86 dans un projet La Poste observé).

Tâches :
1. **Registre des processeurs** (`translate/prepare/registry.py`) : un traducteur par `type` de processeur, qui produit une expression Spark SQL ou une étape CTE. Traiter les processeurs dans l'ordre du catalogue de la phase 2. Les plus probables :
   - renommer, supprimer ou garder des colonnes ;
   - filtrer des lignes ;
   - `CreateColumnWithGREL` (formule) ;
   - `FillEmptyWithValue` ;
   - parser une date, découper une colonne, rechercher et remplacer, extraire par regex ;
   - changer la casse, normaliser ;
   - arrondir, convertir un type, concaténer des colonnes ;
   - fold/unfold.
2. **Traducteur de formules** (`translate/prepare/formula.py`) : une grammaire `lark` du langage de formules Dataiku (opérateurs, `if()`, fonctions de chaîne, de date et mathématiques, références de colonnes, variables `${...}`), puis la génération en Spark SQL. Une fonction inconnue lève `UnsupportedConstruct` ; ne jamais deviner.
3. Les steps `disabled: true` sont ignorées et listées dans le rapport. Un `metaType` autre que `PROCESSOR` (groupe de steps) lève une erreur tant qu'il n'est pas géré explicitement.
4. Les processeurs qui exigent un référentiel (GeoIP, User-Agent, jours fériés, enrichissement département/code postal) ou un calcul hors SQL sont classés `MANUAL`. Ils sont listés avec une proposition de cible : une UDF Unity Catalog ou un custom operator Lakeflow Designer.
5. Tests : un test par processeur et par fonction de formule. Les **pièges sémantiques** de la section finale ont chacun leur test dédié.

Terminé quand : les processeurs qui représentent au moins 80 % des occurrences du catalogue sont traduits et testés, chaque recette Prepare des fixtures est soit traduite, soit explicitement listée avec ses étapes non couvertes, et `docs/pieges_semantiques.md` est à jour.

---

## Phase 5 — Simplification du Flow

**Objectif :** reproduire l'étape « Simplifier ». On fusionne les chaînes de recettes pour ne matérialiser que les tables utiles (exemple observé : 86 recettes deviennent 25 étapes et 61 tables intermédiaires disparaissent).

Règles de fusion. **Une table reste matérialisée** si l'une de ces conditions est vraie :
- c'est une sortie finale ou un objet exposé à un autre projet ;
- elle est lue par plusieurs recettes ;
- elle est partitionnée ou écrite en mode append ;
- elle porte des checks ou des règles qualité, ou elle est lue par un scénario ;
- elle est l'entrée ou la sortie d'une recette `LLM_REVIEW` ou `MANUAL`.

Les autres tables deviennent des CTE ou des vues temporaires dans l'étape qui les consomme.

Tâches :
1. Implémenter l'algorithme sur le graphe de l'IR. Il produit des « étapes », chacune composée d'une séquence de recettes.
2. Ajouter une option `--no-fusion` (1 recette = 1 table), indispensable pour la réconciliation fine et le débogage.
3. Ajouter au rapport : nombre de recettes avant, nombre d'étapes après, tables supprimées et justification de chaque table conservée.

Terminé quand : les tests vérifient chaque règle de conservation sur des graphes construits à la main, la sortie de `DEMO_COMPLEXE` est vérifiée par snapshot et `--no-fusion` redonne une étape par recette.

---

## Phase 6 — Générateurs de code et bundle

**Objectif :** produire un projet Databricks déployable par projet Dataiku.

Deux cibles, à choisir par projet :
- **A. Job de notebooks SQL** : une tâche de préparation du schéma, puis un notebook SQL par étape, orchestrés dans un Lakeflow Job.
- **B. Lakeflow pipeline** : une table ou materialized view par étape, en SQL ou en Python (`from pyspark import pipelines as dp`). Les tables partitionnées ou en append passent par une tâche SQL séparée.

(Une cible C, Lakeflow Designer / « Visual Data Prep », est à étudier plus tard : le format de ses fichiers n'est pas documenté publiquement.)

Tâches :
1. Templates `jinja2` pour les notebooks SQL, les fichiers de pipeline, la définition du job et `databricks.yml` :
   - targets `dev` et `prod` ;
   - variables `catalog` et `schema` ;
   - permissions.
2. **Partitions** : une partition Dataiku devient une colonne de date et une écriture `INSERT INTO … REPLACE WHERE <colonne> = :date`. Le job reçoit un paramètre de date. Avec les références dynamiques (`{{job.start_time.iso_date}}`), **attention à l'UTC** : documenter le décalage avec l'heure de Paris. Les dépendances « Time range » deviennent des prédicats de plage ; « Latest available » est signalé pour revue.
3. **Scénarios step-based** : les steps « build » deviennent des tâches du job, les déclenchements temporels un `schedule`, et les déclenchements « dataset modifié » un trigger *table update*. Les scénarios Python et les triggers SQL ou Python personnalisés sont classés `MANUAL`.
4. **Variables de projet** → variables de bundle et paramètres de job. **Checks et règles qualité simples** → expectations de pipeline ou contrôles SQL ; les autres sont listés.
5. En-tête de traçabilité dans chaque fichier généré (voir `CLAUDE.md`).
6. Commande `dku2dbx generate <projet> --target job|pipeline --out out/<projet>/bundle/`.

Terminé quand : le bundle généré pour `DEMO_SIMPLE` passe `databricks bundle validate` (lancé en CI si un profil Databricks est disponible, sinon par une validation de schéma locale), le SQL généré parse avec `sqlglot` et un test de bout en bout exécute les étapes de `DEMO_SIMPLE` sur PySpark local.

---

## Phase 7 — Branchement des sources

**Objectif :** reproduire l'étape « Brancher » : chaque dataset source Dataiku doit pointer vers une table Unity Catalog.

Tâches :
1. `config/connections.yaml` associe chaque connexion Dataiku à un `catalog.schema` UC, avec des règles de renommage.
2. Résoudre automatiquement les noms de tables. Les sources non résolues apparaissent dans un rapport « à brancher » et sont marquées en pointillé dans le graphe.
3. Optionnel, si un accès Databricks est configuré : vérifier l'existence des tables via le SDK (`databricks-sdk`, `WorkspaceClient().tables.get`) et comparer leurs colonnes au schéma déclaré par Dataiku.
4. Les sources non branchées génèrent une tâche d'ingestion de substitution, signalée dans le rapport.

Terminé quand : les tests couvrent la résolution, les variables non résolues et une connexion inconnue ; le rapport « à brancher » est produit pour les fixtures.

---

## Phase 8 — Résidu assisté par LLM

**Objectif :** traiter ce que les traducteurs déterministes ne couvrent pas, avec relecture humaine obligatoire.

Prérequis bloquant : un endpoint Model Serving Databricks **validé par la sécurité** est renseigné dans `config/llm.yaml`. Sans lui, la phase se limite à préparer les fichiers d'entrée.

Tâches :
1. **Recettes Python** : d'abord une réécriture déterministe des idiomes, puis le LLM pour le reste.

   | Idiome Dataiku | Cible Databricks |
   |---|---|
   | `dataiku.Dataset("x").get_dataframe()` | `spark.table("catalog.schema.x")` (ou `.toPandas()` si nécessaire) |
   | `dataiku.Dataset("y").write_with_schema(df)` | `df.write.mode("overwrite").saveAsTable("catalog.schema.y")` |
   | `dataiku.Folder("f")` | chemin `/Volumes/catalog/schema/volume/` |
   | `dataiku.get_custom_variables()` | paramètres de job ou widgets |
   | `dataiku.api_client()` | `MANUAL` (cas par cas) |

2. Prompts versionnés dans `src/dku2dbx/translate/llm/prompts/`. Chaque entrée envoyée au LLM est un JSON enrichi : définition de la recette, payload, schémas d'entrée et tables UC résolues.
3. Chaque sortie LLM porte l'en-tête `REVIEW_REQUIRED`. Elle est vérifiée statiquement (`ruff`, parse `sqlglot`) et n'est jamais classée `AUTO`.
4. Option alternative : exporter ces entrées au format attendu par **Lakebridge Switch** (prompt YAML personnalisé) au lieu d'appeler le LLM directement.

Terminé quand : la recette Python de `DEMO_COMPLEXE` est réécrite par les règles déterministes et testée, le flux LLM fonctionne avec un endpoint de test (ou un faux client dans les tests) et le rapport liste chaque fichier à relire.

---

## Phase 9 — Réconciliation

**Objectif :** prouver que les sorties Databricks sont identiques à celles de Dataiku, ou expliquer chaque écart.

Hypothèse de travail : les sorties Dataiku sont accessibles dans Unity Catalog (re-plateformage de Dataiku sur Databricks, ou copie des tables de sortie).

Tâches :
1. Générer, par projet, un notebook ou job de réconciliation qui compare chaque table de sortie en couches :
   1. schéma (colonnes, types, nullabilité) ;
   2. nombre de lignes, au total et par partition ;
   3. agrégats métier par colonne (somme, min, max, distincts), avec tolérances configurables ;
   4. comparaison ligne à ligne sur clé métier (`EXCEPT ALL` dans les deux sens, ou hash par ligne), et `datacompy` en option ;
2. Produire un rapport de réconciliation (Markdown et table Delta) avec statut par table : `IDENTIQUE`, `ÉCART TOLÉRÉ` ou `ÉCART`.
3. Fournir un gabarit de **registre des écarts acceptés** (décision métier : corriger, ou reproduire l'ancien comportement).

Terminé quand : les tests couvrent chaque couche avec des DataFrames construits pour être identiques, légèrement différents (dans et hors tolérance) ou complètement différents, et le notebook généré s'exécute sur PySpark local.

---

## Phase 10 — Interface (optionnelle, après validation du pilote)

**Objectif :** offrir aux équipes une interface simple au-dessus de la CLI, sous forme de **Databricks App** (Streamlit ou Dash).

Parcours : déposer un export ZIP → Analyser → Simplifier → Brancher → Migrer (générer, télécharger ou déployer le bundle) → Réconcilier. L'app s'authentifie avec son service principal ou avec l'identité de l'utilisateur. Les exports sont stockés dans un Volume Unity Catalog à accès restreint.

Terminé quand : l'app est déployée en `dev` via le bundle du projet et le parcours complet fonctionne sur `DEMO_SIMPLE`.

---

## Pilote et passage à l'échelle (après la phase 9)

1. Choisir 2 ou 3 projets réels représentatifs avec l'équipe : un petit projet visuel, un gros projet Prepare, un projet avec partitions et scénario.
2. Les dérouler de bout en bout, en run parallèle avec Dataiku, jusqu'à réconciliation signée par le métier.
3. Calibrer `scoring.yaml` (jours réels par classe de recette) et compléter le registre des processeurs.
4. Seulement ensuite, lancer les vagues de la phase 2.

---

## Pièges sémantiques à couvrir par des tests

Chacun de ces points doit avoir au moins un test et une règle dans le traducteur concerné.

| Piège | Dataiku | Databricks / Spark | Règle |
|---|---|---|---|
| Chaîne vide et NULL | `isBlank`, `FillEmptyWithValue` et `coalesce` traitent `''` comme vide | `coalesce` ne remplace que NULL | Générer `coalesce(nullif(trim(col), ''), valeur)` ou l'équivalent |
| Arrondi des négatifs | Documenté : `round(-3.5) = -3` | `round` en HALF_UP, probablement `-4` | Tester, puis générer une expression qui reproduit Dataiku |
| Concaténation avec `+` | Concatène des chaînes (moteur DSS) | Addition numérique | Traduire en `concat()` selon le type |
| Dates et fuseau | Dates locales selon la configuration | Références de job en UTC | Paramètre de date explicite, documenter le décalage avec Paris |
| Patterns de date | — | `MM` = mois, `mm` = minutes | Table de conversion des formats testée |
| Fuzzy join | Damerau-Levenshtein (transposition = 1) | `levenshtein` simple (transposition = 2) | Classer `LLM_REVIEW` ou `MANUAL`, recalibrer les seuils |
| Top N à égalité | Ordre non déterministe | Idem | Ajouter une colonne de départage |
| Distances géographiques | — | `st_distance` est planaire (degrés) | Utiliser `st_distancesphere` pour des mètres |
| Typage | « Meanings » et inférence Dataiku | Types Spark stricts | Utiliser le schéma déclaré dans l'export, avec un `cast` explicite |
| Steps Prepare groupées | `metaType` différent de `PROCESSOR` | — | Lever une erreur, ne jamais filtrer en silence |
| Variables dans les noms de tables | `${projectKey}`, `${NODE_DC}` | — | Résoudre, sinon signaler |

---

## Prérequis à obtenir avant ou pendant le projet

- **Exports Dataiku** : qui peut exporter les projets (export ZIP « configuration seulement ») ? Quels projets pour le pilote ? Où les stocker de façon sécurisée ?
- **Databricks** : un workspace de dev avec un catalogue bac à sable Unity Catalog, un SQL warehouse et un profil CLI pour `databricks bundle validate` et `deploy`.
- **LLM** : un endpoint Model Serving validé par la sécurité. Les exports contiennent la logique métier et les noms de tables.
- **Dépôt Git** de l'organisation et accès à la CI.
- **Databricks** : demander si le prototype « Dataiku Sunset » présenté le 10/11/2026 peut être partagé ou réutilisé, pour éviter de refaire ce qui existe.
