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

_BIG_SCREEN = (120, 60)


@pytest.mark.asyncio
async def test_chip_betting_flow(tmp_path) -> None:
    """Clicking a $25 chip and pressing DEAL must place a 25 bet."""
    app = BlackjackApp(seed=42, store=JsonSessionStore(tmp_path / "s.json"))
    async with app.run_test(size=_BIG_SCREEN) as pilot:
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
    async with app.run_test(size=_BIG_SCREEN) as pilot:
        await pilot.click("#chip-100")
        await pilot.click("#chip-5")
        assert app.pending_bet == 105
        await pilot.click("#clear-bet-btn")
        assert app.pending_bet == 0
        assert app.state is not None
        assert app.state.phase is Phase.AWAITING_BET


@pytest.mark.asyncio
async def test_action_button_fires_hit(tmp_path) -> None:
    """Clicking the HIT button on PLAYER_TURN must deal a card."""
    app = BlackjackApp(seed=42, store=JsonSessionStore(tmp_path / "s.json"))
    async with app.run_test(size=_BIG_SCREEN) as pilot:
        await pilot.click("#chip-25")
        await pilot.click("#deal-btn")
        if app.state is not None and app.state.phase is Phase.PLAYER_TURN:
            cards_before = len(app.state.active_hand.cards)
            await pilot.click("#action-hit")
            assert (
                len(app.state.active_hand.cards) > cards_before
                or app.state.phase is not Phase.PLAYER_TURN
            )


@pytest.mark.asyncio
async def test_history_modal_opens_and_closes(tmp_path) -> None:
    """Pressing comma opens the History modal; ESC closes it."""
    app = BlackjackApp(seed=42, store=JsonSessionStore(tmp_path / "s.json"))
    async with app.run_test(size=_BIG_SCREEN) as pilot:
        assert len(app.screen_stack) == 1
        await pilot.press("comma")
        assert len(app.screen_stack) == 2
        await pilot.press("escape")
        assert len(app.screen_stack) == 1


def test_card_render_does_not_truncate() -> None:
    """Regression: cards used to print '...' because the rank overflowed."""
    # Tens render as "10" not "T" — the visible token, not the enum value.
    visible = {Rank.ACE: "A", Rank.TEN: "10", Rank.KING: "K", Rank.TWO: "2"}
    for rank, label in visible.items():
        buf = io.StringIO()
        Console(file=buf, width=80, theme=build_theme(), legacy_windows=False).print(
            render_card(Card(rank, Suit.HEARTS))
        )
        out = buf.getvalue()
        assert "..." not in out, f"Card {rank} truncated: {out!r}"
        assert label in out
