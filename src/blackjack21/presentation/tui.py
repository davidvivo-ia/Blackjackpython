"""Textual TUI for blackjack21 — Premiere Blackjack skin.

The TUI is deliberately small: one screen, one widget tree. The
state machine in :mod:`blackjack21.domain.state` is the source of
truth; this module only renders snapshots and forwards user input.

Visual reference: the Stitch "Premiere Blackjack" mock. We keep the
terminal constraints (no glass blur, no backdrop) but echo the
layout: balance / current-bet / hand-value row, dealer/you hand
columns, chip selector for betting, gold accents.
"""

from __future__ import annotations

import contextlib
from importlib import resources
from typing import ClassVar

from rich.console import RenderableType
from rich.rule import Rule
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Input, Static

from blackjack21.application.session import SavedSession, SessionStats
from blackjack21.application.strategy import recommend
from blackjack21.application.use_cases import (
    deal_hand,
    finish_round,
    next_hand,
    player_action,
    take_insurance,
)
from blackjack21.domain.actions import Action
from blackjack21.domain.errors import BlackjackError
from blackjack21.domain.outcomes import Outcome
from blackjack21.domain.rules import DEFAULT_RULES
from blackjack21.domain.state import GameState, Phase, start_session
from blackjack21.infrastructure.persistence import JsonSessionStore
from blackjack21.infrastructure.rng import SystemShuffler
from blackjack21.presentation.render import render_hand
from blackjack21.presentation.theme import build_theme

CHIP_DENOMINATIONS: tuple[int, ...] = (5, 25, 100, 500)


def load_css() -> str:
    """Read the bundled CSS file."""
    return (
        resources.files("blackjack21.assets")
        .joinpath("blackjack.tcss")
        .read_text(encoding="utf-8")
    )


class HandPanel(Static):
    """A widget that renders a labelled hand row."""

    def update_hand(self, renderable: RenderableType) -> None:
        self.update(renderable)


class BlackjackApp(App[int]):
    """Main Textual application."""

    CSS = load_css()
    TITLE = "PREMIERE BLACKJACK"
    SUB_TITLE = "high-stakes table"

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("h", "act('hit')", "Hit", show=True),
        Binding("s", "act('stand')", "Stand", show=True),
        Binding("d", "act('double')", "Double", show=True),
        Binding("slash", "act('split')", "Split", show=True),
        Binding("i", "take_insurance", "Insurance", show=False),
        Binding("n", "next_hand", "Next hand", show=True),
        Binding("c", "clear_bet", "Clear bet", show=False),
        Binding("enter", "deal", "Deal", show=False),
        Binding("t", "hint", "Tip", show=True),
        Binding("question_mark", "toggle_help", "Help", show=True),
        Binding("q", "quit_save", "Quit", show=True),
    ]

    state: reactive[GameState | None] = reactive(None)
    last_message: reactive[str] = reactive("")
    pending_bet: reactive[int] = reactive(0)

    def __init__(
        self,
        *,
        seed: int | None = None,
        store: JsonSessionStore | None = None,
        ascii_only: bool = False,
    ) -> None:
        super().__init__()
        # Registramos la paleta semantica en el Console de Rich que
        # Textual usa para renderizar los Static/HandPanel. Sin esto
        # los nombres "card-paper", "accent", etc. revientan al
        # parsear el markup.
        self.console.push_theme(build_theme())
        self._seed = seed
        self._store = store or JsonSessionStore()
        self._shuffler = SystemShuffler(seed=seed)
        self._biggest_pot = 0
        self._ascii_only = ascii_only

    # ---- composition --------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="main"):
            with Horizontal(id="stats-row"):
                yield Static("BALANCE\n[bold accent]$1,000[/]", id="balance")
                yield Static(
                    "CURRENT BET\n[bold accent]$0[/]", id="current-bet"
                )
                yield Static(
                    "HAND VALUE\n[bold accent]—[/]", id="hand-value"
                )
            yield Static("DEALER", classes="section-title")
            yield HandPanel(id="dealer-hand", classes="hand-row")
            yield Static("YOU", classes="section-title")
            yield HandPanel(id="player-hand", classes="hand-row")
            with Horizontal(id="actions"):
                yield Static("place a bet to start", id="status")
            with Horizontal(id="chip-row"):
                for denom in CHIP_DENOMINATIONS:
                    yield Button(
                        f"${denom}",
                        id=f"chip-{denom}",
                        classes=f"chip chip-{denom}",
                    )
            with Horizontal(id="bet-controls"):
                yield Button(
                    "CLEAR BET", id="clear-bet-btn", classes="bet-btn bet-btn-clear"
                )
                yield Button("DEAL", id="deal-btn", classes="bet-btn bet-btn-deal")
            yield Input(placeholder="insurance (0 = none)", id="bet-input")
            yield Static("", id="message")
            yield Static(
                "[bold]H[/]it · [bold]S[/]tand · [bold]D[/]ouble · "
                "[bold]/[/] split · [bold]I[/]nsurance · [bold]T[/]ip · "
                "[bold]N[/]ext · [bold]Q[/]uit",
                classes="help",
            )
        yield Footer()

    # ---- lifecycle ----------------------------------------------------

    def on_mount(self) -> None:
        saved = self._load_saved_session()
        bankroll = saved.bankroll if saved else DEFAULT_RULES.initial_bankroll
        self._biggest_pot = saved.stats.biggest_pot if saved else 0
        self.state = start_session(
            rules=DEFAULT_RULES, shuffler=self._shuffler, bankroll=bankroll
        )
        # Hide the insurance input until needed.
        self.query_one("#bet-input", Input).display = False
        self._refresh()

    def _load_saved_session(self) -> SavedSession | None:
        try:
            return self._store.load()
        except BlackjackError:
            return None

    # ---- input --------------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.state is None:
            return
        if self.state.phase is Phase.AWAITING_INSURANCE:
            self._submit_insurance(event.value)
            event.input.value = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "deal-btn":
            self.action_deal()
            return
        if event.button.id == "clear-bet-btn":
            self.action_clear_bet()
            return
        if event.button.id and event.button.id.startswith("chip-"):
            denom = int(event.button.id.removeprefix("chip-"))
            self._add_chip(denom)

    # ---- chip & bet flow ---------------------------------------------

    def _add_chip(self, denom: int) -> None:
        if self.state is None or self.state.phase is not Phase.AWAITING_BET:
            return
        rules = DEFAULT_RULES
        proposed = self.pending_bet + denom
        if proposed > self.state.bankroll:
            self.last_message = "Not enough balance for that chip."
            self._refresh()
            return
        if proposed > rules.max_bet:
            self.last_message = f"Max bet is ${rules.max_bet}."
            self._refresh()
            return
        self.pending_bet = proposed
        self.last_message = ""
        self._refresh()

    def action_clear_bet(self) -> None:
        if self.state is None or self.state.phase is not Phase.AWAITING_BET:
            return
        self.pending_bet = 0
        self.last_message = ""
        self._refresh()

    def action_deal(self) -> None:
        if self.state is None or self.state.phase is not Phase.AWAITING_BET:
            return
        if self.pending_bet <= 0:
            self.last_message = "Select chips to build your bet, then DEAL."
            self._refresh()
            return
        self._submit_bet(self.pending_bet)

    def _submit_bet(self, amount: int) -> None:
        assert self.state is not None
        try:
            new_state, _ = deal_hand(self.state, amount, shuffler=self._shuffler)
        except BlackjackError as exc:
            self.last_message = str(exc)
            self._refresh()
            return
        self.last_message = ""
        self.pending_bet = 0
        self.state = new_state
        self._auto_resolve_if_done()
        self._refresh()

    def _submit_insurance(self, raw: str) -> None:
        assert self.state is not None
        try:
            amount = int(raw) if raw.strip() else 0
        except ValueError:
            self.last_message = "Insurance bet must be an integer."
            self._refresh()
            return
        try:
            new_state, _ = take_insurance(self.state, amount)
        except BlackjackError as exc:
            self.last_message = str(exc)
            self._refresh()
            return
        self.last_message = ""
        self.state = new_state
        self._auto_resolve_if_done()
        self._refresh()

    # ---- actions ------------------------------------------------------

    def action_act(self, action: str) -> None:
        if self.state is None or self.state.phase is not Phase.PLAYER_TURN:
            return
        try:
            action_enum = Action(action)
        except ValueError:
            return
        if action_enum not in self.state.legal_actions():
            self.last_message = f"{action_enum.value} not legal here."
            self._refresh()
            return
        try:
            new_state, _ = player_action(
                self.state, action_enum, shuffler=self._shuffler
            )
        except BlackjackError as exc:
            self.last_message = str(exc)
            self._refresh()
            return
        self.last_message = ""
        self.state = new_state
        self._auto_resolve_if_done()
        self._refresh()

    def action_take_insurance(self) -> None:
        if self.state is None or self.state.phase is not Phase.AWAITING_INSURANCE:
            return
        # `I` alone = decline; players entering 0 in the input also work.
        self._submit_insurance("0")

    def action_next_hand(self) -> None:
        if self.state is None or self.state.phase is not Phase.HAND_RESOLVED:
            return
        self.state = next_hand(self.state)
        self.last_message = ""
        self._refresh()

    def action_toggle_help(self) -> None:
        self.last_message = (
            "Click chips to build a bet, then DEAL. Press T for a basic-strategy tip."
        )
        self._refresh()

    def action_hint(self) -> None:
        """Display the basic-strategy recommendation for the current decision."""
        if self.state is None or self.state.phase is not Phase.PLAYER_TURN:
            self.last_message = "Tip only available on your turn."
            self._refresh()
            return
        suggested = recommend(self.state)
        self.last_message = (
            f"[bold accent]TIP:[/] basic strategy says "
            f"[bold]{suggested.value.upper()}[/]"
        )
        self._refresh()

    def action_quit_save(self) -> None:
        self._persist()
        self.exit(self.state.bankroll if self.state else 0)

    # ---- internals ----------------------------------------------------

    def _auto_resolve_if_done(self) -> None:
        if self.state is None:
            return
        if self.state.phase is Phase.DEALER_TURN:
            try:
                new_state, _ = finish_round(self.state, shuffler=self._shuffler)
            except BlackjackError as exc:
                self.last_message = str(exc)
                return
            self.state = new_state
            self._update_biggest_pot()
            self._persist()

    def _update_biggest_pot(self) -> None:
        assert self.state is not None
        pot = sum(abs(s.net) for s in self.state.settlements)
        self._biggest_pot = max(self._biggest_pot, pot)

    def _persist(self) -> None:
        if self.state is None:
            return
        with contextlib.suppress(OSError):
            self._store.save(
                SavedSession(
                    bankroll=max(0, self.state.bankroll),
                    stats=SessionStats(
                        hands_played=self.state.hands_played,
                        blackjacks=self.state.blackjacks,
                        biggest_pot=self._biggest_pot,
                    ),
                )
            )

    def _refresh(self) -> None:
        if self.state is None:
            return
        self._refresh_stats_row()
        self._refresh_hands()
        self._refresh_status()
        self._refresh_chip_controls()
        self.query_one("#message", Static).update(self.last_message)

    def _refresh_stats_row(self) -> None:
        assert self.state is not None
        balance = self.state.bankroll
        self.query_one("#balance", Static).update(
            f"BALANCE\n[bold accent]${balance:,}[/]"
        )
        self.query_one("#current-bet", Static).update(
            f"CURRENT BET\n[bold accent]${self._displayed_bet():,}[/]"
        )
        self.query_one("#hand-value", Static).update(
            f"HAND VALUE\n[bold accent]{self._displayed_hand_value()}[/]"
        )

    def _displayed_bet(self) -> int:
        assert self.state is not None
        if self.state.phase is Phase.AWAITING_BET:
            return self.pending_bet
        if self.state.player_hands:
            return self.state.active_hand.bet
        return 0

    def _displayed_hand_value(self) -> str:
        assert self.state is not None
        if not self.state.player_hands:
            return "—"
        return str(self.state.active_hand.value.total)

    def _refresh_hands(self) -> None:
        assert self.state is not None
        dealer_panel = self.query_one("#dealer-hand", HandPanel)
        player_panel = self.query_one("#player-hand", HandPanel)
        if self.state.dealer.cards:
            hide = self.state.phase in (
                Phase.PLAYER_TURN,
                Phase.AWAITING_INSURANCE,
            )
            dealer_panel.update_hand(
                render_hand(
                    self.state.dealer,
                    hide_first=hide,
                    ascii_only=self._ascii_only,
                )
            )
        else:
            dealer_panel.update_hand(Rule(style="accent-dim"))
        if self.state.player_hands:
            player_panel.update_hand(
                render_hand(
                    self.state.active_hand,
                    from_initial_deal=not self.state.active_hand.from_split,
                    ascii_only=self._ascii_only,
                )
            )
        else:
            player_panel.update_hand(Rule(style="accent-dim"))

    def _refresh_status(self) -> None:
        assert self.state is not None
        status = self.query_one("#status", Static)
        bet_input = self.query_one("#bet-input", Input)
        match self.state.phase:
            case Phase.AWAITING_BET:
                status.update(
                    "[accent]click chips to build your bet, then DEAL[/]"
                )
                self._hide_input(bet_input)
            case Phase.AWAITING_INSURANCE:
                status.update(
                    "insurance? type amount and Enter, or press [bold]I[/] to decline"
                )
                self._show_input(bet_input, placeholder="insurance (0 = none)")
            case Phase.PLAYER_TURN:
                legal = ", ".join(a.value for a in sorted(self.state.legal_actions()))
                status.update(
                    f"your turn: {legal} -- press [bold]H[/]/[bold]S[/]/"
                    "[bold]D[/]/[bold]/[/]"
                )
                self._hide_input(bet_input)
            case Phase.DEALER_TURN:
                status.update("dealer is playing...")
                self._hide_input(bet_input)
            case Phase.HAND_RESOLVED:
                outcome = self.state.settlements[0].outcome
                status.update(_outcome_banner(outcome))
                self._hide_input(bet_input)
            case Phase.GAME_OVER:
                status.update(
                    "[danger]BALANCE EXHAUSTED[/] -- press Q to quit, "
                    "then 'blackjack21 reset' to start over"
                )
                self._hide_input(bet_input)

    def _refresh_chip_controls(self) -> None:
        """Enable chips + DEAL/CLEAR only while collecting a bet."""
        assert self.state is not None
        betting = self.state.phase is Phase.AWAITING_BET
        for denom in CHIP_DENOMINATIONS:
            chip = self.query_one(f"#chip-{denom}", Button)
            chip.disabled = not betting
            chip.display = betting
        deal_btn = self.query_one("#deal-btn", Button)
        clear_btn = self.query_one("#clear-bet-btn", Button)
        deal_btn.display = betting
        clear_btn.display = betting
        if betting:
            deal_btn.disabled = self.pending_bet <= 0

    def _show_input(self, widget: Input, *, placeholder: str) -> None:
        widget.placeholder = placeholder
        if not widget.display:
            widget.display = True
        if widget.disabled:
            widget.disabled = False
        if self.focused is not widget:
            widget.focus()

    def _hide_input(self, widget: Input) -> None:
        if widget.display:
            widget.display = False
            widget.disabled = True
            widget.value = ""
        if self.focused is widget:
            self.set_focus(None)


def _outcome_banner(outcome: Outcome) -> str:
    table = {
        Outcome.WIN: "[bold accent]WIN[/] - press N for next hand",
        Outcome.BLACKJACK: "[bold reverse accent]BLACKJACK[/] - press N for next hand",
        Outcome.LOSS: "[bold danger]LOSS[/] - press N for next hand",
        Outcome.BUST: "[bold danger]BUST[/] - press N for next hand",
        Outcome.PUSH: "[bold warning]PUSH[/] - press N for next hand",
        Outcome.SURRENDER: "[bold warning]SURRENDER[/] - press N for next hand",
    }
    return table[outcome]
