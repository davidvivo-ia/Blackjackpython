"""Saved session model and stats."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SessionStats(BaseModel):
    """Aggregate stats across all hands played."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    hands_played: int = 0
    blackjacks: int = 0
    biggest_pot: int = 0


class SavedSession(BaseModel):
    """The slice of state we persist between runs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    bankroll: int = Field(ge=0)
    stats: SessionStats = SessionStats()
    schema_version: int = 1
