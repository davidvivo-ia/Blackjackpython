"""GameRules tests."""

from __future__ import annotations

import pytest

from blackjack21.domain.errors import InvalidBetError
from blackjack21.domain.rules import DEFAULT_RULES, GameRules


def test_defaults_match_original_listing() -> None:
    r = DEFAULT_RULES
    assert r.min_bet == 1
    assert r.max_bet == 500
    assert r.initial_bankroll == 1000
    assert r.dealer_stands_on == 17
    assert r.dealer_hits_soft_17 is False


def test_validate_bet_accepts_within_range() -> None:
    DEFAULT_RULES.validate_bet(100, bankroll=1000)
    DEFAULT_RULES.validate_bet(1, bankroll=1000)
    DEFAULT_RULES.validate_bet(500, bankroll=1000)


@pytest.mark.parametrize(
    ("bet", "bankroll"),
    [(0, 1000), (-1, 1000), (501, 1000), (100, 50)],
)
def test_validate_bet_rejects_invalid(bet: int, bankroll: int) -> None:
    with pytest.raises(InvalidBetError):
        DEFAULT_RULES.validate_bet(bet, bankroll=bankroll)


def test_h17_variant_is_supported() -> None:
    h17 = GameRules(dealer_hits_soft_17=True)
    assert h17.dealer_hits_soft_17
