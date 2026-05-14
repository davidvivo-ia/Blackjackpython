"""Basic-strategy drill mode.

Generates random decision scenarios (hard totals, soft totals, pairs,
or surrender spots) and grades the player's answer against
:func:`blackjack21.application.strategy.recommend`. Pure logic only —
the CLI in :mod:`blackjack21.presentation.cli` handles the IO.
"""

from __future__ import annotations

import random
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from blackjack21.application.strategy import recommend
from blackjack21.domain.actions import Action
from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.domain.deck import Deck
from blackjack21.domain.hand import Hand
from blackjack21.domain.rules import GameRules
from blackjack21.domain.state import GameState, Phase
from blackjack21.infrastructure.rng import IdentityShuffler

DEFAULT_ROUNDS = 10


class Topic(StrEnum):
    """Categories of basic-strategy spots the drill can quiz."""

    HARD = "hard"
    SOFT = "soft"
    PAIRS = "pairs"
    SURRENDER = "surrender"
    ALL = "all"


@dataclass(frozen=True, slots=True)
class Situation:
    """One scenario: a player hand vs a dealer upcard."""

    hand: Hand
    upcard: Card


@dataclass(frozen=True, slots=True)
class GradedAnswer:
    """The outcome of grading a single situation."""

    situation: Situation
    answer: Action
    expected: Action

    @property
    def correct(self) -> bool:
        return self.answer is self.expected


_NON_ACE_RANKS: tuple[Rank, ...] = tuple(r for r in Rank if r is not Rank.ACE)
_RULES = GameRules()


def build_state(situation: Situation) -> GameState:
    """Build a minimal :class:`GameState` parked in PLAYER_TURN."""
    dealer = Hand(cards=(situation.upcard, Card(Rank.TWO, Suit.CLUBS)))
    return GameState(
        rules=_RULES,
        bankroll=1000,
        deck=Deck.fresh(IdentityShuffler()),
        dealer=dealer,
        player_hands=(situation.hand,),
        phase=Phase.PLAYER_TURN,
    )


def expected_action(situation: Situation) -> Action:
    """The basic-strategy action for ``situation``."""
    return recommend(build_state(situation))


def grade(situation: Situation, answer: Action) -> GradedAnswer:
    """Wrap an answer with whether it matches basic strategy."""
    return GradedAnswer(
        situation=situation, answer=answer, expected=expected_action(situation)
    )


def _random_non_ace(rng: random.Random) -> Rank:
    return rng.choice(_NON_ACE_RANKS)


def _hard_hand(rng: random.Random) -> Hand:
    """Two non-Ace cards forming a non-pair hard total in 5..18."""
    while True:
        a = _random_non_ace(rng)
        b = _random_non_ace(rng)
        # Avoid pairs (those belong to the PAIRS topic).
        if a.hard_value == b.hard_value:
            continue
        cards = (
            Card(a, Suit.SPADES),
            Card(b, Suit.HEARTS),
        )
        total = a.hard_value + b.hard_value
        if 5 <= total <= 18:
            return Hand(cards=cards, bet=100)


def _soft_hand(rng: random.Random) -> Hand:
    """Ace plus a non-Ace card."""
    candidates = [
        r for r in _NON_ACE_RANKS if r is not Rank.TEN and r.hard_value < 10
    ]
    other = rng.choice(candidates)
    return Hand(
        cards=(
            Card(Rank.ACE, Suit.SPADES),
            Card(other, Suit.HEARTS),
        ),
        bet=100,
    )


def _pair_hand(rng: random.Random) -> Hand:
    rank = rng.choice(list(Rank))
    return Hand(
        cards=(
            Card(rank, Suit.SPADES),
            Card(rank, Suit.HEARTS),
        ),
        bet=100,
    )


def _surrender_hand(rng: random.Random) -> Hand:
    """Hard 14/15/16 — the cells where surrender is in play."""
    target = rng.choice((14, 15, 16))
    # Build with TEN + (target-10) for simplicity.
    other_value = target - 10
    other_rank = next(
        r for r in Rank if r.hard_value == other_value and r is not Rank.ACE
    )
    return Hand(
        cards=(
            Card(Rank.TEN, Suit.SPADES),
            Card(other_rank, Suit.HEARTS),
        ),
        bet=100,
    )


def _random_upcard(rng: random.Random) -> Card:
    return Card(rng.choice(list(Rank)), Suit.CLUBS)


def random_situation(topic: Topic, rng: random.Random) -> Situation:
    """Pick a random :class:`Situation` for ``topic``."""
    if topic is Topic.ALL:
        topic = rng.choice(
            (Topic.HARD, Topic.SOFT, Topic.PAIRS, Topic.SURRENDER)
        )
    if topic is Topic.HARD:
        hand = _hard_hand(rng)
    elif topic is Topic.SOFT:
        hand = _soft_hand(rng)
    elif topic is Topic.PAIRS:
        hand = _pair_hand(rng)
    elif topic is Topic.SURRENDER:
        hand = _surrender_hand(rng)
    else:  # pragma: no cover — exhaustive above
        raise ValueError(f"Unknown topic: {topic}")
    return Situation(hand=hand, upcard=_random_upcard(rng))


_ACTION_KEYS: dict[str, Action] = {
    "H": Action.HIT,
    "S": Action.STAND,
    "D": Action.DOUBLE,
    "P": Action.SPLIT,
    "U": Action.SURRENDER,
}


def parse_action(key: str) -> Action | None:
    """Map a single-letter input to an :class:`Action`. ``None`` if invalid."""
    return _ACTION_KEYS.get(key.strip().upper()[:1])


def score(answers: Iterable[GradedAnswer]) -> tuple[int, int]:
    """Return ``(correct, total)`` for an iterable of graded answers."""
    correct = 0
    total = 0
    for a in answers:
        total += 1
        if a.correct:
            correct += 1
    return correct, total
