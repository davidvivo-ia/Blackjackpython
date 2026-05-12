"""Tests for hand evaluation."""

from __future__ import annotations

from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.domain.hand import Hand, evaluate

S = Suit.SPADES
H = Suit.HEARTS


def card(rank: Rank, suit: Suit = S) -> Card:
    return Card(rank, suit)


def test_empty_hand_totals_zero() -> None:
    v = evaluate(())
    assert v.total == 0
    assert not v.is_soft
    assert not v.is_bust
    assert not v.is_blackjack


def test_natural_blackjack() -> None:
    v = evaluate((card(Rank.ACE), card(Rank.KING, H)))
    assert v.total == 21
    assert v.is_soft
    assert v.is_blackjack


def test_blackjack_only_from_initial_deal() -> None:
    v = evaluate(
        (card(Rank.ACE), card(Rank.KING, H)),
        from_initial_deal=False,
    )
    assert v.total == 21
    assert not v.is_blackjack


def test_soft_18_then_hard_18() -> None:
    soft = evaluate((card(Rank.ACE), card(Rank.SEVEN)))
    assert soft.total == 18 and soft.is_soft
    hard = evaluate((card(Rank.ACE), card(Rank.SEVEN), card(Rank.TEN)))
    assert hard.total == 18 and not hard.is_soft


def test_bust_marks_total_as_minimum_value() -> None:
    v = evaluate((card(Rank.KING), card(Rank.QUEEN), card(Rank.TWO)))
    assert v.is_bust
    assert v.total == 22


def test_multiple_aces() -> None:
    v = evaluate((card(Rank.ACE), card(Rank.ACE, H), card(Rank.NINE)))
    assert v.total == 21
    assert v.is_soft


def test_hand_pair_detection() -> None:
    pair = Hand(cards=(card(Rank.EIGHT), card(Rank.EIGHT, H)))
    assert pair.is_pair
    mixed_face_pair = Hand(cards=(card(Rank.JACK), card(Rank.KING, H)))
    assert mixed_face_pair.is_pair  # both worth 10
    not_pair = Hand(cards=(card(Rank.EIGHT), card(Rank.NINE, H)))
    assert not not_pair.is_pair


def test_hand_double_doubles_bet_and_stands() -> None:
    h = Hand(cards=(card(Rank.FIVE), card(Rank.SIX, H)), bet=10).double()
    assert h.bet == 20
    assert h.doubled
    assert h.stood


def test_hand_is_finished_on_21() -> None:
    h = Hand(cards=(card(Rank.SEVEN), card(Rank.SEVEN, H), card(Rank.SEVEN)))
    assert h.value.total == 21
    assert h.is_finished
