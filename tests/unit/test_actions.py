"""Tests for action predicates."""

from __future__ import annotations

from blackjack21.domain.actions import Action, legal_actions
from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.domain.hand import Hand


def h(*ranks: Rank, **kwargs: object) -> Hand:
    cards = tuple(Card(r, Suit.SPADES) for r in ranks)
    return Hand(cards=cards, **kwargs)  # type: ignore[arg-type]


def test_finished_hand_has_no_actions() -> None:
    busted = h(Rank.KING, Rank.QUEEN, Rank.FIVE, bet=10)
    assert legal_actions(busted, bankroll=1000) == frozenset()


def test_initial_two_cards_offer_hit_stand_double() -> None:
    hand = h(Rank.NINE, Rank.SEVEN, bet=10)
    legal = legal_actions(hand, bankroll=1000)
    assert Action.HIT in legal
    assert Action.STAND in legal
    assert Action.DOUBLE in legal


def test_pair_offers_split() -> None:
    pair = h(Rank.EIGHT, Rank.EIGHT, bet=10)
    legal = legal_actions(pair, bankroll=1000)
    assert Action.SPLIT in legal


def test_no_double_without_bankroll() -> None:
    hand = h(Rank.NINE, Rank.SEVEN, bet=100)
    legal = legal_actions(hand, bankroll=50)
    assert Action.DOUBLE not in legal


def test_after_hit_no_double_or_split() -> None:
    hand = h(Rank.NINE, Rank.SEVEN, Rank.TWO, bet=10)
    legal = legal_actions(hand, bankroll=1000)
    assert legal == frozenset({Action.HIT, Action.STAND})


def test_split_hands_cannot_resplit() -> None:
    hand = h(Rank.EIGHT, Rank.EIGHT, bet=10, from_split=True)
    legal = legal_actions(hand, bankroll=1000)
    assert Action.SPLIT not in legal
