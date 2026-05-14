"""Exact-deck bust probability tests."""

from __future__ import annotations

from blackjack21.application.odds import prob_bust_on_hit
from blackjack21.domain.cards import Card, Rank, Suit, standard_deck
from blackjack21.domain.deck import Deck
from blackjack21.domain.hand import Hand


def _full_deck_minus(used: tuple[Card, ...]) -> Deck:
    """Return a Deck containing every card NOT in ``used``."""
    remaining = tuple(c for c in standard_deck() if c not in used)
    return Deck(cards=remaining)


def test_empty_hand_or_empty_deck_returns_zero() -> None:
    empty_hand = Hand(cards=(), bet=0)
    deck = Deck(cards=())
    assert prob_bust_on_hit(empty_hand, _full_deck_minus(())) == 0.0
    assert prob_bust_on_hit(
        Hand(cards=(Card(Rank.TEN, Suit.SPADES),)),
        deck,
    ) == 0.0


def test_total_5_never_busts_on_next_card() -> None:
    """5 + any single card maxes at 5 + 11 = 16, no bust possible."""
    used = (Card(Rank.TWO, Suit.SPADES), Card(Rank.THREE, Suit.HEARTS))
    hand = Hand(cards=used, bet=10)
    assert prob_bust_on_hit(hand, _full_deck_minus(used)) == 0.0


def test_hard_20_busts_on_anything_but_ace() -> None:
    """T+T = 20. Any 2-9, J, Q, K busts; only A keeps it at 21."""
    used = (Card(Rank.TEN, Suit.SPADES), Card(Rank.KING, Suit.HEARTS))
    hand = Hand(cards=used, bet=10)
    deck = _full_deck_minus(used)
    # 4 aces remain out of 50 cards → 46 bust / 50 = 92%
    p = prob_bust_on_hit(hand, deck)
    assert abs(p - 46 / 50) < 1e-9


def test_soft_17_never_busts() -> None:
    """A+6 = soft 17. Any card keeps total <= 21 by re-counting Ace as 1."""
    used = (Card(Rank.ACE, Suit.SPADES), Card(Rank.SIX, Suit.HEARTS))
    hand = Hand(cards=used, bet=10)
    assert prob_bust_on_hit(hand, _full_deck_minus(used)) == 0.0
