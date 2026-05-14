"""Coverage for the ``blackjack21 scores`` subcommand."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from blackjack21.application.session import SavedSession, SessionStats
from blackjack21.infrastructure.persistence import JsonSessionStore
from blackjack21.presentation.cli import app

runner = CliRunner()


def _seed_profile(tmp_path: Path, *, name: str, payload: SavedSession) -> None:
    """Write ``payload`` as the session file for profile ``name``."""
    if name == "default":
        path = tmp_path / "session.json"
    else:
        path = tmp_path / "profiles" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    JsonSessionStore(path).save(payload)


def test_scores_says_no_session_for_unknown_profile(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    result = runner.invoke(app, ["scores", "--profile", "ghost"])
    assert result.exit_code == 0
    assert "No session yet" in result.stdout


def test_scores_renders_stats_and_achievements(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "blackjack21"))
    saved = SavedSession(
        bankroll=1500,
        stats=SessionStats(
            hands_played=42,
            blackjacks=3,
            biggest_pot=800,
            longest_win_streak=6,
            max_bankroll_reached=2000,
            lowest_bankroll=350,
            times_bet_max=5,
        ),
        unlocked_achievements=["first_bj", "streak_5", "big_pot"],
    )
    _seed_profile(
        tmp_path / "blackjack21" / "blackjack21",
        name="alice",
        payload=saved,
    )
    result = runner.invoke(app, ["scores", "--profile", "alice"])
    assert result.exit_code == 0, result.stdout
    assert "HALL OF FAME" in result.stdout
    assert "alice" in result.stdout
    assert "$1,500" in result.stdout
    # Three achievements unlocked → at least three star markers visible.
    assert result.stdout.count("★") >= 3
    # The remaining four still show in the table.
    assert "Whale" in result.stdout


def test_scores_handles_corrupt_session(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "blackjack21"))
    profile_dir = tmp_path / "blackjack21" / "blackjack21" / "profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "broken.json").write_text("{not-json", encoding="utf-8")
    result = runner.invoke(app, ["scores", "--profile", "broken"])
    assert result.exit_code == 1
    assert "Could not load" in result.stdout
