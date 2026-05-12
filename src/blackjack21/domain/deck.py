"""Immutable single-deck shoe with a discard pile.

A ``Deck`` is an immutable snapshot. Drawing returns a fresh ``Deck``
plus the drawn card. When the remaining cards fall below a threshold,
``Deck.draw`` automatically reshuffles the discard pile back in.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from blackjack21.domain.cards import Card, standard_deck
from blackjack21.domain.errors import DeckExhaustedError
from blackjack21.domain.shuffler import Shuffler

RESHUFFLE_THRESHOLD: int = 15
"""Number of cards remaining at or below which we reshuffle."""


@dataclass(frozen=True, slots=True)
class Deck:
    """An ordered shoe with a discard pile.

    Attributes:
        cards: The cards still to be drawn, top of the deck at index 0.
        discard: Cards already played and burned, in deposit order.
        shuffler: Strategy used when reshuffling.
    """

    cards: tuple[Card, ...]
    discard: tuple[Card, ...] = field(default_factory=tuple)

    @classmethod
    def fresh(cls, shuffler: Shuffler) -> Deck:
        """Return a freshly shuffled 52-card deck."""
        return cls(cards=shuffler.shuffled(standard_deck()))

    @property
    def remaining(self) -> int:
        return len(self.cards)

    def draw(self, shuffler: Shuffler) -> tuple[Card, Deck]:
        """Draw the top card.

        If the deck is at or below :data:`RESHUFFLE_THRESHOLD`, the
        discard pile is folded back in before drawing. If even after
        the reshuffle no cards remain (impossible in practice with
        normal play but guarded for safety), raises
        :class:`DeckExhaustedError`.
        """
        deck = self
        if deck.remaining <= RESHUFFLE_THRESHOLD and deck.discard:
            deck = deck.reshuffle(shuffler)
        if not deck.cards:
            raise DeckExhaustedError("No cards available even after reshuffle.")
        return deck.cards[0], Deck(cards=deck.cards[1:], discard=deck.discard)

    def discard_cards(self, cards: tuple[Card, ...]) -> Deck:
        """Return a new deck with ``cards`` appended to the discard pile."""
        if not cards:
            return self
        return Deck(cards=self.cards, discard=self.discard + cards)

    def reshuffle(self, shuffler: Shuffler) -> Deck:
        """Fold the discard pile back into the deck and shuffle."""
        pooled = self.cards + self.discard
        return Deck(cards=shuffler.shuffled(pooled))
