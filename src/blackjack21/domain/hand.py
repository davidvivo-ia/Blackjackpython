"""Hands and their evaluation.

Following the spirit of the BASIC original, a hand is just a sequence
of cards plus a current bet. Soft/hard ace handling is derived on
demand by :func:`evaluate`, not stored.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from blackjack21.domain.cards import Card, Rank


@dataclass(frozen=True, slots=True)
class HandValue:
    """Computed view of a hand.

    Attributes:
        total: The best non-busting total, or the busted total if every
            possible interpretation exceeds 21.
        is_soft: True if at least one ace is still being counted as 11.
        is_bust: True if the lowest possible total exceeds 21.
        is_blackjack: True only for a 2-card 21 dealt initially.
    """

    total: int
    is_soft: bool
    is_bust: bool
    is_blackjack: bool


@dataclass(frozen=True, slots=True)
class Hand:
    """A player's hand of cards plus its current bet and flags."""

    cards: tuple[Card, ...] = field(default_factory=tuple)
    bet: int = 0
    doubled: bool = False
    surrendered: bool = False
    from_split: bool = False
    stood: bool = False

    def add(self, card: Card) -> Hand:
        """Return a new hand with ``card`` appended."""
        return replace(self, cards=(*self.cards, card))

    def with_bet(self, bet: int) -> Hand:
        return replace(self, bet=bet)

    def stand(self) -> Hand:
        return replace(self, stood=True)

    def double(self) -> Hand:
        return replace(self, bet=self.bet * 2, doubled=True, stood=True)

    def surrender(self) -> Hand:
        return replace(self, surrendered=True, stood=True)

    @property
    def value(self) -> HandValue:
        return evaluate(self.cards, from_initial_deal=not self.from_split)

    @property
    def is_finished(self) -> bool:
        v = self.value
        return self.stood or self.surrendered or v.is_bust or v.total == 21

    @property
    def is_pair(self) -> bool:
        """True iff the hand has exactly two cards of the same rank."""
        if len(self.cards) != 2:
            return False
        return self.cards[0].rank.hard_value == self.cards[1].rank.hard_value


def evaluate(cards: tuple[Card, ...], *, from_initial_deal: bool = True) -> HandValue:
    """Evaluate a tuple of cards as a blackjack hand.

    Args:
        cards: The cards in the hand, in deal order.
        from_initial_deal: Whether the hand was dealt from the initial
            two-card round; only such hands can qualify as a *natural*
            blackjack.
    """
    hard_total = sum(c.rank.hard_value for c in cards)
    aces = sum(1 for c in cards if c.rank is Rank.ACE)
    total = hard_total
    is_soft = False
    if aces and hard_total + 10 <= 21:
        total = hard_total + 10
        is_soft = True
    is_bust = hard_total > 21
    is_blackjack = (
        from_initial_deal
        and len(cards) == 2
        and total == 21
        and any(c.rank is Rank.ACE for c in cards)
    )
    return HandValue(
        total=total,
        is_soft=is_soft,
        is_bust=is_bust,
        is_blackjack=is_blackjack,
    )
