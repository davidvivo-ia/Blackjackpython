"""E2E test for the deterministic demo."""

from __future__ import annotations

import io

import pytest
from rich.console import Console

from blackjack21.presentation.demo import run_demo
from blackjack21.presentation.theme import build_theme


@pytest.mark.e2e
def test_demo_seed_42_is_deterministic() -> None:
    """The same seed must produce the same final bankroll across runs."""
    buf1 = io.StringIO()
    buf2 = io.StringIO()
    run_demo(
        seed=42,
        hands=5,
        console=Console(file=buf1, width=80, theme=build_theme(), legacy_windows=False),
    )
    run_demo(
        seed=42,
        hands=5,
        console=Console(file=buf2, width=80, theme=build_theme(), legacy_windows=False),
    )
    assert buf1.getvalue() == buf2.getvalue()


@pytest.mark.e2e
def test_demo_produces_expected_summary() -> None:
    buf = io.StringIO()
    state = run_demo(
        seed=42,
        hands=5,
        console=Console(file=buf, width=80, theme=build_theme(), legacy_windows=False),
    )
    output = buf.getvalue()
    assert "BLACKJACK 21" in output
    assert "Demo Summary" in output
    assert state.hands_played == 5
    # With seed 42 and 5 hands the bankroll never reaches 0
    assert state.bankroll > 0
