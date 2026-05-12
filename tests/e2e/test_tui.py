"""TUI Pilot tests — lock down focus and card rendering regressions."""

from __future__ import annotations

import io

import pytest
from rich.console import Console

from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.domain.state import Phase
from blackjack21.infrastructure.persistence import JsonSessionStore
from blackjack21.presentation.render import render_card
from blackjack21.presentation.theme import build_theme
from blackjack21.presentation.tui import BlackjackApp


@pytest.mark.asyncio
async def test_input_hidden_during_player_turn(tmp_path) -> None:
    """After placing a bet, the bet input must hide so H/S/D bindings fire."""
    app = BlackjackApp(seed=42, store=JsonSessionStore(tmp_path / "s.json"))
    async with app.run_test() as pilot:
        assert app.state is not None
        assert app.state.phase is Phase.AWAITING_BET
        bet_input = app.query_one("#bet-input")
        assert bet_input.display
        await pilot.click("#bet-input")
        await pilot.press("2", "5", "enter")
        assert app.state.phase in (
            Phase.PLAYER_TURN,
            Phase.AWAITING_INSURANCE,
            Phase.HAND_RESOLVED,
        )
        if app.state.phase is Phase.PLAYER_TURN:
            assert not bet_input.display
            cards_before = len(app.state.active_hand.cards)
            await pilot.press("h")
            assert (
                len(app.state.active_hand.cards) > cards_before
                or app.state.phase is not Phase.PLAYER_TURN
            )


def test_card_render_does_not_truncate() -> None:
    """Regression: cards used to print '...' because the rank overflowed."""
    for rank in (Rank.ACE, Rank.TEN, Rank.KING, Rank.TWO):
        buf = io.StringIO()
        Console(file=buf, width=80, theme=build_theme(), legacy_windows=False).print(
            render_card(Card(rank, Suit.HEARTS))
        )
        out = buf.getvalue()
        assert "..." not in out, f"Card {rank} truncated: {out!r}"
        assert rank.value in out
