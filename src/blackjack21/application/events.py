"""Flat event records emitted while a hand plays out.

The TUI subscribes to these events to drive its animations, and the
``--demo`` mode serializes them to stdout for E2E snapshot testing.
The event union is closed and exhaustive so ``match`` over it is
type-checked.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from blackjack21.domain.actions import Action
from blackjack21.domain.cards import Card
from blackjack21.domain.outcomes import Settlement


@dataclass(frozen=True, slots=True)
class BetPlaced:
    bet: int
    bankroll: int
    kind: Literal["bet_placed"] = "bet_placed"


@dataclass(frozen=True, slots=True)
class CardDealt:
    card: Card
    to: Literal["player", "dealer"]
    hidden: bool = False
    hand_index: int = 0
    kind: Literal["card_dealt"] = "card_dealt"


@dataclass(frozen=True, slots=True)
class PlayerActed:
    action: Action
    hand_index: int
    kind: Literal["player_acted"] = "player_acted"


@dataclass(frozen=True, slots=True)
class DealerRevealed:
    hole_card: Card
    kind: Literal["dealer_revealed"] = "dealer_revealed"


@dataclass(frozen=True, slots=True)
class InsuranceOffered:
    max_insurance: int
    kind: Literal["insurance_offered"] = "insurance_offered"


@dataclass(frozen=True, slots=True)
class InsuranceResolved:
    insurance_bet: int
    won: bool
    kind: Literal["insurance_resolved"] = "insurance_resolved"


@dataclass(frozen=True, slots=True)
class HandResolved:
    settlement: Settlement
    hand_index: int
    bankroll_after: int
    kind: Literal["hand_resolved"] = "hand_resolved"


@dataclass(frozen=True, slots=True)
class SessionEnded:
    final_bankroll: int
    reason: Literal["bankroll_exhausted", "user_quit"]
    kind: Literal["session_ended"] = "session_ended"


type GameEvent = (
    BetPlaced
    | CardDealt
    | PlayerActed
    | DealerRevealed
    | InsuranceOffered
    | InsuranceResolved
    | HandResolved
    | SessionEnded
)
