"""Property-based tests for the basic-strategy recommender.

These complement the parametrised cell-by-cell chart in
``test_strategy.py``: instead of hand-picked spots, we generate
random (player hand, dealer upcard) pairs and assert invariants
that must hold for every legal decision point.
"""

from __future__ import annotations

from dataclasses import replace as dc_replace

import hypothesis.strategies as st
from hypothesis import assume, given, settings

from blackjack21.application.strategy import recommend
from blackjack21.domain.actions import Action
from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.domain.deck import Deck
from blackjack21.domain.hand import Hand
from blackjack21.domain.rules import GameRules
from blackjack21.domain.state import GameState, Phase
from blackjack21.infrastructure.rng import IdentityShuffler

cards = st.builds(Card, st.sampled_from(list(Rank)), st.sampled_from(list(Suit)))


@st.composite
def _player_hand(draw: st.DrawFn) -> Hand:
    n = draw(st.integers(min_value=2, max_value=5))
    cs = tuple(draw(cards) for _ in range(n))
    hand = Hand(cards=cs, bet=100)
    # Strategy is only consulted on live (non-bust, non-21) hands.
    assume(not hand.value.is_bust)
    assume(hand.value.total != 21)
    return hand


def _state(hand: Hand, upcard: Card, *, rules: GameRules) -> GameState:
    dealer = Hand(cards=(upcard, Card(Rank.TWO, Suit.CLUBS)))
    return GameState(
        rules=rules,
        bankroll=1000,
        deck=Deck.fresh(IdentityShuffler()),
        dealer=dealer,
        player_hands=(hand,),
        phase=Phase.PLAYER_TURN,
    )


_DEFAULT = GameRules()
_NO_SURRENDER = GameRules(allow_surrender=False)


@given(hand=_player_hand(), upcard=cards)
@settings(max_examples=100)
def test_recommendation_is_always_legal(hand: Hand, upcard: Card) -> None:
    """Whatever recommend returns must be in the legal-actions set."""
    state = _state(hand, upcard, rules=_DEFAULT)
    assume(state.legal_actions())  # skip already-finished hands
    rec = recommend(state)
    assert rec in state.legal_actions(), (
        f"{rec} not legal for hand {hand.cards} vs {upcard}; "
        f"legal: {state.legal_actions()}"
    )


@given(hand=_player_hand(), upcard=cards)
@settings(max_examples=100)
def test_recommendation_stable_under_card_permutation(
    hand: Hand, upcard: Card
) -> None:
    """Permuting hand cards must not change the recommendation."""
    state1 = _state(hand, upcard, rules=_DEFAULT)
    permuted = dc_replace(hand, cards=tuple(reversed(hand.cards)))
    state2 = _state(permuted, upcard, rules=_DEFAULT)
    assume(state1.legal_actions())
    assume(state2.legal_actions())
    assert recommend(state1) == recommend(state2)


@given(hand=_player_hand(), upcard=cards)
@settings(max_examples=100)
def test_surrender_only_when_rule_allows(hand: Hand, upcard: Card) -> None:
    """If the variant disables surrender, it must never be recommended."""
    state = _state(hand, upcard, rules=_NO_SURRENDER)
    assume(state.legal_actions())
    rec = recommend(state)
    assert rec is not Action.SURRENDER
