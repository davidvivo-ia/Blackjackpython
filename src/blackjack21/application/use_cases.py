"""High-level use cases that orchestrate the domain.

The TUI calls these functions; they return the new ``GameState`` plus
the emitted ``GameEvent`` list so callers can render animations.
"""

from __future__ import annotations

from blackjack21.application.events import (
    BetPlaced,
    CardDealt,
    DealerRevealed,
    GameEvent,
    HandResolved,
    InsuranceOffered,
    InsuranceResolved,
    PlayerActed,
    SessionEnded,
)
from blackjack21.domain.actions import Action
from blackjack21.domain.shuffler import Shuffler
from blackjack21.domain.state import (
    GameState,
    Phase,
    apply_action,
    begin_next_hand,
    place_bet_and_deal,
    resolve_insurance,
    resolve_round,
)


def deal_hand(
    state: GameState, bet: int, *, shuffler: Shuffler
) -> tuple[GameState, list[GameEvent]]:
    """Place a bet and deal initial cards, emitting their events."""
    new_state = place_bet_and_deal(state, bet, shuffler=shuffler)
    events: list[GameEvent] = [BetPlaced(bet=bet, bankroll=new_state.bankroll)]
    player_hand = new_state.player_hands[0]
    dealer = new_state.dealer
    events.extend(
        [
            CardDealt(card=player_hand.cards[0], to="player"),
            CardDealt(card=dealer.cards[0], to="dealer"),
            CardDealt(card=player_hand.cards[1], to="player"),
            CardDealt(card=dealer.cards[1], to="dealer", hidden=True),
        ]
    )
    if new_state.phase is Phase.AWAITING_INSURANCE:
        events.append(InsuranceOffered(max_insurance=bet // 2))
    return new_state, events


def take_insurance(
    state: GameState, insurance_bet: int
) -> tuple[GameState, list[GameEvent]]:
    """Process the insurance decision."""
    new_state = resolve_insurance(state, insurance_bet)
    events: list[GameEvent] = []
    if insurance_bet > 0 and new_state.phase is Phase.DEALER_TURN:
        # Dealer will reveal blackjack: insurance pays.
        won = new_state.dealer.value.is_blackjack
        events.append(InsuranceResolved(insurance_bet=insurance_bet, won=won))
    return new_state, events


def player_action(
    state: GameState, action: Action, *, shuffler: Shuffler
) -> tuple[GameState, list[GameEvent]]:
    """Apply a player action and emit the resulting card events."""
    prior_hands = len(state.player_hands)
    new_state = apply_action(state, action, shuffler=shuffler)
    events: list[GameEvent] = [
        PlayerActed(action=action, hand_index=state.active_hand_index)
    ]
    if action in (Action.HIT, Action.DOUBLE):
        last_card = new_state.player_hands[state.active_hand_index].cards[-1]
        events.append(
            CardDealt(card=last_card, to="player", hand_index=state.active_hand_index)
        )
    elif action is Action.SPLIT and len(new_state.player_hands) > prior_hands:
        left = new_state.player_hands[state.active_hand_index]
        right = new_state.player_hands[state.active_hand_index + 1]
        events.append(
            CardDealt(
                card=left.cards[-1], to="player", hand_index=state.active_hand_index
            )
        )
        events.append(
            CardDealt(
                card=right.cards[-1],
                to="player",
                hand_index=state.active_hand_index + 1,
            )
        )
    return new_state, events


def finish_round(
    state: GameState, *, shuffler: Shuffler
) -> tuple[GameState, list[GameEvent]]:
    """Resolve the dealer and emit settlement events."""
    pre_dealer_card_count = len(state.dealer.cards)
    new_state = resolve_round(state, shuffler=shuffler)
    events: list[GameEvent] = [DealerRevealed(hole_card=state.dealer.cards[1])]
    for card in new_state.dealer.cards[pre_dealer_card_count:]:
        events.append(CardDealt(card=card, to="dealer"))
    bankroll_running = state.bankroll
    for index, settlement in enumerate(new_state.settlements):
        bankroll_running += settlement.net + settlement.insurance_net
        events.append(
            HandResolved(
                settlement=settlement,
                hand_index=index,
                bankroll_after=bankroll_running,
            )
        )
    if new_state.is_game_over:
        events.append(
            SessionEnded(final_bankroll=new_state.bankroll, reason="bankroll_exhausted")
        )
    return new_state, events


def next_hand(state: GameState) -> GameState:
    """Convenience wrapper for the state-machine reset between hands."""
    return begin_next_hand(state)
