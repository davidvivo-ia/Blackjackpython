"""Basic Strategy recommender for blackjack21.

Single deck, dealer stands on soft 17 (S17), double after split allowed,
no surrender. This is the textbook chart from Thorp / Wong adapted for
single-deck S17, the variant our domain rules describe in
:mod:`blackjack21.domain.rules`.

The function :func:`recommend` is pure: given a state snapshot, it
returns the action a perfect basic-strategy player would take, falling
back gracefully when the recommendation isn't legal (e.g. doubling is
only allowed on the first decision).

This module is deliberately decoupled from the TUI and from the demo
strategy. Both can call it, neither owns it.
"""

from __future__ import annotations

from blackjack21.domain.actions import Action
from blackjack21.domain.cards import Rank
from blackjack21.domain.hand import Hand
from blackjack21.domain.state import GameState, Phase


def recommend(state: GameState) -> Action:
    """Return the basic-strategy action for the player's current decision.

    Caller must ensure ``state.phase is Phase.PLAYER_TURN``. If called
    outside that phase, falls back to ``Action.STAND``.
    """
    if state.phase is not Phase.PLAYER_TURN or not state.player_hands:
        return Action.STAND
    hand = state.active_hand
    upcard = state.dealer.cards[0]
    upcard_value = _upcard_value(upcard.rank)
    legal = state.legal_actions()

    desired = _ideal_action(hand, upcard_value)
    return _fallback(desired, legal)


def _upcard_value(rank: Rank) -> int:
    """Return the basic-strategy value of the dealer upcard.

    Aces are encoded as 11 because the strategy tables key off the soft
    upcard total ("A" column), not the hard value 1.
    """
    if rank is Rank.ACE:
        return 11
    return rank.hard_value


def _ideal_action(hand: Hand, upcard: int) -> Action:
    """Pick the textbook action, ignoring legality."""
    if hand.is_pair:
        pair_rank = hand.cards[0].rank.hard_value
        return _pair_action(pair_rank, upcard)
    value = hand.value
    if value.is_soft:
        return _soft_action(value.total, upcard)
    return _hard_action(value.total, upcard)


def _pair_action(pair_rank: int, upcard: int) -> Action:
    """Pair-splitting matrix.

    ``pair_rank`` is the hard value of one of the two paired cards
    (Ace = 1; ten-valued cards = 10, lumped together for splitting).
    """
    # Always split Aces and 8s.
    if pair_rank == 1:
        return Action.SPLIT
    if pair_rank == 8:
        return Action.SPLIT
    # Never split 5s (play as a hard 10) or any ten-valued pair.
    if pair_rank == 5:
        return _hard_action(10, upcard)
    if pair_rank == 10:
        return _hard_action(20, upcard)
    # Split 2-2, 3-3, 7-7 against dealer 2-7.
    if pair_rank in (2, 3, 7) and 2 <= upcard <= 7:
        return Action.SPLIT
    # Split 4-4 only against dealer 5 or 6.
    if pair_rank == 4 and upcard in (5, 6):
        return Action.SPLIT
    # Split 6-6 against dealer 2-6.
    if pair_rank == 6 and 2 <= upcard <= 6:
        return Action.SPLIT
    # Split 9-9 against dealer 2-6, 8, 9. Stand against 7, 10, A.
    if pair_rank == 9:
        if upcard in (7, 10, 11):
            return Action.STAND
        return Action.SPLIT
    # Default for unmatched pair scenarios: treat as the same hard total.
    return _hard_action(pair_rank * 2, upcard)


def _soft_action(total: int, upcard: int) -> Action:
    """Soft-total chart (Ace counted as 11)."""
    if total >= 20:
        return Action.STAND
    if total == 19:
        return Action.STAND
    if total == 18:
        if upcard in (3, 4, 5, 6):
            return Action.DOUBLE
        if upcard in (2, 7, 8):
            return Action.STAND
        # 9, 10, A: hit
        return Action.HIT
    if total == 17:
        if upcard in (3, 4, 5, 6):
            return Action.DOUBLE
        return Action.HIT
    if total in (15, 16):
        if upcard in (4, 5, 6):
            return Action.DOUBLE
        return Action.HIT
    if total in (13, 14):
        if upcard in (5, 6):
            return Action.DOUBLE
        return Action.HIT
    # Soft 12 only happens as A+A, handled by the pair branch.
    return Action.HIT


def _hard_action(total: int, upcard: int) -> Action:
    """Hard-total chart."""
    if total >= 17:
        return Action.STAND
    if 13 <= total <= 16:
        if 2 <= upcard <= 6:
            return Action.STAND
        return Action.HIT
    if total == 12:
        if 4 <= upcard <= 6:
            return Action.STAND
        return Action.HIT
    if total == 11:
        return Action.DOUBLE
    if total == 10:
        if upcard in (10, 11):
            return Action.HIT
        return Action.DOUBLE
    if total == 9:
        if 3 <= upcard <= 6:
            return Action.DOUBLE
        return Action.HIT
    return Action.HIT


def _fallback(desired: Action, legal: frozenset[Action] | set[Action]) -> Action:
    """If the ideal action is illegal, degrade gracefully.

    DOUBLE without first-card privilege → HIT.
    SPLIT when not a pair → fall back to the next sensible move (HIT or
    STAND depending on whether the recommendation came from a stiff).
    """
    if desired in legal:
        return desired
    if desired is Action.DOUBLE:
        return Action.HIT if Action.HIT in legal else Action.STAND
    if desired is Action.SPLIT:
        return Action.HIT if Action.HIT in legal else Action.STAND
    return desired
