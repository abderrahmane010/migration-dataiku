"""CLI: the six sub-commands exist; `analyze --dump-ir` writes the IR (phase 1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dku2dbx import __version__
from dku2dbx.cli import NOT_IMPLEMENTED_EXIT_CODE, app
from tests.fixtures.make_fixture import DEFAULT_OUT_DIR

runner = CliRunner()

COMMANDS = ["analyze", "simplify", "translate", "generate", "connect", "reconcile"]
PLACEHOLDERS = ["simplify", "translate", "generate", "connect", "reconcile"]


def test_help_lists_all_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in COMMANDS:
        assert command in result.output


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


@pytest.mark.parametrize("command", PLACEHOLDERS)
def test_placeholder_commands_fail_explicitly(command: str) -> None:
    """An empty command must never look like a successful run."""
    result = runner.invoke(app, [command])
    assert result.exit_code == NOT_IMPLEMENTED_EXIT_CODE
    assert "pas encore implémentée" in result.output


def test_analyze_dump_ir(tmp_path: Path) -> None:
    export = DEFAULT_OUT_DIR / "DEMO_COMPLEXE.zip"
    result = runner.invoke(app, ["analyze", str(export), "--dump-ir", "--out", str(tmp_path)])
    assert result.exit_code == 0, result.output
    target = tmp_path / "DEMO_COMPLEXE" / "ir.json"
    assert f"IR écrite dans {target}" in result.output
    assert "UNRESOLVED_VARIABLE : 1" in result.output
    doc = json.loads(target.read_text(encoding="utf-8"))
    assert doc["meta"]["source_file"] == "DEMO_COMPLEXE.zip"
    assert doc["project"]["key"] == "DEMO_COMPLEXE"
    assert len(doc["project"]["recipes"]) == 20


def test_analyze_dump_ir_is_byte_reproducible(tmp_path: Path) -> None:
    export = str(DEFAULT_OUT_DIR / "DEMO_SIMPLE.zip")
    for run in ("a", "b"):
        runner.invoke(app, ["analyze", export, "--dump-ir", "--out", str(tmp_path / run)])
    first = (tmp_path / "a" / "DEMO_SIMPLE" / "ir.json").read_bytes()
    assert first == (tmp_path / "b" / "DEMO_SIMPLE" / "ir.json").read_bytes()


def test_analyze_without_dump_ir_is_phase_2() -> None:
    result = runner.invoke(app, ["analyze", str(DEFAULT_OUT_DIR / "DEMO_SIMPLE.zip")])
    assert result.exit_code == NOT_IMPLEMENTED_EXIT_CODE
    assert "phase 2" in result.output


def test_analyze_unreadable_export(tmp_path: Path) -> None:
    bad = tmp_path / "bad.zip"
    bad.write_text("nope")
    result = runner.invoke(app, ["analyze", str(bad), "--dump-ir", "--out", str(tmp_path)])
    assert result.exit_code == 1
    assert "Erreur de lecture" in result.output
