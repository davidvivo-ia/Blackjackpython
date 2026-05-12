"""Integration tests for the application layer."""

from __future__ import annotations

from blackjack21.application.events import (
    BetPlaced,
    CardDealt,
    DealerRevealed,
    HandResolved,
    PlayerActed,
)
from blackjack21.application.use_cases import (
    deal_hand,
    finish_round,
    next_hand,
    player_action,
)
from blackjack21.domain.actions import Action
from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.domain.deck import Deck
from blackjack21.domain.outcomes import Outcome
from blackjack21.domain.rules import DEFAULT_RULES
from blackjack21.domain.state import GameState, Phase
from blackjack21.infrastructure.rng import IdentityShuffler


def card(rank: Rank, suit: Suit = Suit.SPADES) -> Card:
    return Card(rank, suit)


def fixed_state(*cards: Card, bankroll: int = 1000) -> GameState:
    return GameState(
        rules=DEFAULT_RULES,
        bankroll=bankroll,
        deck=Deck(cards=cards),
        phase=Phase.AWAITING_BET,
    )


def test_deal_hand_emits_initial_events() -> None:
    state = fixed_state(
        card(Rank.NINE),
        card(Rank.KING, Suit.HEARTS),
        card(Rank.EIGHT),
        card(Rank.SIX, Suit.DIAMONDS),
    )
    new_state, events = deal_hand(state, bet=10, shuffler=IdentityShuffler())
    assert isinstance(events[0], BetPlaced)
    assert events[0].bet == 10
    assert sum(1 for e in events if isinstance(e, CardDealt)) == 4
    assert new_state.phase is Phase.PLAYER_TURN


def test_player_action_emits_card_for_hit() -> None:
    state = fixed_state(
        card(Rank.NINE),
        card(Rank.KING, Suit.HEARTS),
        card(Rank.FIVE),
        card(Rank.SIX, Suit.DIAMONDS),
        card(Rank.THREE),
    )
    new_state, _ = deal_hand(state, bet=10, shuffler=IdentityShuffler())
    after, events = player_action(new_state, Action.HIT, shuffler=IdentityShuffler())
    assert isinstance(events[0], PlayerActed)
    assert events[0].action is Action.HIT
    card_events = [e for e in events if isinstance(e, CardDealt)]
    assert len(card_events) == 1
    assert card_events[0].card == card(Rank.THREE)
    assert after.active_hand.value.total == 17


def test_finish_round_emits_dealer_reveal_and_settlement() -> None:
    state = fixed_state(
        card(Rank.KING),
        card(Rank.NINE, Suit.DIAMONDS),
        card(Rank.KING, Suit.HEARTS),
        card(Rank.SEVEN, Suit.CLUBS),
        card(Rank.FIVE),
    )
    s1, _ = deal_hand(state, bet=10, shuffler=IdentityShuffler())
    s2, _ = player_action(s1, Action.STAND, shuffler=IdentityShuffler())
    s3, events = finish_round(s2, shuffler=IdentityShuffler())
    assert isinstance(events[0], DealerRevealed)
    resolutions = [e for e in events if isinstance(e, HandResolved)]
    assert len(resolutions) == 1
    assert resolutions[0].settlement.outcome is Outcome.LOSS
    assert s3.phase is Phase.HAND_RESOLVED


def test_next_hand_clears_table() -> None:
    state = fixed_state(
        card(Rank.KING),
        card(Rank.NINE, Suit.DIAMONDS),
        card(Rank.KING, Suit.HEARTS),
        card(Rank.NINE, Suit.CLUBS),
    )
    s1, _ = deal_hand(state, bet=10, shuffler=IdentityShuffler())
    s2, _ = player_action(s1, Action.STAND, shuffler=IdentityShuffler())
    s3, _ = finish_round(s2, shuffler=IdentityShuffler())
    s4 = next_hand(s3)
    assert s4.phase is Phase.AWAITING_BET
