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
async def test_chip_betting_flow(tmp_path) -> None:
    """Clicking a $25 chip and pressing DEAL must place a 25 bet."""
    app = BlackjackApp(seed=42, store=JsonSessionStore(tmp_path / "s.json"))
    async with app.run_test() as pilot:
        assert app.state is not None
        assert app.state.phase is Phase.AWAITING_BET
        assert app.pending_bet == 0
        await pilot.click("#chip-25")
        assert app.pending_bet == 25
        await pilot.click("#deal-btn")
        assert app.state.phase in (
            Phase.PLAYER_TURN,
            Phase.AWAITING_INSURANCE,
            Phase.HAND_RESOLVED,
        )
        if app.state.phase is Phase.PLAYER_TURN:
            cards_before = len(app.state.active_hand.cards)
            await pilot.press("h")
            assert (
                len(app.state.active_hand.cards) > cards_before
                or app.state.phase is not Phase.PLAYER_TURN
            )


@pytest.mark.asyncio
async def test_clear_bet_resets_pending(tmp_path) -> None:
    """CLEAR BET must zero the pending stake without dealing."""
    app = BlackjackApp(seed=42, store=JsonSessionStore(tmp_path / "s.json"))
    async with app.run_test() as pilot:
        await pilot.click("#chip-100")
        await pilot.click("#chip-5")
        assert app.pending_bet == 105
        await pilot.click("#clear-bet-btn")
        assert app.pending_bet == 0
        assert app.state is not None
        assert app.state.phase is Phase.AWAITING_BET


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
