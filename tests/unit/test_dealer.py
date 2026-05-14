"""Dealer policy tests."""

from __future__ import annotations

from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.domain.dealer import dealer_should_hit
from blackjack21.domain.hand import Hand
from blackjack21.domain.rules import DEFAULT_RULES, GameRules


def hand(*ranks: Rank) -> Hand:
    return Hand(cards=tuple(Card(r, Suit.SPADES) for r in ranks))


def test_dealer_hits_below_17() -> None:
    assert dealer_should_hit(hand(Rank.KING, Rank.SIX), DEFAULT_RULES)


def test_dealer_stands_on_hard_17() -> None:
    assert not dealer_should_hit(hand(Rank.KING, Rank.SEVEN), DEFAULT_RULES)


def test_s17_stands_on_soft_17() -> None:
    # Ace + 6 = soft 17
    assert not dealer_should_hit(hand(Rank.ACE, Rank.SIX), DEFAULT_RULES)


def test_h17_hits_soft_17() -> None:
    h17 = GameRules(dealer_hits_soft_17=True)
    assert dealer_should_hit(hand(Rank.ACE, Rank.SIX), h17)


def test_dealer_does_not_hit_after_bust() -> None:
    assert not dealer_should_hit(hand(Rank.KING, Rank.QUEEN, Rank.FIVE), DEFAULT_RULES)
