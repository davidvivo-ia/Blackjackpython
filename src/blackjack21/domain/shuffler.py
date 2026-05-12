"""Shuffler protocol — the only abstraction over randomness in the domain."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from blackjack21.domain.cards import Card


@runtime_checkable
class Shuffler(Protocol):
    """Strategy for ordering a collection of cards.

    Implementations must be pure functions over their input: no global
    state and no observable side effects. The same input always yields
    the same output for a given shuffler instance.
    """

    def shuffled(self, cards: Iterable[Card]) -> tuple[Card, ...]:
        """Return ``cards`` reordered according to this shuffler."""
        ...
