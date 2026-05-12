"""Configurable rules (constants by default, frozen)."""

from __future__ import annotations

from dataclasses import dataclass

from blackjack21.domain.errors import InvalidBetError


@dataclass(frozen=True, slots=True)
class GameRules:
    """Knobs that shape a session.

    Defaults reproduce the BASIC original: minimum bet 1, maximum bet
    500, dealer stands on soft 17. ``initial_bankroll`` is a 2026
    addition since the original carried over only via terminal session
    memory.
    """

    min_bet: int = 1
    max_bet: int = 500
    initial_bankroll: int = 1000
    dealer_stands_on: int = 17
    dealer_hits_soft_17: bool = False  # S17, like the original
    blackjack_pays_numerator: int = 3
    blackjack_pays_denominator: int = 2

    def validate_bet(self, bet: int, *, bankroll: int) -> None:
        """Raise :class:`InvalidBetError` if ``bet`` is illegal."""
        if bet < self.min_bet:
            raise InvalidBetError(f"Bet {bet} below minimum {self.min_bet}.")
        if bet > self.max_bet:
            raise InvalidBetError(f"Bet {bet} above maximum {self.max_bet}.")
        if bet > bankroll:
            raise InvalidBetError(f"Bet {bet} exceeds bankroll {bankroll}.")


DEFAULT_RULES: GameRules = GameRules()
