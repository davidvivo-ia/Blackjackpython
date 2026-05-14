"""Achievement-predicate unit tests."""

from __future__ import annotations

from blackjack21.application.achievements import ACHIEVEMENTS, by_id, evaluate
from blackjack21.application.session import SessionStats


def _stats(**overrides: object) -> SessionStats:
    return SessionStats(**overrides)


def test_seven_achievements_are_defined() -> None:
    assert len({a.id for a in ACHIEVEMENTS}) == 7


def test_first_bj_unlocks_on_first_blackjack() -> None:
    locked = evaluate(_stats(blackjacks=0), bankroll=1000, already_unlocked=set())
    assert "first_bj" not in locked
    unlocked = evaluate(_stats(blackjacks=1), bankroll=1000, already_unlocked=set())
    assert "first_bj" in unlocked


def test_streak_5_needs_five_in_a_row() -> None:
    assert "streak_5" not in evaluate(
        _stats(longest_win_streak=4), bankroll=1000, already_unlocked=set()
    )
    assert "streak_5" in evaluate(
        _stats(longest_win_streak=5), bankroll=1000, already_unlocked=set()
    )


def test_comeback_requires_dip_then_recovery() -> None:
    assert "comeback" not in evaluate(
        _stats(lowest_bankroll=300), bankroll=1000, already_unlocked=set()
    )
    assert "comeback" not in evaluate(
        _stats(lowest_bankroll=150), bankroll=900, already_unlocked=set()
    )
    assert "comeback" in evaluate(
        _stats(lowest_bankroll=150), bankroll=1000, already_unlocked=set()
    )


def test_whale_after_ten_max_bets() -> None:
    assert "whale" in evaluate(
        _stats(times_bet_max=10), bankroll=1000, already_unlocked=set()
    )


def test_marathon_after_100_hands() -> None:
    assert "marathon" in evaluate(
        _stats(hands_played=100), bankroll=1000, already_unlocked=set()
    )


def test_big_pot_at_500() -> None:
    assert "big_pot" in evaluate(
        _stats(biggest_pot=500), bankroll=1000, already_unlocked=set()
    )


def test_high_roller_at_5k() -> None:
    assert "high_roller" in evaluate(
        _stats(max_bankroll_reached=5000), bankroll=5000, already_unlocked=set()
    )


def test_already_unlocked_ids_are_skipped() -> None:
    """An achievement only fires once: subsequent evaluations don't repeat it."""
    fully_eligible = _stats(
        blackjacks=1,
        longest_win_streak=5,
        lowest_bankroll=100,
        times_bet_max=10,
        hands_played=100,
        biggest_pot=500,
        max_bankroll_reached=5000,
    )
    first_pass = evaluate(fully_eligible, bankroll=1000, already_unlocked=set())
    assert len(first_pass) == 7
    second_pass = evaluate(
        fully_eligible, bankroll=1000, already_unlocked=first_pass
    )
    assert second_pass == set()


def test_by_id_returns_none_for_unknown() -> None:
    assert by_id("does-not-exist") is None
    assert by_id("first_bj") is not None
