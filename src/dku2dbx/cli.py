"""Command-line entry point for dku2dbx.

Phase 0: every sub-command is a placeholder. It prints which roadmap phase will
implement it and exits with a non-zero code, so that no caller mistakes an empty
command for a successful run.
"""

from __future__ import annotations

import typer

from dku2dbx import __version__

app = typer.Typer(
    name="dku2dbx",
    help="Usine de migration Dataiku DSS → Databricks (Analyser → Simplifier → Brancher → Migrer).",
    no_args_is_help=True,
    add_completion=False,
)

NOT_IMPLEMENTED_EXIT_CODE = 2


def _not_implemented(command: str, phase: int) -> None:
    typer.echo(f"`{command}` n'est pas encore implémentée (prévue en phase {phase}).", err=True)
    raise typer.Exit(code=NOT_IMPLEMENTED_EXIT_CODE)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"dku2dbx {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Affiche la version et quitte.",
    ),
) -> None:
    """Usine de migration Dataiku DSS → Databricks."""


@app.command()
def analyze() -> None:
    """Analyser : lire les exports et produire inventaire, score et vagues (phases 1-2)."""
    _not_implemented("analyze", 1)


@app.command()
def simplify() -> None:
    """Simplifier : fusionner les chaînes de recettes en étapes (phase 5)."""
    _not_implemented("simplify", 5)


@app.command()
def translate() -> None:
    """Migrer : traduire les recettes en Spark SQL (phases 3-4)."""
    _not_implemented("translate", 3)


@app.command()
def generate() -> None:
    """Migrer : générer notebooks, pipelines, jobs et bundle (phase 6)."""
    _not_implemented("generate", 6)


@app.command()
def connect() -> None:
    """Brancher : associer les sources Dataiku aux tables Unity Catalog (phase 7)."""
    _not_implemented("connect", 7)


@app.command()
def reconcile() -> None:
    """Réconcilier : comparer les sorties Dataiku et Databricks (phase 9)."""
    _not_implemented("reconcile", 9)


if __name__ == "__main__":  # pragma: no cover
    app()
