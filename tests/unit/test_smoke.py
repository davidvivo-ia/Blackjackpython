"""Smoke test verifying the package imports."""

from __future__ import annotations

import blackjack21


def test_package_has_version() -> None:
    assert isinstance(blackjack21.__version__, str)
    assert blackjack21.__version__.count(".") == 2
