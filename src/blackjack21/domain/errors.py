"""Domain-level exceptions for blackjack21."""

from __future__ import annotations


class BlackjackError(Exception):
    """Base class for any domain-level error."""


class InvalidBetError(BlackjackError):
    """Raised when a bet violates the rules (range or bankroll)."""


class InvalidActionError(BlackjackError):
    """Raised when an action is illegal in the current state."""


class DeckExhaustedError(BlackjackError):
    """Raised when the deck cannot satisfy a draw, even after reshuffle."""


class SessionCorruptError(BlackjackError):
    """Raised when a persisted session cannot be decoded safely."""
