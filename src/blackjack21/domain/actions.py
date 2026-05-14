"""Player actions and their predicates."""

from __future__ import annotations

from enum import StrEnum

from blackjack21.domain.hand import Hand


class Action(StrEnum):
    """A choice the player can make on their turn."""

    HIT = "hit"
    STAND = "stand"
    DOUBLE = "double"
    SPLIT = "split"
    SURRENDER = "surrender"


def legal_actions(
    hand: Hand,
    *,
    bankroll: int,
    allow_surrender: bool = True,
) -> frozenset[Action]:
    """Return the set of actions legal on ``hand`` given ``bankroll``.

    A player can always hit or stand on a live hand. They can double
    on the first two cards as long as they can afford it. They can
    split a pair (also subject to bankroll). Late surrender is legal
    only on the first decision of a non-split hand.
    """
    if hand.is_finished:
        return frozenset()
    actions: set[Action] = {Action.HIT, Action.STAND}
    is_first_decision = len(hand.cards) == 2 and not hand.stood and not hand.doubled
    if is_first_decision and bankroll >= hand.bet:
        actions.add(Action.DOUBLE)
    if (
        is_first_decision
        and hand.is_pair
        and not hand.from_split
        and bankroll >= hand.bet
    ):
        actions.add(Action.SPLIT)
    if is_first_decision and allow_surrender and not hand.from_split:
        actions.add(Action.SURRENDER)
    return frozenset(actions)
