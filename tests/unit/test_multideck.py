"""Multi-deck shoe basics."""

from __future__ import annotations

from collections import Counter

import pytest

from blackjack21.domain.cards import Card
from blackjack21.domain.deck import SHOE_PENETRATION, Deck
from blackjack21.infrastructure.rng import IdentityShuffler, SystemShuffler


@pytest.mark.parametrize("n", [1, 2, 4, 6, 8])
def test_fresh_shoe_has_correct_card_count(n: int) -> None:
    deck = Deck.fresh(SystemShuffler(seed=0), num_decks=n)
    assert deck.remaining == n * 52
    # Every (rank, suit) appears exactly n times.
    counts = Counter(deck.cards)
    assert all(c == n for c in counts.values())


def test_fresh_shoe_rejects_zero_decks() -> None:
    with pytest.raises(ValueError, match="num_decks"):
        Deck.fresh(IdentityShuffler(), num_decks=0)


def test_multi_deck_reshuffle_uses_penetration() -> None:
    """A 6-deck shoe should reshuffle around the 75% mark, not at 15 cards."""
    shoe = Deck.fresh(SystemShuffler(seed=0), num_decks=6)
    total = shoe.total  # 312
    target = int(total * (1 - SHOE_PENETRATION))  # 78 for 6 decks
    # Burn cards (drawing + discarding) until we sit exactly at the trigger.
    while shoe.remaining > target:
        card: Card
        card, shoe = shoe.draw(SystemShuffler(seed=0))
        shoe = shoe.discard_cards((card,))
    assert shoe.remaining == target
    pre = shoe.remaining
    # The very next draw should fold the discard pile back.
    _, shoe = shoe.draw(SystemShuffler(seed=0))
    assert shoe.discard == ()
    assert shoe.remaining > pre
