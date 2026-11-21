# Journal du projet dku2dbx

Une entrée par phase de `ROADMAP.md`, rédigée à la fin de la phase, avant la validation humaine.

---

## Phase 0 — Socle du dépôt (2026-11-21)

**Statut :** terminée côté développement, **en attente de validation humaine**.

### Décisions prises avec le responsable

| Sujet | Décision |
|---|---|
| Installation de uv | Installeur officiel (`~/.local/bin/uv`, version 0.13.9) |
| Version de Python | 3.12 géré par uv (`.python-version`) ; `requires-python >= 3.11` ; CI en 3.11 et 3.12 |
| Plateforme de CI | GitHub Actions (`.github/workflows/ci.yml`) |
| Git | `git init` local sur la branche `main` ; commits Conventional Commits ; aucun remote |

### Réalisé

- Arborescence de `CLAUDE.md` : les packages `src/dku2dbx/*` sont vides, `config/` contient des squelettes, et `templates/`, `exports/` et `out/` existent.
- `pyproject.toml` avec les dépendances de `CLAUDE.md` et `uv.lock`. Configuration de `ruff` (lint et format), `mypy --strict` sur `src/` et `pytest`. Le marqueur `spark` est déclaré.
- CLI `dku2dbx` (typer) avec 6 sous-commandes vides. Chacune quitte avec le **code 2** et le message « pas encore implémentée (phase N) », pour qu'une commande vide ne passe jamais pour un succès.
- `tests/fixtures/make_fixture.py` génère deux exports ZIP synthétiques et reproductibles octet pour octet : entrées triées, date fixe, permissions fixes, aucune compression, JSON canonique.
  - `DEMO_SIMPLE` : 5 recettes (Prepare, Stack, Join, Group, Window), 8 datasets, aucune partition, une step Prepare désactivée. Expose `customer_stats`.
  - `DEMO_COMPLEXE` : 20 recettes de 14 types et 26 datasets, dont `parcels_events` partitionné par jour avec `${NODE_DC}` dans le nom de table. Il contient aussi :
    - une recette Python (idiomes `dataiku.*`) et une recette SQL ;
    - un plugin (`CustomCode_geo-toolkit-geocode`) ;
    - un scénario step-based `DAILY_BUILD` (trigger temporel et trigger dataset) ;
    - une step groupée (`metaType: GROUP`) ;
    - un processeur de référentiel (`ZipCodeGeocoder`) ;
    - une sortie en append et un check de dataset ;
    - 2 zones de Flow et la lecture du dataset partagé `DEMO_SIMPLE.customer_stats`.
- Les 25 hypothèses de format (H-01 à H-17, sous-hypothèses comprises) sont marquées `# ASSUMPTION` dans le générateur et listées dans `docs/hypotheses.md`.
- `docs/pieges_semantiques.md` reprend le tableau de la roadmap, avec une colonne de suivi des tests.
- La CI GitHub Actions lance `ruff check`, `ruff format --check`, `mypy`, la vérification que les fixtures sont à jour, `pytest` (avec Java 17 pour PySpark) et `dku2dbx --help`.
- `pre-commit` : hooks d'hygiène (espaces en fin de ligne, YAML et TOML valides, gros fichiers, clés privées), plus `ruff` et `mypy` lancés via `uv run`.

### Résultats

- `uv run pytest` : 24 tests passés et 1 sauté. Le test sauté vérifie PySpark local et ne peut pas tourner sans Java ici. Résultat identique sous Python 3.11.
- `ruff check`, `ruff format --check` et `mypy --strict` : propres.
- `uv run dku2dbx --help` liste les 6 commandes.

### Points ouverts

- **Java absent du poste** : le test PySpark local est sauté. Java 17+ sera indispensable dès la phase 3. En CI, Java est installé et le test s'exécute.
- **CI non encore exécutée** : aucun remote GitHub n'est configuré. La CI ne sera « verte » qu'après le premier push.
- Toutes les hypothèses de format sont `SUPPOSÉE` tant qu'aucun vrai export n'est disponible.
