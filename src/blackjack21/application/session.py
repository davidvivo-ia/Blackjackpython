"""Saved session model and stats."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SessionStats(BaseModel):
    """Aggregate stats across all hands played.

    New fields added for D-phase achievements are optional with sane
    defaults so v1.0 session files load unchanged.
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    hands_played: int = 0
    blackjacks: int = 0
    biggest_pot: int = 0
    longest_win_streak: int = 0
    max_bankroll_reached: int = 0
    lowest_bankroll: int | None = None
    times_bet_max: int = 0


class SavedSession(BaseModel):
    """The slice of state we persist between runs."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    bankroll: int = Field(ge=0)
    stats: SessionStats = SessionStats()
    schema_version: int = 1
    unlocked_achievements: list[str] = Field(default_factory=list)
