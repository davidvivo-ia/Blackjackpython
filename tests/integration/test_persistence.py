"""Persistence integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from blackjack21.application.session import SavedSession, SessionStats
from blackjack21.domain.errors import SessionCorruptError
from blackjack21.infrastructure.persistence import (
    InMemorySessionStore,
    JsonSessionStore,
)


def test_load_returns_none_when_no_file(tmp_path: Path) -> None:
    store = JsonSessionStore(tmp_path / "session.json")
    assert store.load() is None


def test_save_then_load_round_trip(tmp_path: Path) -> None:
    store = JsonSessionStore(tmp_path / "session.json")
    session = SavedSession(
        bankroll=750, stats=SessionStats(hands_played=12, blackjacks=2, biggest_pot=80)
    )
    store.save(session)
    loaded = store.load()
    assert loaded == session


def test_save_is_atomic_and_restricts_permissions(tmp_path: Path) -> None:
    path = tmp_path / "session.json"
    store = JsonSessionStore(path)
    store.save(SavedSession(bankroll=10))
    mode = path.stat().st_mode & 0o777
    assert mode == 0o600


def test_corrupt_file_raises(tmp_path: Path) -> None:
    path = tmp_path / "session.json"
    path.write_text("this is not json", encoding="utf-8")
    store = JsonSessionStore(path)
    with pytest.raises(SessionCorruptError):
        store.load()


def test_reset_removes_file(tmp_path: Path) -> None:
    path = tmp_path / "session.json"
    store = JsonSessionStore(path)
    store.save(SavedSession(bankroll=5))
    store.reset()
    assert not path.exists()
    # idempotent
    store.reset()


def test_in_memory_store() -> None:
    store = InMemorySessionStore()
    assert store.load() is None
    session = SavedSession(bankroll=42)
    store.save(session)
    assert store.load() == session
    store.reset()
    assert store.load() is None
