"""Ports (Protocols) implemented by adapters in infrastructure/."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from blackjack21.application.session import SavedSession


@runtime_checkable
class SessionStore(Protocol):
    """Persistence backend for the player's session."""

    def load(self) -> SavedSession | None:
        """Return the saved session if any, else ``None``."""

    def save(self, session: SavedSession) -> None:
        """Persist ``session`` atomically."""

    def reset(self) -> None:
        """Delete the saved session, if any."""
