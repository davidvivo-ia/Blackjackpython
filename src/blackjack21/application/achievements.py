"""Local achievements unlocked from session-wide stats.

A list of seven simple predicates that fire on the totals tracked by
``SessionStats`` plus the current bankroll. Each achievement has a
stable ``id`` (persisted) and a human-readable name.

Achievements are evaluated **after** each settled round in the TUI;
the TUI compares newly-unlocked ids to the already-persisted set and
surfaces any deltas as a toast in the message bar.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from blackjack21.application.session import SessionStats


@dataclass(frozen=True, slots=True)
class Achievement:
    """One unlockable accolade."""

    id: str
    name: str
    description: str
    predicate: Callable[[SessionStats, int], bool]


def _first_bj(stats: SessionStats, bankroll: int) -> bool:
    del bankroll
    return stats.blackjacks >= 1


def _streak_5(stats: SessionStats, bankroll: int) -> bool:
    del bankroll
    return stats.longest_win_streak >= 5


def _comeback(stats: SessionStats, bankroll: int) -> bool:
    if stats.lowest_bankroll is None:
        return False
    return stats.lowest_bankroll < 200 and bankroll >= 1000


def _whale(stats: SessionStats, bankroll: int) -> bool:
    del bankroll
    return stats.times_bet_max >= 10


def _marathon(stats: SessionStats, bankroll: int) -> bool:
    del bankroll
    return stats.hands_played >= 100


def _big_pot(stats: SessionStats, bankroll: int) -> bool:
    del bankroll
    return stats.biggest_pot >= 500


def _high_roller(stats: SessionStats, bankroll: int) -> bool:
    del bankroll
    return stats.max_bankroll_reached >= 5000


ACHIEVEMENTS: tuple[Achievement, ...] = (
    Achievement(
        "first_bj",
        "First Blackjack",
        "Land your first natural 21.",
        _first_bj,
    ),
    Achievement(
        "streak_5",
        "Hot Hand",
        "Win five hands in a row.",
        _streak_5,
    ),
    Achievement(
        "comeback",
        "Phoenix",
        "Dip below $200 and climb back to $1,000.",
        _comeback,
    ),
    Achievement(
        "whale",
        "Whale",
        "Bet the table max ten times.",
        _whale,
    ),
    Achievement(
        "marathon",
        "Marathon",
        "Play one hundred hands in a session.",
        _marathon,
    ),
    Achievement(
        "big_pot",
        "Big Pot",
        "Net at least $500 on a single hand.",
        _big_pot,
    ),
    Achievement(
        "high_roller",
        "High Roller",
        "Reach a bankroll of $5,000.",
        _high_roller,
    ),
)

_BY_ID: dict[str, Achievement] = {a.id: a for a in ACHIEVEMENTS}


def by_id(achievement_id: str) -> Achievement | None:
    """Return the :class:`Achievement` with the given id, or ``None``."""
    return _BY_ID.get(achievement_id)


def evaluate(
    stats: SessionStats, bankroll: int, already_unlocked: set[str]
) -> set[str]:
    """Return the ids of achievements unlocked *now* but not before.

    Pure function: callers persist the new set themselves.
    """
    return {
        a.id
        for a in ACHIEVEMENTS
        if a.id not in already_unlocked and a.predicate(stats, bankroll)
    }
