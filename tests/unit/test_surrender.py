"""Tests for late-surrender wiring (rules + actions + state + settlement)."""

from __future__ import annotations

from blackjack21.application.use_cases import deal_hand, finish_round, player_action
from blackjack21.domain.actions import Action, legal_actions
from blackjack21.domain.cards import Card, Rank, Suit, standard_deck
from blackjack21.domain.hand import Hand
from blackjack21.domain.outcomes import Outcome
from blackjack21.domain.rules import GameRules
from blackjack21.domain.state import Phase, start_session
from blackjack21.infrastructure.rng import FixedOrderShuffler


def _hand(*cards: Card, bet: int = 100) -> Hand:
    return Hand(cards=cards, bet=bet)


def test_surrender_legal_on_first_decision() -> None:
    hand = _hand(Card(Rank.TEN, Suit.SPADES), Card(Rank.SIX, Suit.HEARTS))
    legal = legal_actions(hand, bankroll=1000, allow_surrender=True)
    assert Action.SURRENDER in legal


def test_surrender_disabled_by_rule() -> None:
    hand = _hand(Card(Rank.TEN, Suit.SPADES), Card(Rank.SIX, Suit.HEARTS))
    legal = legal_actions(hand, bankroll=1000, allow_surrender=False)
    assert Action.SURRENDER not in legal


def test_surrender_not_legal_after_hit() -> None:
    hand = _hand(
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.FOUR, Suit.HEARTS),
        Card(Rank.TWO, Suit.CLUBS),
    )
    legal = legal_actions(hand, bankroll=1000, allow_surrender=True)
    assert Action.SURRENDER not in legal


def test_surrender_settlement_returns_half_bet() -> None:
    """Surrender from the TUI must lose exactly half the bet."""
    rules = GameRules(allow_surrender=True)
    # Force a hand that won't be a natural BJ for either side and won't
    # trigger the insurance flow (no dealer Ace upcard).
    deck_order = (
        Card(Rank.TEN, Suit.SPADES),   # player 1
        Card(Rank.NINE, Suit.HEARTS),  # dealer up
        Card(Rank.SIX, Suit.DIAMONDS),  # player 2 -> hard 16
        Card(Rank.EIGHT, Suit.CLUBS),  # dealer hole
    )
    # FixedOrderShuffler needs the full 52-card multiset.
    rest = [c for c in standard_deck() if c not in deck_order]
    shuffler = FixedOrderShuffler(order=(*deck_order, *rest))
    state = start_session(rules=rules, shuffler=shuffler, bankroll=1000)
    state, _ = deal_hand(state, 100, shuffler=shuffler)
    assert state.phase is Phase.PLAYER_TURN
    assert Action.SURRENDER in state.legal_actions()

    state, _ = player_action(state, Action.SURRENDER, shuffler=shuffler)
    # All hands surrendered → no dealer play, but resolve_round still
    # needs to be called to settle. This mirrors the TUI's
    # _auto_resolve_if_done hook.
    assert state.phase is Phase.DEALER_TURN
    state, _ = finish_round(state, shuffler=shuffler)
    assert state.phase is Phase.HAND_RESOLVED
    settlement = state.settlements[0]
    assert settlement.outcome is Outcome.SURRENDER
    assert settlement.net == -50  # half of the 100 bet
    assert state.bankroll == 950
