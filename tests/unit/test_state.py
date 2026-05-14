"""State machine tests."""

from __future__ import annotations

import pytest

from blackjack21.domain.actions import Action
from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.domain.deck import Deck
from blackjack21.domain.errors import InvalidActionError, InvalidBetError
from blackjack21.domain.outcomes import Outcome
from blackjack21.domain.rules import DEFAULT_RULES, GameRules
from blackjack21.domain.state import (
    GameState,
    Phase,
    apply_action,
    begin_next_hand,
    place_bet_and_deal,
    resolve_insurance,
    resolve_round,
    start_session,
)
from blackjack21.infrastructure.rng import FixedOrderShuffler, IdentityShuffler

S = Suit.SPADES
H = Suit.HEARTS
D = Suit.DIAMONDS
C = Suit.CLUBS


def card(rank: Rank, suit: Suit = S) -> Card:
    return Card(rank, suit)


def stack(*cards: Card) -> Deck:
    """Build a deck whose top is the first argument."""
    return Deck(cards=cards)


def state_with(*cards: Card, bankroll: int = 1000) -> GameState:
    """Build a deterministic state using a deck stacked top-first."""
    return GameState(
        rules=DEFAULT_RULES,
        bankroll=bankroll,
        deck=stack(*cards),
        phase=Phase.AWAITING_BET,
    )


def test_start_session_uses_initial_bankroll() -> None:
    s = start_session(rules=DEFAULT_RULES, shuffler=IdentityShuffler())
    assert s.bankroll == DEFAULT_RULES.initial_bankroll
    assert s.phase is Phase.AWAITING_BET
    assert s.deck.remaining == 52


def test_place_bet_and_deal_advances_to_player_turn() -> None:
    s0 = state_with(
        card(Rank.NINE),
        card(Rank.KING, H),
        card(Rank.SEVEN),
        card(Rank.SIX, D),
    )
    s1 = place_bet_and_deal(s0, 10, shuffler=IdentityShuffler())
    assert s1.phase is Phase.PLAYER_TURN
    assert s1.active_hand.cards == (card(Rank.NINE), card(Rank.SEVEN))
    assert s1.dealer.cards == (card(Rank.KING, H), card(Rank.SIX, D))


def test_bet_rejected_outside_bounds() -> None:
    s = state_with(card(Rank.NINE), card(Rank.SEVEN), card(Rank.KING), card(Rank.SIX))
    with pytest.raises(InvalidBetError):
        place_bet_and_deal(s, 0, shuffler=IdentityShuffler())
    with pytest.raises(InvalidBetError):
        place_bet_and_deal(s, 9999, shuffler=IdentityShuffler())


def test_dealer_ace_triggers_insurance_phase() -> None:
    s0 = state_with(
        card(Rank.NINE), card(Rank.ACE, H), card(Rank.SEVEN), card(Rank.SIX, D)
    )
    s1 = place_bet_and_deal(s0, 10, shuffler=IdentityShuffler())
    assert s1.phase is Phase.AWAITING_INSURANCE


def test_resolve_insurance_no_bet_advances_to_player_turn() -> None:
    s0 = state_with(
        card(Rank.NINE), card(Rank.ACE, H), card(Rank.SEVEN), card(Rank.SIX, D)
    )
    s1 = place_bet_and_deal(s0, 10, shuffler=IdentityShuffler())
    s2 = resolve_insurance(s1, 0)
    assert s2.phase is Phase.PLAYER_TURN
    assert s2.insurance_bet == 0


def test_hit_until_bust() -> None:
    # Deal order is P, D, P, D, ...
    s0 = state_with(
        card(Rank.KING),  # player1
        card(Rank.QUEEN, D),  # dealer1
        card(Rank.FIVE, H),  # player2 -> player K,5 = 15
        card(Rank.SIX, C),  # dealer2 -> dealer Q,6 = 16
        card(Rank.NINE),  # player hit -> K,5,9 = 24 bust
        card(Rank.FIVE, D),  # dealer hit -> 16+5 = 21
    )
    s1 = place_bet_and_deal(s0, 10, shuffler=IdentityShuffler())
    s2 = apply_action(s1, Action.HIT, shuffler=IdentityShuffler())
    assert s2.active_hand.value.is_bust
    assert s2.phase is Phase.DEALER_TURN
    s3 = resolve_round(s2, shuffler=IdentityShuffler())
    assert s3.phase is Phase.HAND_RESOLVED
    assert s3.settlements[0].outcome is Outcome.BUST


def test_stand_then_dealer_resolves_round() -> None:
    s0 = state_with(
        card(Rank.KING),  # player1
        card(Rank.NINE, D),  # dealer1
        card(Rank.KING, H),  # player2 -> K,K = 20
        card(Rank.SEVEN, C),  # dealer2 -> 9,7 = 16
        card(Rank.FIVE),  # dealer hit -> 21
    )
    s1 = place_bet_and_deal(s0, 10, shuffler=IdentityShuffler())
    s2 = apply_action(s1, Action.STAND, shuffler=IdentityShuffler())
    s3 = resolve_round(s2, shuffler=IdentityShuffler())
    assert s3.dealer.value.total == 21
    assert s3.settlements[0].outcome is Outcome.LOSS


def test_double_doubles_bet_and_takes_one_card() -> None:
    s0 = state_with(
        card(Rank.SIX),  # player1
        card(Rank.KING, D),  # dealer1
        card(Rank.NINE, H),  # player2 -> 6,9 = 15
        card(Rank.SIX, C),  # dealer2 -> K,6 = 16
        card(Rank.FIVE),  # player double card -> 20
        card(Rank.NINE, C),  # dealer hit -> 25 bust
    )
    s1 = place_bet_and_deal(s0, 50, shuffler=IdentityShuffler())
    s2 = apply_action(s1, Action.DOUBLE, shuffler=IdentityShuffler())
    assert s2.player_hands[0].bet == 100
    assert s2.phase is Phase.DEALER_TURN
    s3 = resolve_round(s2, shuffler=IdentityShuffler())
    assert s3.settlements[0].outcome is Outcome.WIN
    assert s3.settlements[0].net == 100


def test_split_creates_two_hands_with_one_card_each() -> None:
    s0 = state_with(
        card(Rank.EIGHT),  # player1
        card(Rank.KING, D),  # dealer1
        card(Rank.EIGHT, H),  # player2 -> pair of 8s
        card(Rank.SIX, C),  # dealer2 -> K,6 = 16
        card(Rank.TWO),  # first split hand draws -> 8,2 = 10
        card(Rank.NINE),  # second split hand draws -> 8,9 = 17
        card(Rank.QUEEN),
        card(Rank.FIVE, C),
        card(Rank.FIVE, D),
        card(Rank.FIVE, H),
    )
    s1 = place_bet_and_deal(s0, 10, shuffler=IdentityShuffler())
    assert Action.SPLIT in s1.legal_actions()
    s2 = apply_action(s1, Action.SPLIT, shuffler=IdentityShuffler())
    assert len(s2.player_hands) == 2
    assert s2.player_hands[0].bet == 10
    assert s2.player_hands[1].bet == 10
    assert s2.player_hands[0].from_split
    assert s2.player_hands[1].from_split


def test_natural_blackjack_skips_player_turn() -> None:
    s0 = state_with(
        card(Rank.ACE),  # player1
        card(Rank.KING, D),  # dealer1
        card(Rank.KING, H),  # player2 -> A,K natural BJ
        card(Rank.NINE, C),  # dealer2 -> K,9 = 19
    )
    s1 = place_bet_and_deal(s0, 10, shuffler=IdentityShuffler())
    assert s1.phase is Phase.DEALER_TURN
    s2 = resolve_round(s1, shuffler=IdentityShuffler())
    assert s2.settlements[0].outcome is Outcome.BLACKJACK
    assert s2.settlements[0].net == 15


def test_begin_next_hand_resets_table() -> None:
    s0 = state_with(
        card(Rank.KING),
        card(Rank.NINE, D),
        card(Rank.KING, H),
        card(Rank.NINE, C),
    )
    s1 = place_bet_and_deal(s0, 10, shuffler=IdentityShuffler())
    s2 = apply_action(s1, Action.STAND, shuffler=IdentityShuffler())
    s3 = resolve_round(s2, shuffler=IdentityShuffler())
    s4 = begin_next_hand(s3)
    assert s4.phase is Phase.AWAITING_BET
    assert s4.player_hands == ()
    assert s4.dealer.cards == ()


def test_game_over_when_bankroll_falls_below_min_bet() -> None:
    rules = GameRules(initial_bankroll=10, min_bet=10, max_bet=10)
    deck = stack(
        card(Rank.KING),  # player1
        card(Rank.KING, H),  # dealer1
        card(Rank.KING, D),  # player2 -> K,K = 20
        card(Rank.ACE),  # dealer2 -> K,A natural blackjack
    )
    s0 = GameState(rules=rules, bankroll=10, deck=deck)
    s1 = place_bet_and_deal(s0, 10, shuffler=IdentityShuffler())
    s2 = resolve_round(s1, shuffler=IdentityShuffler())
    assert s2.is_game_over


def test_apply_action_in_wrong_phase_raises() -> None:
    s = start_session(rules=DEFAULT_RULES, shuffler=IdentityShuffler())
    with pytest.raises(InvalidActionError):
        apply_action(s, Action.HIT, shuffler=IdentityShuffler())


def test_fixed_order_shuffler_round_trip() -> None:
    cards = (card(Rank.ACE), card(Rank.TWO), card(Rank.THREE))
    sh = FixedOrderShuffler(cards)
    assert sh.shuffled(cards) == cards
    with pytest.raises(ValueError, match="does not match"):
        sh.shuffled((card(Rank.ACE),))
