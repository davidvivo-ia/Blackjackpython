"""Typer CLI for blackjack21."""

from __future__ import annotations

import sys
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from blackjack21 import __version__
from blackjack21.infrastructure.paths import session_path
from blackjack21.infrastructure.persistence import JsonSessionStore
from blackjack21.presentation.demo import DEFAULT_HANDS, run_demo
from blackjack21.presentation.theme import build_theme
from blackjack21.presentation.tui import BlackjackApp

app = typer.Typer(
    name="blackjack21",
    help="Modern Python reinterpretation of Ahl's 1978 Black Jack.",
    no_args_is_help=False,
    add_completion=False,
    invoke_without_command=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"blackjack21 {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Root callback. Required so ``--version`` works without a sub-command."""
    del version  # consumed by the callback above


@app.command()
def play(
    seed: Annotated[
        int | None,
        typer.Option(help="Seed for the shuffler (omit for system randomness)."),
    ] = None,
    demo: Annotated[
        bool,
        typer.Option(
            "--demo",
            help="Run a deterministic non-interactive demo session and exit.",
        ),
    ] = False,
    hands: Annotated[
        int,
        typer.Option(min=1, max=50, help="Number of hands to play in --demo mode."),
    ] = DEFAULT_HANDS,
    ascii_only: Annotated[
        bool,
        typer.Option(
            "--ascii",
            help="Use plain S/H/D/C letters instead of ♠♥♦♣ glyphs (legacy fonts).",
        ),
    ] = False,
) -> None:
    """Play blackjack: interactive TUI by default, ``--demo`` for headless."""
    if demo:
        effective_seed = seed if seed is not None else 42
        run_demo(seed=effective_seed, hands=hands)
        return
    BlackjackApp(seed=seed, ascii_only=ascii_only).run()


@app.command()
def reset() -> None:
    """Delete the saved bankroll and stats."""
    store = JsonSessionStore()
    store.reset()
    typer.echo("Session reset.")


@app.command()
def doctor() -> None:
    """Diagnose the terminal environment."""
    console = Console(theme=build_theme())
    table = Table(title="blackjack21 doctor", border_style="cyan")
    table.add_column("Check")
    table.add_column("Value")
    table.add_row("python", sys.version.split()[0])
    table.add_row("blackjack21", __version__)
    table.add_row("color system", str(console.color_system))
    table.add_row("encoding", console.encoding)
    table.add_row("size", f"{console.width}x{console.height}")
    table.add_row("legacy_windows", str(console.legacy_windows))
    table.add_row("session path", str(session_path()))
    console.print(table)


if __name__ == "__main__":
    app()
