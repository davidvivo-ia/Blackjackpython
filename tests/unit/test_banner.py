"""Outcome banner renders the right label, sign and amount."""

from __future__ import annotations

import io

import pytest
from rich.console import Console

from blackjack21.domain.outcomes import Outcome
from blackjack21.presentation.banner import outcome_banner
from blackjack21.presentation.theme import build_theme


def _render(renderable: object) -> str:
    buf = io.StringIO()
    Console(
        file=buf, width=60, theme=build_theme(), legacy_windows=False
    ).print(renderable)
    return buf.getvalue()


@pytest.mark.parametrize(
    ("outcome", "expected_label"),
    [
        (Outcome.WIN, "W I N"),
        (Outcome.BLACKJACK, "B L A C K J A C K"),
        (Outcome.LOSS, "L O S S"),
        (Outcome.BUST, "B U S T"),
        (Outcome.PUSH, "P U S H"),
        (Outcome.SURRENDER, "S U R R E N D E R"),
    ],
)
def test_outcome_banner_includes_label(
    outcome: Outcome, expected_label: str
) -> None:
    out = _render(outcome_banner(outcome, 100))
    assert expected_label in out


def test_outcome_banner_shows_signed_amount() -> None:
    win = _render(outcome_banner(Outcome.WIN, 25))
    assert "+$25" in win
    loss = _render(outcome_banner(Outcome.LOSS, -50))
    assert "−$50" in loss  # noqa: RUF001
