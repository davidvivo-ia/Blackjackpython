"""Basic Strategy recommender tests.

These tests pin a representative slice of the Thorp single-deck S17
chart. Where the published chart disagrees on borderline cells across
sources we picked the most widely cited recommendation.
"""

from __future__ import annotations

import pytest

from blackjack21.application.strategy import recommend
from blackjack21.domain.actions import Action
from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.domain.dealer import play_dealer  # noqa: F401  (import smoke)
from blackjack21.domain.deck import Deck
from blackjack21.domain.hand import Hand
from blackjack21.domain.rules import DEFAULT_RULES
from blackjack21.domain.state import GameState, Phase
from blackjack21.infrastructure.rng import IdentityShuffler


def _state(
    player_cards: tuple[Card, ...], upcard: Card, *, bankroll: int = 1000
) -> GameState:
    """Build a minimal GameState parked in PLAYER_TURN for the chart cells."""
    hand = Hand(cards=player_cards, bet=10)
    dealer = Hand(cards=(upcard, Card(Rank.TWO, Suit.CLUBS)))
    return GameState(
        rules=DEFAULT_RULES,
        bankroll=bankroll,
        deck=Deck.fresh(IdentityShuffler()),
        dealer=dealer,
        player_hands=(hand,),
        phase=Phase.PLAYER_TURN,
    )


def C(rank: Rank, suit: Suit = Suit.SPADES) -> Card:  # noqa: N802
    return Card(rank, suit)


# ---- hard totals --------------------------------------------------------


@pytest.mark.parametrize(
    ("total", "upcard_rank", "expected"),
    [
        (5, Rank.SIX, Action.HIT),
        (8, Rank.FIVE, Action.HIT),
        (9, Rank.TWO, Action.HIT),
        (9, Rank.THREE, Action.DOUBLE),
        (9, Rank.SIX, Action.DOUBLE),
        (9, Rank.SEVEN, Action.HIT),
        (10, Rank.NINE, Action.DOUBLE),
        (10, Rank.TEN, Action.HIT),
        (10, Rank.ACE, Action.HIT),
        (11, Rank.ACE, Action.DOUBLE),
        (12, Rank.THREE, Action.HIT),
        (12, Rank.FOUR, Action.STAND),
        (12, Rank.SIX, Action.STAND),
        (12, Rank.SEVEN, Action.HIT),
        (16, Rank.SIX, Action.STAND),
        (16, Rank.SEVEN, Action.HIT),
        (17, Rank.ACE, Action.STAND),
    ],
)
def test_hard_chart(total: int, upcard_rank: Rank, expected: Action) -> None:
    """Build a non-pair non-soft hand summing to ``total`` and check the chart."""
    cards_by_total: dict[int, tuple[Card, ...]] = {
        5: (C(Rank.TWO), C(Rank.THREE)),
        8: (C(Rank.FIVE), C(Rank.THREE)),
        9: (C(Rank.SEVEN), C(Rank.TWO)),
        10: (C(Rank.SEVEN), C(Rank.THREE)),
        11: (C(Rank.SEVEN), C(Rank.FOUR)),
        12: (C(Rank.SEVEN), C(Rank.THREE), C(Rank.TWO)),
        16: (C(Rank.SEVEN), C(Rank.SIX), C(Rank.THREE)),
        17: (C(Rank.SEVEN), C(Rank.SIX), C(Rank.FOUR)),
    }
    cards = cards_by_total[total]
    s = _state(cards, C(upcard_rank))
    assert recommend(s) == expected


# ---- soft totals --------------------------------------------------------


@pytest.mark.parametrize(
    ("other_rank", "upcard_rank", "expected"),
    [
        (Rank.TWO, Rank.FIVE, Action.DOUBLE),  # A2 vs 5
        (Rank.TWO, Rank.TWO, Action.HIT),  # A2 vs 2
        (Rank.SIX, Rank.SIX, Action.DOUBLE),  # A6 vs 6
        (Rank.SIX, Rank.SEVEN, Action.HIT),  # A6 vs 7
        (Rank.SEVEN, Rank.TWO, Action.STAND),  # A7 vs 2
        (Rank.SEVEN, Rank.SIX, Action.DOUBLE),  # A7 vs 6
        (Rank.SEVEN, Rank.NINE, Action.HIT),  # A7 vs 9
        (Rank.EIGHT, Rank.SIX, Action.STAND),  # A8 vs 6 (single-deck-conservative)
        (Rank.NINE, Rank.SIX, Action.STAND),  # A9 vs 6
    ],
)
def test_soft_chart(
    other_rank: Rank, upcard_rank: Rank, expected: Action
) -> None:
    s = _state((C(Rank.ACE), C(other_rank)), C(upcard_rank))
    # A2 + Ace etc. are pairs of Ace if other is Ace, but we never test that here.
    assert recommend(s) == expected


# ---- pair splitting -----------------------------------------------------


@pytest.mark.parametrize(
    ("pair_rank", "upcard_rank", "expected"),
    [
        (Rank.ACE, Rank.TEN, Action.SPLIT),  # AA always splits
        (Rank.EIGHT, Rank.ACE, Action.SPLIT),  # 88 always splits
        (Rank.TWO, Rank.SEVEN, Action.SPLIT),  # 22 vs 7
        (Rank.TWO, Rank.EIGHT, Action.HIT),  # 22 vs 8
        (Rank.FOUR, Rank.SIX, Action.SPLIT),  # 44 vs 6
        (Rank.FOUR, Rank.FOUR, Action.HIT),  # 44 vs 4
        (Rank.FIVE, Rank.NINE, Action.DOUBLE),  # 55 = hard 10 vs 9
        (Rank.NINE, Rank.SEVEN, Action.STAND),  # 99 vs 7
        (Rank.NINE, Rank.EIGHT, Action.SPLIT),  # 99 vs 8
        (Rank.TEN, Rank.SIX, Action.STAND),  # TT never splits
    ],
)
def test_pair_chart(
    pair_rank: Rank, upcard_rank: Rank, expected: Action
) -> None:
    s = _state((C(pair_rank), C(pair_rank, Suit.HEARTS)), C(upcard_rank))
    assert recommend(s) == expected


# ---- legality fallback --------------------------------------------------


def test_recommend_falls_back_to_hit_when_double_illegal() -> None:
    """3-card hands cannot double; the recommendation should degrade to hit."""
    # 7+2+2 = soft? no, hard 11. Strategy says DOUBLE, but with 3 cards
    # the legal actions exclude DOUBLE, so we should get HIT.
    hand = Hand(cards=(C(Rank.SEVEN), C(Rank.TWO), C(Rank.TWO)), bet=10)
    dealer = Hand(cards=(C(Rank.FIVE), C(Rank.TWO)))
    state = GameState(
        rules=DEFAULT_RULES,
        bankroll=1000,
        deck=Deck.fresh(IdentityShuffler()),
        dealer=dealer,
        player_hands=(hand,),
        phase=Phase.PLAYER_TURN,
    )
    assert Action.DOUBLE not in state.legal_actions()
    assert recommend(state) == Action.HIT


def test_recommend_outside_player_turn_returns_stand() -> None:
    hand = Hand(cards=(C(Rank.TEN), C(Rank.SEVEN)), bet=10)
    dealer = Hand(cards=(C(Rank.FIVE), C(Rank.TWO)))
    state = GameState(
        rules=DEFAULT_RULES,
        bankroll=1000,
        deck=Deck.fresh(IdentityShuffler()),
        dealer=dealer,
        player_hands=(hand,),
        phase=Phase.AWAITING_BET,
    )
    assert recommend(state) == Action.STAND
