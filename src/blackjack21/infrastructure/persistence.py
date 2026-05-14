"""Filesystem-backed persistence of :class:`SavedSession`."""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path

from pydantic import ValidationError

from blackjack21.application.session import SavedSession
from blackjack21.domain.errors import SessionCorruptError
from blackjack21.infrastructure.paths import session_path


class JsonSessionStore:
    """Atomically reads/writes ``session.json`` under XDG."""

    __slots__ = ("_path",)

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or session_path()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> SavedSession | None:
        if not self._path.exists():
            return None
        try:
            raw = self._path.read_text(encoding="utf-8")
            return SavedSession.model_validate_json(raw)
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValidationError,
        ) as exc:
            raise SessionCorruptError(
                f"Cannot decode session file at {self._path}: {exc}"
            ) from exc

    def save(self, session: SavedSession) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = session.model_dump_json(indent=2)
        # Atomic write: temp file then rename, set restrictive permissions.
        fd, tmp_name = tempfile.mkstemp(
            dir=self._path.parent, prefix=".session-", suffix=".json"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(data)
            os.chmod(tmp_name, 0o600)
            os.replace(tmp_name, self._path)
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(tmp_name)
            raise

    def reset(self) -> None:
        with contextlib.suppress(FileNotFoundError):
            self._path.unlink()


class InMemorySessionStore:
    """Test-only :class:`SessionStore` that keeps state in a slot."""

    __slots__ = ("_session",)

    def __init__(self) -> None:
        self._session: SavedSession | None = None

    def load(self) -> SavedSession | None:
        return self._session

    def save(self, session: SavedSession) -> None:
        self._session = session

    def reset(self) -> None:
        self._session = None
