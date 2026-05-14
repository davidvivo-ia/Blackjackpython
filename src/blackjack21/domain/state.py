"""Game state machine.

A ``GameState`` is an immutable snapshot of a session: bankroll, deck,
dealer hand, player hands and the current phase. Every transition is
a free function that returns a fresh state.

The state machine is intentionally narrow. The application layer is in
charge of looping over user input and pushing actions through
:func:`apply_action`, then calling :func:`resolve_round` once the
player has finished acting.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum

from blackjack21.domain.actions import Action, legal_actions
from blackjack21.domain.cards import Card, Rank
from blackjack21.domain.dealer import play_dealer
from blackjack21.domain.deck import Deck
from blackjack21.domain.errors import InvalidActionError
from blackjack21.domain.hand import Hand
from blackjack21.domain.outcomes import Settlement, settle
from blackjack21.domain.rules import GameRules
from blackjack21.domain.shuffler import Shuffler


class Phase(StrEnum):
    """High-level state of the table."""

    AWAITING_BET = "awaiting_bet"
    AWAITING_INSURANCE = "awaiting_insurance"
    PLAYER_TURN = "player_turn"
    DEALER_TURN = "dealer_turn"
    HAND_RESOLVED = "hand_resolved"
    GAME_OVER = "game_over"


@dataclass(frozen=True, slots=True)
class GameState:
    """Immutable snapshot of a session."""

    rules: GameRules
    bankroll: int
    deck: Deck
    dealer: Hand = field(default_factory=Hand)
    player_hands: tuple[Hand, ...] = field(default_factory=tuple)
    active_hand_index: int = 0
    insurance_bet: int = 0
    phase: Phase = Phase.AWAITING_BET
    settlements: tuple[Settlement, ...] = field(default_factory=tuple)
    hands_played: int = 0
    blackjacks: int = 0

    @property
    def active_hand(self) -> Hand:
        return self.player_hands[self.active_hand_index]

    @property
    def is_game_over(self) -> bool:
        return self.phase is Phase.GAME_OVER

    def legal_actions(self) -> frozenset[Action]:
        """Actions legal right now on the active hand."""
        if self.phase is not Phase.PLAYER_TURN:
            return frozenset()
        return legal_actions(
            self.active_hand,
            bankroll=self.bankroll,
            allow_surrender=self.rules.allow_surrender,
        )


def start_session(
    *, rules: GameRules, shuffler: Shuffler, bankroll: int | None = None
) -> GameState:
    """Build a fresh session with a shuffled deck."""
    starting = bankroll if bankroll is not None else rules.initial_bankroll
    return GameState(
        rules=rules,
        bankroll=starting,
        deck=Deck.fresh(shuffler, num_decks=rules.num_decks),
        phase=Phase.AWAITING_BET,
    )


def place_bet_and_deal(state: GameState, bet: int, *, shuffler: Shuffler) -> GameState:
    """Place ``bet``, deal two cards to player and dealer, advance phase."""
    if state.phase is not Phase.AWAITING_BET:
        raise InvalidActionError(f"Cannot place a bet from phase {state.phase}.")
    state.rules.validate_bet(bet, bankroll=state.bankroll)

    deck = state.deck
    player = Hand(bet=bet)
    dealer = Hand()

    for _ in range(2):
        card, deck = deck.draw(shuffler)
        player = player.add(card)
        card, deck = deck.draw(shuffler)
        dealer = dealer.add(card)

    new = replace(
        state,
        deck=deck,
        dealer=dealer,
        player_hands=(player,),
        active_hand_index=0,
        insurance_bet=0,
        settlements=(),
    )
    return _post_deal_phase(new)


def _post_deal_phase(state: GameState) -> GameState:
    dealer_up = state.dealer.cards[0]
    if dealer_up.rank is Rank.ACE:
        return replace(state, phase=Phase.AWAITING_INSURANCE)
    if state.dealer.value.is_blackjack or state.active_hand.value.is_blackjack:
        return replace(state, phase=Phase.DEALER_TURN)
    return replace(state, phase=Phase.PLAYER_TURN)


def resolve_insurance(state: GameState, insurance_bet: int) -> GameState:
    """Apply the insurance side-bet (0 means decline)."""
    if state.phase is not Phase.AWAITING_INSURANCE:
        raise InvalidActionError(f"Insurance not available in phase {state.phase}.")
    if insurance_bet < 0:
        raise InvalidActionError("Insurance bet must be non-negative.")
    max_insurance = state.active_hand.bet // 2
    if insurance_bet > max_insurance:
        raise InvalidActionError(
            f"Insurance bet {insurance_bet} exceeds half of the original "
            f"bet ({max_insurance})."
        )
    if insurance_bet > state.bankroll:
        raise InvalidActionError("Cannot afford insurance bet.")
    new = replace(state, insurance_bet=insurance_bet)
    if new.dealer.value.is_blackjack or new.active_hand.value.is_blackjack:
        return replace(new, phase=Phase.DEALER_TURN)
    return replace(new, phase=Phase.PLAYER_TURN)


def apply_action(state: GameState, action: Action, *, shuffler: Shuffler) -> GameState:
    """Apply a player action to the active hand."""
    if state.phase is not Phase.PLAYER_TURN:
        raise InvalidActionError(f"No player action allowed in phase {state.phase}.")
    if action not in state.legal_actions():
        raise InvalidActionError(f"Action {action} is not legal on the current hand.")
    match action:
        case Action.HIT:
            return _apply_hit(state, shuffler=shuffler)
        case Action.STAND:
            return _advance_or_dealer(_replace_active(state, state.active_hand.stand()))
        case Action.DOUBLE:
            return _apply_double(state, shuffler=shuffler)
        case Action.SPLIT:
            return _apply_split(state, shuffler=shuffler)
        case Action.SURRENDER:
            return _advance_or_dealer(
                _replace_active(state, state.active_hand.surrender())
            )


def _apply_hit(state: GameState, *, shuffler: Shuffler) -> GameState:
    card, deck = state.deck.draw(shuffler)
    updated = state.active_hand.add(card)
    state2 = replace(_replace_active(state, updated), deck=deck)
    if state2.active_hand.is_finished:
        return _advance_or_dealer(state2)
    return state2


def _apply_double(state: GameState, *, shuffler: Shuffler) -> GameState:
    card, deck = state.deck.draw(shuffler)
    updated = state.active_hand.add(card).double()
    state2 = replace(_replace_active(state, updated), deck=deck)
    return _advance_or_dealer(state2)


def _apply_split(state: GameState, *, shuffler: Shuffler) -> GameState:
    original = state.active_hand
    first_card, second_card = original.cards
    base_bet = original.bet

    left = Hand(cards=(first_card,), bet=base_bet, from_split=True)
    right = Hand(cards=(second_card,), bet=base_bet, from_split=True)

    new_card, deck = state.deck.draw(shuffler)
    left = left.add(new_card)
    new_card, deck = deck.draw(shuffler)
    right = right.add(new_card)

    hands = list(state.player_hands)
    hands[state.active_hand_index] = left
    hands.insert(state.active_hand_index + 1, right)

    state2 = replace(state, deck=deck, player_hands=tuple(hands))
    if state2.active_hand.is_finished:
        return _advance_or_dealer(state2)
    return state2


def _replace_active(state: GameState, hand: Hand) -> GameState:
    hands = list(state.player_hands)
    hands[state.active_hand_index] = hand
    return replace(state, player_hands=tuple(hands))


def _advance_or_dealer(state: GameState) -> GameState:
    next_index = state.active_hand_index + 1
    while next_index < len(state.player_hands):
        if not state.player_hands[next_index].is_finished:
            return replace(state, active_hand_index=next_index, phase=Phase.PLAYER_TURN)
        next_index += 1
    return replace(state, phase=Phase.DEALER_TURN)


def resolve_round(state: GameState, *, shuffler: Shuffler) -> GameState:
    """Play out the dealer (if needed) and settle every player hand."""
    if state.phase is not Phase.DEALER_TURN:
        raise InvalidActionError(
            f"resolve_round called in unexpected phase {state.phase}."
        )

    needs_dealer = any(
        not (h.value.is_bust or h.surrendered) for h in state.player_hands
    )
    if state.dealer.value.is_blackjack:
        needs_dealer = False

    dealer_final = state.dealer
    deck = state.deck
    if needs_dealer:
        dealer_final, deck = play_dealer(
            state.dealer, state.deck, rules=state.rules, shuffler=shuffler
        )

    settlements = tuple(
        settle(
            player=hand,
            dealer=dealer_final,
            insurance_bet=state.insurance_bet if i == 0 else 0,
        )
        for i, hand in enumerate(state.player_hands)
    )

    bankroll_delta = sum(s.net + s.insurance_net for s in settlements)
    new_bankroll = state.bankroll + bankroll_delta

    blackjacks = state.blackjacks + sum(
        1 for h in state.player_hands if h.value.is_blackjack
    )

    next_phase = (
        Phase.GAME_OVER if new_bankroll < state.rules.min_bet else Phase.HAND_RESOLVED
    )

    return replace(
        state,
        dealer=dealer_final,
        deck=deck.discard_cards(_collect_discards(state.player_hands, dealer_final)),
        settlements=settlements,
        bankroll=new_bankroll,
        hands_played=state.hands_played + 1,
        blackjacks=blackjacks,
        phase=next_phase,
    )


def _collect_discards(player_hands: tuple[Hand, ...], dealer: Hand) -> tuple[Card, ...]:
    pieces: list[Card] = []
    for hand in player_hands:
        pieces.extend(hand.cards)
    pieces.extend(dealer.cards)
    return tuple(pieces)


def begin_next_hand(state: GameState) -> GameState:
    """Reset the table for another deal, keeping bankroll and stats."""
    if state.phase is not Phase.HAND_RESOLVED:
        raise InvalidActionError(f"Cannot begin a new hand from phase {state.phase}.")
    return replace(
        state,
        dealer=Hand(),
        player_hands=(),
        active_hand_index=0,
        insurance_bet=0,
        settlements=(),
        phase=Phase.AWAITING_BET,
    )
