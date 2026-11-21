# dku2dbx

Usine de migration de projets Dataiku DSS vers Databricks (Unity Catalog, Lakeflow Jobs, Lakeflow pipelines).
Le contexte et les règles sont dans [`CLAUDE.md`](CLAUDE.md), le plan dans [`ROADMAP.md`](ROADMAP.md) et l'avancement dans [`docs/journal.md`](docs/journal.md).

## Démarrage

Prérequis : [uv](https://docs.astral.sh/uv/). Java 17+ est aussi nécessaire pour les tests PySpark locaux.

```bash
uv sync                                         # crée .venv et installe les dépendances (uv.lock)
uv run pre-commit install                       # installe les hooks Git
uv run dku2dbx --help                           # CLI
uv run dku2dbx analyze export.zip --dump-ir     # écrit out/<projet>/ir.json (modèle interne)
uv run python tests/fixtures/make_fixture.py    # régénère les exports synthétiques
uv run pytest                                   # tests
uv run ruff check . && uv run ruff format --check . && uv run mypy
```

Les exports réels vont dans `exports/` et les artefacts générés dans `out/`. Ces deux dossiers sont ignorés par Git.
