"""Textual TUI for blackjack21 — Premiere Blackjack skin.

One screen, one widget tree. The state machine in
:mod:`blackjack21.domain.state` is the source of truth; this module
only renders snapshots and forwards user input.

Layout inspired by the Stitch "Premiere Blackjack" mock: header bar,
3-cell stats row (balance / current bet / hand value) with a chip-disc
visualisation under the current bet, a live counter row (W/L/P/BJ
plus streak with fire/snow when hot/cold), dealer + you hand columns
rendered as paper-white cards with classic pip patterns, gold accents.

Three button rows take turns owning the action area depending on the
phase:

- AWAITING_BET → chip selector + CLEAR BET + DEAL
- PLAYER_TURN  → HIT / STAND / DOUBLE / SPLIT / SURRENDER (greyed
  out individually when not legal)
- AWAITING_INSURANCE → INSURANCE / NO THANKS

A hand-history modal opens on ``,`` and a session-info modal on ``.``.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from importlib import resources
from typing import ClassVar

from rich.console import RenderableType
from rich.rule import Rule
from rich.table import Table
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Static

from blackjack21.application.session import SavedSession, SessionStats
from blackjack21.application.strategy import explain, recommend
from blackjack21.application.use_cases import (
    deal_hand,
    finish_round,
    next_hand,
    player_action,
    take_insurance,
)
from blackjack21.domain.actions import Action
from blackjack21.domain.cards import Rank
from blackjack21.domain.errors import BlackjackError
from blackjack21.domain.hand import Hand
from blackjack21.domain.outcomes import Outcome
from blackjack21.domain.rules import DEFAULT_RULES, GameRules
from blackjack21.domain.state import GameState, Phase, start_session
from blackjack21.infrastructure.persistence import JsonSessionStore
from blackjack21.infrastructure.rng import SystemShuffler
from blackjack21.presentation.banner import outcome_banner
from blackjack21.presentation.render import render_hand
from blackjack21.presentation.theme import (
    DEFAULT_THEME,
    THEMES,
    build_theme,
    tcss_variable_block,
)

CHIP_DENOMINATIONS: tuple[int, ...] = (5, 25, 100, 500)

# Map each chip denomination to its theme colour class. Used both for
# the Button styling and the chip-stack visualisation in the
# CURRENT BET stat cell.
_CHIP_STYLES: dict[int, str] = {
    5: "chip-red",
    25: "chip-green",
    100: "chip-black",
    500: "chip-purple",
}

# Action buttons rendered during PLAYER_TURN — one per legal move.
# Order matches the way a player reads a casino mat left-to-right.
_ACTION_BUTTONS: tuple[tuple[Action, str], ...] = (
    (Action.HIT, "HIT"),
    (Action.STAND, "STAND"),
    (Action.DOUBLE, "DOUBLE"),
    (Action.SPLIT, "SPLIT"),
    (Action.SURRENDER, "SURRENDER"),
)

_HISTORY_LIMIT = 50


def _chip_breakdown(amount: int) -> list[int]:
    """Greedy decomposition of ``amount`` into 500/100/25/5 chips."""
    chips: list[int] = []
    remaining = amount
    for denom in (500, 100, 25, 5):
        n, remaining = divmod(remaining, denom)
        chips.extend([denom] * n)
    return chips


def _chip_stack_markup(amount: int, *, max_discs: int = 8) -> str:
    """Render a horizontal stack of ● chip discs in their theme colors."""
    chips = _chip_breakdown(amount)
    if not chips:
        return "[muted]· · ·[/]"
    visible = chips[:max_discs]
    discs = "".join(f"[{_CHIP_STYLES[c]}]●[/]" for c in visible)
    overflow = " …" if len(chips) > max_discs else ""
    return f"{discs}{overflow}"


@dataclass(frozen=True, slots=True)
class HandRecord:
    """Compact record of one resolved hand, kept for the History modal."""

    bet: int
    player_text: str
    dealer_text: str
    outcome: Outcome
    net: int
    balance_after: int


def _hand_text(hand: Hand) -> str:
    """Render a hand as a compact one-line ``T♠ K♥ 4♣`` string."""
    return " ".join(str(c) for c in hand.cards)


def _read_base_css() -> str:
    """Read the static portion of the TCSS (without variable declarations)."""
    return (
        resources.files("blackjack21.assets")
        .joinpath("blackjack.tcss")
        .read_text(encoding="utf-8")
    )


def load_css(theme_name: str = DEFAULT_THEME) -> str:
    """Return the full TCSS for ``theme_name``.

    Prepends a per-theme ``$var: #HEX;`` block in front of the rule set
    so the same rule body works across the four built-in palettes.
    """
    return tcss_variable_block(theme_name) + _read_base_css()


class HandPanel(Static):
    """A widget that renders a labelled hand row."""

    def update_hand(self, renderable: RenderableType) -> None:
        self.update(renderable)


class HistoryScreen(ModalScreen[None]):
    """Modal showing the last ``_HISTORY_LIMIT`` resolved hands."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("escape", "dismiss", "Close"),
        Binding("comma", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    def __init__(self, history: list[HandRecord]) -> None:
        super().__init__()
        self._history = history

    def compose(self) -> ComposeResult:
        table = Table(
            title="[bold accent]LAST HANDS[/]",
            border_style="accent",
            header_style="bold #A88729",
            expand=True,
        )
        table.add_column("#", justify="right", width=4)
        table.add_column("bet", justify="right", width=6)
        table.add_column("you", width=20)
        table.add_column("dealer", width=20)
        table.add_column("outcome", width=10)
        table.add_column("net", justify="right", width=8)
        table.add_column("balance", justify="right", width=10)
        for i, record in enumerate(reversed(self._history), start=1):
            sign = "+" if record.net >= 0 else ""
            table.add_row(
                str(len(self._history) - i + 1),
                f"${record.bet}",
                record.player_text,
                record.dealer_text,
                record.outcome.value.upper(),
                f"{sign}${record.net}",
                f"${record.balance_after:,}",
            )
        if not self._history:
            table.add_row("", "", "", "no hands yet", "", "", "")
        with Vertical(id="modal-container"):
            yield Static(table, id="modal-body")
            yield Static(
                "[muted]press [bold],[/] / [bold]ESC[/] / [bold]Q[/] to close[/]",
                id="modal-footer",
            )


class InfoScreen(ModalScreen[None]):
    """Modal showing rules, theme and session summary."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("escape", "dismiss", "Close"),
        Binding("period", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    def __init__(
        self,
        *,
        rules: GameRules,
        wins: int,
        losses: int,
        pushes: int,
        blackjacks: int,
        biggest_pot: int,
        ascii_only: bool,
    ) -> None:
        super().__init__()
        self._rules = rules
        self._wins = wins
        self._losses = losses
        self._pushes = pushes
        self._blackjacks = blackjacks
        self._biggest_pot = biggest_pot
        self._ascii_only = ascii_only

    def compose(self) -> ComposeResult:
        info = Table(
            title="[bold accent]SESSION INFO[/]",
            border_style="accent",
            show_header=False,
            expand=True,
        )
        info.add_column("key", style="#A88729")
        info.add_column("value", style="#E5E2E1")
        info.add_row(
            "rules",
            f"{self._rules.num_decks}-deck · "
            f"{'H17' if self._rules.dealer_hits_soft_17 else 'S17'} · "
            f"BJ {self._rules.blackjack_pays_numerator}:"
            f"{self._rules.blackjack_pays_denominator} · "
            f"surrender {'on' if self._rules.allow_surrender else 'off'}",
        )
        info.add_row(
            "bets",
            f"min ${self._rules.min_bet}  max ${self._rules.max_bet}",
        )
        info.add_row(
            "glyphs",
            "ASCII (S/H/D/C)" if self._ascii_only else "Unicode (♠♥♦♣)",
        )
        played = self._wins + self._losses + self._pushes
        info.add_row("hands played", str(played))
        info.add_row(
            "win rate",
            f"{(self._wins / played * 100):.1f}%" if played else "—",
        )
        info.add_row("blackjacks", str(self._blackjacks))
        info.add_row("biggest pot", f"${self._biggest_pot:,}")
        with Vertical(id="modal-container"):
            yield Static(info, id="modal-body")
            yield Static(
                "[muted]press [bold].[/] / [bold]ESC[/] / [bold]Q[/] to close[/]",
                id="modal-footer",
            )


class BlackjackApp(App[int]):
    """Main Textual application."""

    # CSS is rebuilt per instance in ``__init__`` so the chosen
    # palette injects its $vars in front of the static rules.
    CSS = load_css()
    TITLE = "♠ ♥  PREMIERE  BLACKJACK  ♦ ♣"
    SUB_TITLE = "high-stakes table"

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("h", "act('hit')", "Hit", show=True),
        Binding("s", "act('stand')", "Stand", show=True),
        Binding("d", "act('double')", "Double", show=True),
        Binding("slash", "act('split')", "Split", show=True),
        Binding("u", "act('surrender')", "Surrender", show=True),
        Binding("i", "decline_insurance", "Insurance", show=False),
        Binding("y", "take_insurance_full", "Yes insurance", show=False),
        Binding("n", "next_hand", "Next hand", show=True),
        Binding("c", "clear_bet", "Clear bet", show=False),
        Binding("enter", "deal", "Deal", show=False),
        Binding("t", "hint", "Tip", show=True),
        Binding("comma", "show_history", "History", show=True),
        Binding("period", "show_info", "Info", show=True),
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
        rules: GameRules | None = None,
        theme_name: str = DEFAULT_THEME,
    ) -> None:
        if theme_name not in THEMES:
            theme_name = DEFAULT_THEME
        # Rebuild the CSS for the chosen theme BEFORE super().__init__()
        # so Textual loads the right $var block. App.CSS is read at
        # construction time, so mutating the class attribute here is
        # the documented way to swap palettes per instance.
        type(self).CSS = load_css(theme_name)
        super().__init__()
        # Push the semantic palette onto Rich's Console so theme names
        # like "accent" / "card-paper" resolve inside markup. Without
        # this, MissingStyle is raised at first render.
        self.console.push_theme(build_theme(theme_name))
        self._theme_name = theme_name
        self._seed = seed
        self._store = store or JsonSessionStore()
        self._shuffler = SystemShuffler(seed=seed)
        self._ascii_only = ascii_only
        self._rules = rules or DEFAULT_RULES
        self._biggest_pot = 0
        # Live session counters — incremented on every settlement.
        self._wins = 0
        self._losses = 0
        self._pushes = 0
        self._blackjacks = 0
        self._busts = 0
        self._surrenders = 0
        self._streak = 0  # + winning streak, - losing streak
        self._history: list[HandRecord] = []

    # ---- composition --------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="main"):
            with Horizontal(id="stats-row"):
                yield Static("BALANCE\n[bold accent]$1,000[/]", id="balance")
                yield Static(
                    "CURRENT BET\n[muted]· · ·[/]\n[bold accent]$0[/]",
                    id="current-bet",
                )
                yield Static("HAND VALUE\n[bold accent]—[/]", id="hand-value")
            with Horizontal(id="counters-row"):
                yield Static("", id="counters")
            yield Static("DEALER", classes="section-title")
            yield HandPanel(id="dealer-hand", classes="hand-row")
            yield Static("YOU", classes="section-title")
            yield HandPanel(id="player-hand", classes="hand-row")
            yield Static("place a bet to start", id="status")
            with Horizontal(id="chip-row"):
                for denom in CHIP_DENOMINATIONS:
                    yield Button(
                        f"● ${denom}",
                        id=f"chip-{denom}",
                        classes=f"chip chip-{denom}",
                    )
            with Horizontal(id="bet-controls"):
                yield Button(
                    "CLEAR BET",
                    id="clear-bet-btn",
                    classes="bet-btn bet-btn-clear",
                )
                yield Button(
                    "DEAL", id="deal-btn", classes="bet-btn bet-btn-deal"
                )
            with Horizontal(id="actions-row"):
                for action, label in _ACTION_BUTTONS:
                    yield Button(
                        label,
                        id=f"action-{action.value}",
                        classes=f"action-btn action-{action.value}",
                    )
            with Horizontal(id="insurance-row"):
                yield Button(
                    "INSURANCE",
                    id="insurance-yes",
                    classes="ins-btn ins-yes",
                )
                yield Button(
                    "NO THANKS", id="insurance-no", classes="ins-btn ins-no"
                )
            yield Static("", id="message")
            yield Static(
                "[bold]H[/]it · [bold]S[/]tand · [bold]D[/]ouble · "
                "[bold]/[/] split · s[bold]U[/]rrender · "
                "[bold]T[/]ip · [bold]N[/]ext · [bold],[/] history · "
                "[bold].[/] info · [bold]Q[/]uit",
                classes="help",
            )
        yield Footer()

    # ---- lifecycle ----------------------------------------------------

    def on_mount(self) -> None:
        saved = self._load_saved_session()
        bankroll = saved.bankroll if saved else self._rules.initial_bankroll
        self._biggest_pot = saved.stats.biggest_pot if saved else 0
        self.state = start_session(
            rules=self._rules, shuffler=self._shuffler, bankroll=bankroll
        )
        self._refresh()

    def _load_saved_session(self) -> SavedSession | None:
        try:
            return self._store.load()
        except BlackjackError:
            return None

    # ---- input --------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "deal-btn":
            self.action_deal()
        elif bid == "clear-bet-btn":
            self.action_clear_bet()
        elif bid == "insurance-yes":
            self._take_insurance_max()
        elif bid == "insurance-no":
            self._take_insurance(0)
        elif bid.startswith("chip-"):
            denom = int(bid.removeprefix("chip-"))
            self._add_chip(denom)
        elif bid.startswith("action-"):
            self.action_act(bid.removeprefix("action-"))

    # ---- chip & bet flow ---------------------------------------------

    def _add_chip(self, denom: int) -> None:
        if self.state is None or self.state.phase is not Phase.AWAITING_BET:
            return
        proposed = self.pending_bet + denom
        if proposed > self.state.bankroll:
            self.last_message = "Not enough balance for that chip."
            self._refresh()
            return
        if proposed > self._rules.max_bet:
            self.last_message = f"Max bet is ${self._rules.max_bet}."
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

    def _take_insurance_max(self) -> None:
        if self.state is None or self.state.phase is not Phase.AWAITING_INSURANCE:
            return
        max_ins = min(self.state.active_hand.bet // 2, self.state.bankroll)
        self._take_insurance(max_ins)

    def _take_insurance(self, amount: int) -> None:
        if self.state is None or self.state.phase is not Phase.AWAITING_INSURANCE:
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

    def action_decline_insurance(self) -> None:
        self._take_insurance(0)

    def action_take_insurance_full(self) -> None:
        self._take_insurance_max()

    def action_next_hand(self) -> None:
        if self.state is None or self.state.phase is not Phase.HAND_RESOLVED:
            return
        self.state = next_hand(self.state)
        self.last_message = ""
        self._refresh()

    def action_toggle_help(self) -> None:
        self.last_message = (
            "Click chips to build a bet, then DEAL. "
            "[bold]T[/] for a tip, [bold]U[/] to surrender, "
            "[bold],[/] for history, [bold].[/] for info."
        )
        self._refresh()

    def action_hint(self) -> None:
        if self.state is None or self.state.phase is not Phase.PLAYER_TURN:
            self.last_message = "Tip only available on your turn."
            self._refresh()
            return
        suggested = recommend(self.state)
        reason = explain(self.state)
        self.last_message = (
            f"[bold accent]TIP[/] [bold]{suggested.value.upper()}[/] — {reason}"
        )
        self._refresh()

    def action_show_history(self) -> None:
        self.push_screen(HistoryScreen(self._history))

    def action_show_info(self) -> None:
        self.push_screen(
            InfoScreen(
                rules=self._rules,
                wins=self._wins,
                losses=self._losses,
                pushes=self._pushes,
                blackjacks=self._blackjacks,
                biggest_pot=self._biggest_pot,
                ascii_only=self._ascii_only,
            )
        )

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
            self._update_counters_and_history()
            self._update_biggest_pot()
            self._persist()

    def _update_counters_and_history(self) -> None:
        assert self.state is not None
        for i, settlement in enumerate(self.state.settlements):
            outcome = settlement.outcome
            if outcome is Outcome.WIN:
                self._wins += 1
                self._streak = self._streak + 1 if self._streak >= 0 else 1
            elif outcome is Outcome.BLACKJACK:
                self._blackjacks += 1
                self._wins += 1
                self._streak = self._streak + 1 if self._streak >= 0 else 1
            elif outcome is Outcome.LOSS:
                self._losses += 1
                self._streak = self._streak - 1 if self._streak <= 0 else -1
            elif outcome is Outcome.BUST:
                self._busts += 1
                self._losses += 1
                self._streak = self._streak - 1 if self._streak <= 0 else -1
            elif outcome is Outcome.PUSH:
                self._pushes += 1
            elif outcome is Outcome.SURRENDER:
                self._surrenders += 1
                self._losses += 1
                self._streak = self._streak - 1 if self._streak <= 0 else -1
            hand = (
                self.state.player_hands[i]
                if i < len(self.state.player_hands)
                else None
            )
            if hand is not None:
                record = HandRecord(
                    bet=hand.bet,
                    player_text=_hand_text(hand),
                    dealer_text=_hand_text(self.state.dealer),
                    outcome=outcome,
                    net=settlement.net + settlement.insurance_net,
                    balance_after=self.state.bankroll,
                )
                self._history.append(record)
        # Cap the history so the modal doesn't grow forever.
        if len(self._history) > _HISTORY_LIMIT:
            self._history = self._history[-_HISTORY_LIMIT:]

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
        self._refresh_counters_row()
        self._refresh_hands()
        self._refresh_status()
        self._refresh_button_rows()
        self.query_one("#message", Static).update(self.last_message)

    def _refresh_stats_row(self) -> None:
        assert self.state is not None
        balance = self.state.bankroll
        self.query_one("#balance", Static).update(
            f"BALANCE\n[bold accent]${balance:,}[/]"
        )
        bet = self._displayed_bet()
        chip_line = _chip_stack_markup(bet)
        self.query_one("#current-bet", Static).update(
            f"CURRENT BET\n{chip_line}\n[bold accent]${bet:,}[/]"
        )
        self.query_one("#hand-value", Static).update(
            f"HAND VALUE\n[bold accent]{self._displayed_hand_value()}[/]"
        )

    def _refresh_counters_row(self) -> None:
        if self._streak >= 5:
            streak_str = f"🔥 [bold accent]+{self._streak}[/]"
        elif self._streak <= -5:
            streak_str = f"❄  [bold danger]{self._streak}[/]"
        elif self._streak > 0:
            streak_str = f"[bold accent]+{self._streak}[/]"
        elif self._streak < 0:
            streak_str = f"[bold danger]{self._streak}[/]"
        else:
            streak_str = "[muted]0[/]"
        counters = (
            f"[bold accent-dim]W[/] [bold]{self._wins:>3}[/]   "
            f"[bold accent-dim]L[/] [bold]{self._losses:>3}[/]   "
            f"[bold accent-dim]P[/] [bold]{self._pushes:>3}[/]   "
            f"[bold accent-dim]BJ[/] [bold]{self._blackjacks:>3}[/]   "
            f"[bold accent-dim]STREAK[/] {streak_str}"
        )
        self.query_one("#counters", Static).update(counters)

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
        match self.state.phase:
            case Phase.AWAITING_BET:
                status.update(
                    "[accent]click chips to build your bet, then DEAL[/]"
                )
            case Phase.AWAITING_INSURANCE:
                up = self.state.dealer.cards[0]
                up_label = "A" if up.rank is Rank.ACE else up.rank.value
                status.update(
                    f"[accent]dealer shows {up_label} — buy insurance "
                    f"(half bet pays 2:1 if dealer has blackjack)?[/]"
                )
            case Phase.PLAYER_TURN:
                legal = ", ".join(a.value for a in sorted(self.state.legal_actions()))
                status.update(f"your turn: {legal}")
            case Phase.DEALER_TURN:
                status.update("dealer is playing…")
            case Phase.HAND_RESOLVED:
                settlement = self.state.settlements[0]
                status.update(
                    outcome_banner(
                        settlement.outcome,
                        settlement.net + settlement.insurance_net,
                    )
                )
            case Phase.GAME_OVER:
                status.update(
                    "[danger]BALANCE EXHAUSTED[/] — press Q to quit, "
                    "then 'blackjack21 reset' to start over"
                )

    def _refresh_button_rows(self) -> None:
        """Toggle which row of buttons is visible based on the phase."""
        assert self.state is not None
        phase = self.state.phase
        # Betting controls
        betting = phase is Phase.AWAITING_BET
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

        # Player-turn action buttons
        on_turn = phase is Phase.PLAYER_TURN
        legal = self.state.legal_actions() if on_turn else frozenset()
        for action, _label in _ACTION_BUTTONS:
            btn = self.query_one(f"#action-{action.value}", Button)
            btn.display = on_turn
            btn.disabled = action not in legal

        # Insurance buttons
        ins = phase is Phase.AWAITING_INSURANCE
        ins_yes = self.query_one("#insurance-yes", Button)
        ins_no = self.query_one("#insurance-no", Button)
        ins_yes.display = ins
        ins_no.display = ins
        if ins:
            max_ins = min(
                self.state.active_hand.bet // 2, self.state.bankroll
            )
            ins_yes.label = f"INSURANCE ${max_ins}"
            ins_yes.disabled = max_ins <= 0
