"""Typer CLI entry point (placeholder during scaffolding)."""

from __future__ import annotations

import typer

app = typer.Typer(
    name="blackjack21",
    help="Modern Python reinterpretation of Ahl's 1978 Black Jack.",
    no_args_is_help=True,
)


@app.command()
def play() -> None:
    """Placeholder play command — replaced in phase 7."""
    typer.echo("blackjack21 not implemented yet")
