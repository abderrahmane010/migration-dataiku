"""Command-line entry point for dku2dbx.

Sub-commands not implemented yet are placeholders: they print which roadmap
phase will implement them and exit with a non-zero code, so that no caller
mistakes an empty command for a successful run.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import typer

from dku2dbx import __version__
from dku2dbx.errors import ExportReadError
from dku2dbx.reader.zip_reader import ZipExportReader

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
def analyze(
    export: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        help="Export ZIP d'un projet Dataiku (configuration seulement).",
    ),
    dump_ir: bool = typer.Option(
        False, "--dump-ir", help="Écrire le modèle interne (IR) en JSON : <out>/<projet>/ir.json."
    ),
    out: Path = typer.Option(Path("out"), "--out", help="Dossier de sortie."),
) -> None:
    """Analyser : lire les exports et produire inventaire, score et vagues (phases 1-2)."""
    if not dump_ir:
        # Inventory, score and waves come with phase 2; only --dump-ir exists so far.
        _not_implemented("analyze sans --dump-ir", 2)
    try:
        doc = ZipExportReader(export).read_document()
    except ExportReadError as exc:
        typer.echo(f"Erreur de lecture : {exc}", err=True)
        raise typer.Exit(code=1) from exc

    project = doc.project
    target = out / project.key / "ir.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(doc.to_json().encode("utf-8"))

    typer.echo(
        f"Projet {project.key} : {len(project.datasets)} datasets, "
        f"{len(project.recipes)} recettes, {len(project.scenarios)} scénario(s)."
    )
    if project.issues:
        counts = Counter(issue.kind.value for issue in project.issues)
        typer.echo(f"{len(project.issues)} point(s) à examiner :")
        for kind, count in sorted(counts.items()):
            typer.echo(f"  - {kind} : {count}")
    typer.echo(f"IR écrite dans {target}")


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
