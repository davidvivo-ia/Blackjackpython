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
"""Single-deck behaviour: reshuffle when this many cards remain.

For multi-deck shoes we switch to a fraction-based "penetration"
trigger instead — see :meth:`Deck._reshuffle_due`.
"""

SHOE_PENETRATION: float = 0.75
"""Fraction of the shoe played before a reshuffle in multi-deck shoes."""


@dataclass(frozen=True, slots=True)
class Deck:
    """An ordered shoe with a discard pile.

    Attributes:
        cards: The cards still to be drawn, top of the deck at index 0.
        discard: Cards already played and burned, in deposit order.
    """

    cards: tuple[Card, ...]
    discard: tuple[Card, ...] = field(default_factory=tuple)

    @classmethod
    def fresh(cls, shuffler: Shuffler, *, num_decks: int = 1) -> Deck:
        """Return a freshly shuffled shoe of ``num_decks`` x 52 cards."""
        if num_decks < 1:
            raise ValueError("num_decks must be at least 1.")
        base = standard_deck() * num_decks
        return cls(cards=shuffler.shuffled(base))

    @property
    def remaining(self) -> int:
        return len(self.cards)

    @property
    def total(self) -> int:
        """Cards in play + in the discard pile."""
        return len(self.cards) + len(self.discard)

    def _reshuffle_due(self) -> bool:
        if not self.discard:
            return False
        # Single-deck preserves the BASIC original feel: shallow trigger.
        if self.total <= 52:
            return self.remaining <= RESHUFFLE_THRESHOLD
        # Multi-deck shoes: standard casino penetration.
        return self.remaining <= int(self.total * (1 - SHOE_PENETRATION))

    def draw(self, shuffler: Shuffler) -> tuple[Card, Deck]:
        """Draw the top card.

        If the deck has crossed its reshuffle trigger, the discard
        pile is folded back in before drawing. If after reshuffling
        no cards remain (impossible in practice), raises
        :class:`DeckExhaustedError`.
        """
        deck = self
        if deck._reshuffle_due():
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
