"""Outcomes of a single hand and the settlement logic.

The original program lumps wins, pushes and losses in a single signed
total. Here we surface the discrete outcome alongside the net change
so the presentation layer can show distinct banners.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from blackjack21.domain.hand import Hand

BLACKJACK_PAYOUT: Fraction = Fraction(3, 2)


class Outcome(StrEnum):
    """Discrete outcome of a settled hand."""

    BLACKJACK = "blackjack"
    WIN = "win"
    PUSH = "push"
    LOSS = "loss"
    BUST = "bust"
    SURRENDER = "surrender"


@dataclass(frozen=True, slots=True)
class Settlement:
    """Result of settling one player hand against the dealer."""

    outcome: Outcome
    net: int  # signed delta on the player's bankroll (excludes original bet)
    insurance_net: int = 0


def settle(
    *,
    player: Hand,
    dealer: Hand,
    insurance_bet: int = 0,
) -> Settlement:
    """Compute the settlement of ``player`` against ``dealer``.

    ``net`` is the signed change in the player's bankroll *exclusive*
    of the original bet, mirroring how blackjack tables pay.

    A natural blackjack pays 3:2 (rounded down to an integer for the
    bankroll, but kept exact while computing). The optional
    ``insurance_bet`` doubles the player's wager against the dealer
    showing an Ace and pays 2:1 if the dealer ends with a natural.
    """
    pv = player.value
    dv = dealer.value
    insurance_net = _insurance_payoff(insurance_bet=insurance_bet, dealer=dealer)
    if player.surrendered:
        return Settlement(
            outcome=Outcome.SURRENDER,
            net=-(player.bet // 2),
            insurance_net=insurance_net,
        )
    if pv.is_bust:
        return Settlement(
            outcome=Outcome.BUST, net=-player.bet, insurance_net=insurance_net
        )
    if pv.is_blackjack and not dv.is_blackjack:
        payout = int(BLACKJACK_PAYOUT * player.bet)
        return Settlement(
            outcome=Outcome.BLACKJACK,
            net=payout,
            insurance_net=insurance_net,
        )
    if dv.is_blackjack and not pv.is_blackjack:
        return Settlement(
            outcome=Outcome.LOSS, net=-player.bet, insurance_net=insurance_net
        )
    if pv.is_blackjack and dv.is_blackjack:
        return Settlement(outcome=Outcome.PUSH, net=0, insurance_net=insurance_net)
    if dv.is_bust or pv.total > dv.total:
        return Settlement(
            outcome=Outcome.WIN, net=player.bet, insurance_net=insurance_net
        )
    if pv.total < dv.total:
        return Settlement(
            outcome=Outcome.LOSS, net=-player.bet, insurance_net=insurance_net
        )
    return Settlement(outcome=Outcome.PUSH, net=0, insurance_net=insurance_net)


def _insurance_payoff(*, insurance_bet: int, dealer: Hand) -> int:
    if insurance_bet <= 0:
        return 0
    if dealer.value.is_blackjack:
        return insurance_bet * 2
    return -insurance_bet
