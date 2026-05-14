"""Exact-deck odds helpers.

For the deck of remaining cards (i.e. what's left in the shoe), the
probability of busting on the next hit is exact: count the cards that
would push the hand above 21, divide by total remaining.
"""

from __future__ import annotations

from blackjack21.domain.deck import Deck
from blackjack21.domain.hand import Hand, evaluate


def prob_bust_on_hit(hand: Hand, deck: Deck) -> float:
    """Probability that the next card busts ``hand``.

    Returns ``0.0`` when the deck is empty or the hand has no cards.
    Soft aces are taken into account: an A+6 will not bust when hit
    with an 8 (becomes A=1 + 6 + 8 = 15).
    """
    if not deck.cards or not hand.cards:
        return 0.0
    total = len(deck.cards)
    bust = sum(
        1 for c in deck.cards if evaluate((*hand.cards, c)).is_bust
    )
    return bust / total
