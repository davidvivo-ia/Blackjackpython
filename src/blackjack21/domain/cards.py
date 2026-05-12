"""Card primitives: ``Rank``, ``Suit`` and ``Card``.

All values are immutable, hashable and comparable. Cards print with
Unicode suit glyphs by default; use :func:`Card.to_ascii` for the
ASCII fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class Suit(StrEnum):
    """The four card suits."""

    SPADES = "S"
    HEARTS = "H"
    DIAMONDS = "D"
    CLUBS = "C"

    @property
    def glyph(self) -> str:
        """Unicode glyph for this suit (``♠ ♥ ♦ ♣``)."""
        return _SUIT_GLYPH[self]

    @property
    def is_red(self) -> bool:
        """``True`` for hearts and diamonds."""
        return self in (Suit.HEARTS, Suit.DIAMONDS)


_SUIT_GLYPH: Final[dict[Suit, str]] = {
    Suit.SPADES: "♠",
    Suit.HEARTS: "♥",
    Suit.DIAMONDS: "♦",
    Suit.CLUBS: "♣",
}


class Rank(StrEnum):
    """The thirteen card ranks.

    Encoded with single characters: ``A 2 3 4 5 6 7 8 9 T J Q K``. We
    use ``T`` for ten so every rank fits in one column, mirroring
    poker notation.
    """

    ACE = "A"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "T"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"

    @property
    def hard_value(self) -> int:
        """Numeric value, treating Ace as 1 and faces as 10."""
        return _RANK_HARD[self]

    @property
    def is_ace(self) -> bool:
        return self is Rank.ACE

    @property
    def is_face(self) -> bool:
        return self in (Rank.JACK, Rank.QUEEN, Rank.KING)


_RANK_HARD: Final[dict[Rank, int]] = {
    Rank.ACE: 1,
    Rank.TWO: 2,
    Rank.THREE: 3,
    Rank.FOUR: 4,
    Rank.FIVE: 5,
    Rank.SIX: 6,
    Rank.SEVEN: 7,
    Rank.EIGHT: 8,
    Rank.NINE: 9,
    Rank.TEN: 10,
    Rank.JACK: 10,
    Rank.QUEEN: 10,
    Rank.KING: 10,
}


@dataclass(frozen=True, slots=True, order=True)
class Card:
    """A single playing card.

    ``order=True`` enables sorting by ``(rank, suit)`` which keeps tests
    deterministic when comparing card collections.
    """

    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.glyph}"

    def to_ascii(self) -> str:
        """Return ASCII-only representation (e.g. ``AS``, ``TD``)."""
        return f"{self.rank.value}{self.suit.value}"


def standard_deck() -> tuple[Card, ...]:
    """Return the canonical 52-card deck, sorted by suit and rank."""
    return tuple(Card(rank, suit) for suit in Suit for rank in Rank)
