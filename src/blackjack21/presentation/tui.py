"""Textual TUI for blackjack21.

The TUI is deliberately small: one screen, one widget tree. The
state machine in :mod:`blackjack21.domain.state` is the source of
truth; this module only renders snapshots and forwards user input.
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
from textual.widgets import Footer, Header, Input, Static

from blackjack21.application.session import SavedSession, SessionStats
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
    TITLE = "blackjack21"
    SUB_TITLE = "phosphor green fusion"

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("h", "act('hit')", "Hit", show=True),
        Binding("s", "act('stand')", "Stand", show=True),
        Binding("d", "act('double')", "Double", show=True),
        Binding("slash", "act('split')", "Split", show=True),
        Binding("i", "take_insurance", "Insurance", show=False),
        Binding("n", "next_hand", "Next hand", show=True),
        Binding("question_mark", "toggle_help", "Help", show=True),
        Binding("q", "quit_save", "Quit", show=True),
    ]

    state: reactive[GameState | None] = reactive(None)
    last_message: reactive[str] = reactive("")

    def __init__(
        self,
        *,
        seed: int | None = None,
        store: JsonSessionStore | None = None,
    ) -> None:
        super().__init__()
        self._seed = seed
        self._store = store or JsonSessionStore()
        self._shuffler = SystemShuffler(seed=seed)
        self._biggest_pot = 0

    # ---- composition --------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="main"):
            yield Static("BANKROLL  ◉ 1,000", id="bankroll", classes="bankroll")
            yield Static("DEALER", classes="section-title")
            yield HandPanel(id="dealer-hand", classes="hand-row")
            yield Static("YOU", classes="section-title")
            yield HandPanel(id="player-hand", classes="hand-row")
            with Horizontal(id="actions"):
                yield Static("place a bet to start", id="status")
            yield Input(placeholder="bet (1 to 500)", id="bet-input")
            yield Static("", id="message")
            yield Static(
                "[bold]H[/]it · [bold]S[/]tand · [bold]D[/]ouble · "
                "[bold]/[/] split · [bold]I[/]nsurance · "
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
        self._refresh()
        self.query_one("#bet-input", Input).focus()

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
            return
        if self.state.phase is not Phase.AWAITING_BET:
            return
        self._submit_bet(event.value)
        event.input.value = ""

    def _submit_bet(self, raw: str) -> None:
        assert self.state is not None
        try:
            amount = int(raw)
        except ValueError:
            self.last_message = "Bet must be an integer."
            self._refresh()
            return
        try:
            new_state, _ = deal_hand(self.state, amount, shuffler=self._shuffler)
        except BlackjackError as exc:
            self.last_message = str(exc)
            self._refresh()
            return
        self.last_message = ""
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
        self.query_one("#bet-input", Input).focus()

    def action_toggle_help(self) -> None:
        self.last_message = (
            "Press the letter in brackets to act. Aces count as 11 unless that busts."
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
        bankroll = self.state.bankroll
        self.query_one("#bankroll", Static).update(
            f"BANKROLL  [accent]◉ {bankroll:,}[/]"
        )
        self._refresh_hands()
        self._refresh_status()
        self.query_one("#message", Static).update(self.last_message)

    def _refresh_hands(self) -> None:
        assert self.state is not None
        dealer_panel = self.query_one("#dealer-hand", HandPanel)
        player_panel = self.query_one("#player-hand", HandPanel)
        if self.state.dealer.cards:
            hide = self.state.phase in (
                Phase.PLAYER_TURN,
                Phase.AWAITING_INSURANCE,
            )
            dealer_panel.update_hand(render_hand(self.state.dealer, hide_first=hide))
        else:
            dealer_panel.update_hand(Rule(style="phosphor-dim"))
        if self.state.player_hands:
            player_panel.update_hand(
                render_hand(
                    self.state.active_hand,
                    from_initial_deal=not self.state.active_hand.from_split,
                )
            )
        else:
            player_panel.update_hand(Rule(style="phosphor-dim"))

    def _refresh_status(self) -> None:
        assert self.state is not None
        status = self.query_one("#status", Static)
        match self.state.phase:
            case Phase.AWAITING_BET:
                status.update("place a bet (1 to 500) then Enter")
            case Phase.AWAITING_INSURANCE:
                status.update(
                    "insurance? Enter amount or just press [bold]I[/] to decline"
                )
            case Phase.PLAYER_TURN:
                legal = ", ".join(a.value for a in sorted(self.state.legal_actions()))
                status.update(f"your turn: {legal}")
            case Phase.DEALER_TURN:
                status.update("dealer is playing…")
            case Phase.HAND_RESOLVED:
                outcome = self.state.settlements[0].outcome
                status.update(_outcome_banner(outcome))
            case Phase.GAME_OVER:
                status.update("[danger]BANKROLL ENDED[/] — press Q to quit, R to reset")


def _outcome_banner(outcome: Outcome) -> str:
    table = {
        Outcome.WIN: "[outcome-win]WIN[/] — press N for next hand",
        Outcome.BLACKJACK: "[outcome-blackjack]BLACKJACK[/] — press N for next hand",
        Outcome.LOSS: "[outcome-loss]LOSS[/] — press N for next hand",
        Outcome.BUST: "[outcome-loss]BUST[/] — press N for next hand",
        Outcome.PUSH: "[outcome-push]PUSH[/] — press N for next hand",
        Outcome.SURRENDER: "[outcome-push]SURRENDER[/] — press N for next hand",
    }
    return table[outcome]
