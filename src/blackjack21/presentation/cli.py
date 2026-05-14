"""Typer CLI for blackjack21."""

from __future__ import annotations

import sys
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from blackjack21 import __version__
from blackjack21.application.achievements import ACHIEVEMENTS, by_id
from blackjack21.domain.rules import GameRules
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
    decks: Annotated[
        int,
        typer.Option(
            min=1,
            max=8,
            help="Decks in the shoe (1, 2, 4, 6, 8). Multi-deck triggers"
            " standard 75% penetration reshuffle.",
        ),
    ] = 1,
    h17: Annotated[
        bool,
        typer.Option(
            "--h17/--s17",
            help="Dealer hits soft 17 (H17) vs stands on soft 17 (S17, default).",
        ),
    ] = False,
    no_surrender: Annotated[
        bool,
        typer.Option(
            "--no-surrender",
            help="Disable late surrender (the BASIC original had none).",
        ),
    ] = False,
    theme: Annotated[
        str,
        typer.Option(
            "--theme",
            help="Visual theme: premiere (default), phosphor, midnight, ruby.",
        ),
    ] = "premiere",
    profile: Annotated[
        str,
        typer.Option(
            "--profile",
            help="Session profile name. 'default' uses the legacy session.json.",
        ),
    ] = "default",
) -> None:
    """Play blackjack: interactive TUI by default, ``--demo`` for headless."""
    if demo:
        effective_seed = seed if seed is not None else 42
        run_demo(seed=effective_seed, hands=hands)
        return
    rules = GameRules(
        num_decks=decks,
        dealer_hits_soft_17=h17,
        allow_surrender=not no_surrender,
    )
    BlackjackApp(
        seed=seed,
        store=JsonSessionStore(session_path(profile)),
        ascii_only=ascii_only,
        rules=rules,
        theme_name=theme,
    ).run()


@app.command()
def reset(
    profile: Annotated[
        str,
        typer.Option("--profile", help="Profile whose session.json to delete."),
    ] = "default",
) -> None:
    """Delete the saved bankroll and stats for ``profile``."""
    store = JsonSessionStore(session_path(profile))
    store.reset()
    typer.echo(f"Session reset for profile '{profile}'.")


@app.command()
def scores(
    profile: Annotated[
        str,
        typer.Option("--profile", help="Profile to read stats from."),
    ] = "default",
) -> None:
    """Show the current profile's lifetime stats and unlocked achievements."""
    console = Console(theme=build_theme())
    store = JsonSessionStore(session_path(profile))
    try:
        saved = store.load()
    except Exception as exc:
        console.print(f"[danger]Could not load profile '{profile}': {exc}[/]")
        raise typer.Exit(code=1) from exc
    if saved is None:
        console.print(f"[muted]No session yet for profile '{profile}'.[/]")
        return
    stats_table = Table(
        title=f"[bold accent]HALL OF FAME — {profile}[/]",
        border_style="accent",
        show_header=False,
        expand=False,
    )
    stats_table.add_column("key", style="#A88729")
    stats_table.add_column("value", style="#E5E2E1", justify="right")
    stats_table.add_row("bankroll", f"${saved.bankroll:,}")
    stats_table.add_row("hands played", str(saved.stats.hands_played))
    stats_table.add_row("blackjacks", str(saved.stats.blackjacks))
    stats_table.add_row("biggest pot", f"${saved.stats.biggest_pot:,}")
    stats_table.add_row(
        "longest win streak", str(saved.stats.longest_win_streak)
    )
    stats_table.add_row(
        "max bankroll reached", f"${saved.stats.max_bankroll_reached:,}"
    )
    stats_table.add_row(
        "lowest bankroll",
        f"${saved.stats.lowest_bankroll:,}"
        if saved.stats.lowest_bankroll is not None
        else "—",
    )
    stats_table.add_row("times bet max", str(saved.stats.times_bet_max))
    console.print(stats_table)

    ach_table = Table(
        title="[bold accent]ACHIEVEMENTS[/]",
        border_style="accent",
        expand=False,
    )
    ach_table.add_column("✓", width=3)
    ach_table.add_column("name", style="#E5E2E1")
    ach_table.add_column("description", style="#A88729")
    unlocked = set(saved.unlocked_achievements)
    for ach in ACHIEVEMENTS:
        mark = "[bold accent]★[/]" if ach.id in unlocked else "[muted]·[/]"
        ach_table.add_row(mark, ach.name, ach.description)
    # Surface any persisted ids that the build no longer recognises so
    # they don't silently disappear from the user's record.
    for stale in sorted(unlocked - {a.id for a in ACHIEVEMENTS}):
        if by_id(stale) is None:
            ach_table.add_row(
                "[bold danger]?[/]", stale, "[muted]unknown achievement id[/]"
            )
    console.print(ach_table)


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
