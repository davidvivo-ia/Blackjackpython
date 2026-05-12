"""CLI smoke tests using Typer's runner."""

from __future__ import annotations

from typer.testing import CliRunner

from blackjack21 import __version__
from blackjack21.presentation.cli import app


def test_version_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_demo_command_runs() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["play", "--demo", "--seed", "42", "--hands", "2"])
    assert result.exit_code == 0
    assert "BLACKJACK 21" in result.stdout
    assert "Demo Summary" in result.stdout


def test_doctor_command_runs() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "blackjack21" in result.stdout


def test_reset_command_runs(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(app, ["reset"])
    assert result.exit_code == 0
    assert "reset" in result.stdout.lower()
