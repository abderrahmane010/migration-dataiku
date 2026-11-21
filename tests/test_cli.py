"""Phase 0: the CLI exposes the six placeholder commands."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from dku2dbx import __version__
from dku2dbx.cli import NOT_IMPLEMENTED_EXIT_CODE, app

runner = CliRunner()

COMMANDS = ["analyze", "simplify", "translate", "generate", "connect", "reconcile"]


def test_help_lists_all_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in COMMANDS:
        assert command in result.output


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


@pytest.mark.parametrize("command", COMMANDS)
def test_placeholder_commands_fail_explicitly(command: str) -> None:
    """An empty command must never look like a successful run."""
    result = runner.invoke(app, [command])
    assert result.exit_code == NOT_IMPLEMENTED_EXIT_CODE
    assert "pas encore implémentée" in result.output
