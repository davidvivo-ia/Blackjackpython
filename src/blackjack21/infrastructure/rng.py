"""Random number generation infrastructure.

We deliberately keep this thin: the entire game depends on a single
``Shuffler`` protocol, and these implementations are the only places
where ``random.Random`` is allowed.
"""

from __future__ import annotations

import random
from collections.abc import Iterable

from blackjack21.domain.cards import Card


class SystemShuffler:
    """Pseudorandom shuffler backed by :class:`random.Random`."""

    __slots__ = ("_rng",)

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def shuffled(self, cards: Iterable[Card]) -> tuple[Card, ...]:
        result = list(cards)
        self._rng.shuffle(result)
        return tuple(result)


class IdentityShuffler:
    """Shuffler that returns its input unchanged.

    Useful in property tests and in transitions that don't need any
    randomness (e.g. folding the discard pile back without re-ordering
    in deterministic tests).
    """

    __slots__ = ()

    def shuffled(self, cards: Iterable[Card]) -> tuple[Card, ...]:
        return tuple(cards)


class FixedOrderShuffler:
    """Shuffler that always returns a pre-defined order.

    Useful for replaying a deterministic deal in tests. The order must
    contain exactly the same multiset as ``cards`` passed to
    :meth:`shuffled` or a ``ValueError`` is raised.
    """

    __slots__ = ("_order",)

    def __init__(self, order: Iterable[Card]) -> None:
        self._order = tuple(order)

    def shuffled(self, cards: Iterable[Card]) -> tuple[Card, ...]:
        provided = tuple(cards)
        if sorted(provided) != sorted(self._order):
            raise ValueError(
                "FixedOrderShuffler order does not match the cards provided."
            )
        return self._order
