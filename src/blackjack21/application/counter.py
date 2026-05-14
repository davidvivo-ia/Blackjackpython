"""Hi-Lo card counter — pedagogy only.

Single-deck or shoe counting using the standard Hi-Lo tag values:
2-6 = +1, 7-9 = 0, T-A = -1. Two derived metrics:

- *running count (RC)*: signed sum of every visible card.
- *true count (TC)*: RC divided by the number of decks remaining,
  capped so the divisor never drops below 0.5 (Wong's convention).

This module is a pure read of :class:`GameState`. The TUI calls
:func:`compute` at every refresh and displays the result when the
``--counter`` flag is on. We intentionally do not "play for the
player" — counts are informational, never feed strategy.
"""

from __future__ import annotations

from dataclasses import dataclass

from blackjack21.domain.cards import Rank
from blackjack21.domain.state import GameState, Phase

_TAG: dict[Rank, int] = {
    Rank.TWO: +1,
    Rank.THREE: +1,
    Rank.FOUR: +1,
    Rank.FIVE: +1,
    Rank.SIX: +1,
    Rank.SEVEN: 0,
    Rank.EIGHT: 0,
    Rank.NINE: 0,
    Rank.TEN: -1,
    Rank.JACK: -1,
    Rank.QUEEN: -1,
    Rank.KING: -1,
    Rank.ACE: -1,
}


@dataclass(frozen=True, slots=True)
class HiLoCount:
    """Snapshot of the running and true count at a moment in time."""

    running: int
    cards_seen: int
    decks_in_shoe: int

    @property
    def decks_remaining(self) -> float:
        """Fractional decks still unseen, floored at 0.5."""
        total = self.decks_in_shoe * 52
        unseen = max(0, total - self.cards_seen)
        return max(0.5, unseen / 52)

    @property
    def true_count(self) -> float:
        return self.running / self.decks_remaining


def compute(state: GameState) -> HiLoCount:
    """Tally Hi-Lo over every card the player has actually seen.

    The dealer's hole card stays hidden during PLAYER_TURN /
    AWAITING_INSURANCE, so it doesn't contribute to the count until
    the dealer reveals.
    """
    running = 0
    cards_seen = 0

    for card in state.deck.discard:
        running += _TAG[card.rank]
        cards_seen += 1

    for hand in state.player_hands:
        for card in hand.cards:
            running += _TAG[card.rank]
            cards_seen += 1

    if state.dealer.cards:
        hole_hidden = state.phase in (
            Phase.PLAYER_TURN,
            Phase.AWAITING_INSURANCE,
        )
        visible_dealer = (
            state.dealer.cards[:1] if hole_hidden else state.dealer.cards
        )
        for card in visible_dealer:
            running += _TAG[card.rank]
            cards_seen += 1

    return HiLoCount(
        running=running,
        cards_seen=cards_seen,
        decks_in_shoe=state.rules.num_decks,
    )
