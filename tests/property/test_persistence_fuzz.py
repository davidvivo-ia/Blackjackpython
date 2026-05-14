"""Fuzz test for :class:`JsonSessionStore.load`.

The store's contract: on a missing file, return ``None``; on a valid
file, return a :class:`SavedSession`; on anything malformed, raise
:class:`SessionCorruptError` (which is a :class:`BlackjackError` so
callers can catch it without overreaching).

Property under test: the loader never lets a raw ``json.JSONDecodeError``,
``ValidationError`` or ``OSError`` escape — those are wrapped — and
never raises any unrelated exception type on arbitrary bytes.
"""

from __future__ import annotations

from pathlib import Path

import hypothesis.strategies as st
from hypothesis import HealthCheck, given, settings

from blackjack21.application.session import SavedSession
from blackjack21.domain.errors import SessionCorruptError
from blackjack21.infrastructure.persistence import JsonSessionStore


@given(payload=st.binary(max_size=512))
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_load_wraps_garbage_input_in_session_corrupt_error(
    tmp_path: Path, payload: bytes
) -> None:
    path = tmp_path / "session.json"
    path.write_bytes(payload)
    store = JsonSessionStore(path)
    try:
        result = store.load()
    except SessionCorruptError:
        # Expected for malformed input.
        return
    # If load succeeded, the result must be a valid SavedSession.
    assert isinstance(result, SavedSession)


@given(text=st.text(max_size=512))
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_load_wraps_arbitrary_text(tmp_path: Path, text: str) -> None:
    path = tmp_path / "session.json"
    path.write_text(text, encoding="utf-8")
    store = JsonSessionStore(path)
    try:
        result = store.load()
    except SessionCorruptError:
        return
    assert isinstance(result, SavedSession)


def test_load_returns_none_when_file_missing(tmp_path: Path) -> None:
    store = JsonSessionStore(tmp_path / "absent.json")
    assert store.load() is None
