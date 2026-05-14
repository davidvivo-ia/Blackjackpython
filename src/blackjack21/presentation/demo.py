"""Deterministic ``--demo`` mode.

Plays a fixed number of hands using a tiny built-in strategy:

* Always bet 25 (or remaining bankroll, whichever is smaller).
* Decline insurance.
* Hit while the hand total is below 17, stand otherwise.

The point is not to play well, but to exercise the full pipeline
end-to-end on every run with reproducible output.
"""

from __future__ import annotations

from collections.abc import Iterable

from rich.console import Console
from rich.rule import Rule
from rich.table import Table

from blackjack21.application.events import (
    BetPlaced,
    CardDealt,
    DealerRevealed,
    GameEvent,
    HandResolved,
    InsuranceOffered,
    InsuranceResolved,
    PlayerActed,
    SessionEnded,
)
from blackjack21.application.use_cases import (
    deal_hand,
    finish_round,
    next_hand,
    player_action,
    take_insurance,
)
from blackjack21.domain.actions import Action
from blackjack21.domain.outcomes import Outcome
from blackjack21.domain.rules import DEFAULT_RULES, GameRules
from blackjack21.domain.shuffler import Shuffler
from blackjack21.domain.state import GameState, Phase, start_session
from blackjack21.infrastructure.rng import SystemShuffler
from blackjack21.presentation.theme import build_theme

DEFAULT_HANDS = 5
DEFAULT_BET = 25


def run_demo(
    *,
    seed: int,
    hands: int = DEFAULT_HANDS,
    rules: GameRules = DEFAULT_RULES,
    console: Console | None = None,
) -> GameState:
    """Run the deterministic demo and return the final state."""
    out = console or Console(theme=build_theme())
    shuffler: Shuffler = SystemShuffler(seed=seed)
    state = start_session(rules=rules, shuffler=shuffler)
    out.print(
        Rule(
            f"[bold phosphor]BLACKJACK 21[/]  ·  seed={seed}  ·  hands={hands}",
            style="phosphor-dim",
        )
    )
    for hand_no in range(1, hands + 1):
        if state.is_game_over:
            out.print("[danger]Bankroll exhausted — demo cannot continue.[/]")
            break
        state = _play_one_hand(state, hand_no=hand_no, console=out, shuffler=shuffler)
        if state.phase is Phase.HAND_RESOLVED:
            state = next_hand(state)
    _print_summary(state, console=out)
    return state


def _play_one_hand(
    state: GameState, *, hand_no: int, console: Console, shuffler: Shuffler
) -> GameState:
    bet = min(DEFAULT_BET, state.bankroll)
    console.print(
        f"\n[bold phosphor]Hand {hand_no}[/]  ·  bankroll {state.bankroll}  "
        f"·  bet {bet}"
    )
    state, events = deal_hand(state, bet, shuffler=shuffler)
    _print_events(events, console=console)

    if state.phase is Phase.AWAITING_INSURANCE:
        state, events = take_insurance(state, insurance_bet=0)
        _print_events(events, console=console)

    while state.phase is Phase.PLAYER_TURN:
        action = _basic_strategy(state)
        state, events = player_action(state, action, shuffler=shuffler)
        _print_events(events, console=console)

    if state.phase is Phase.DEALER_TURN:
        state, events = finish_round(state, shuffler=shuffler)
        _print_events(events, console=console)

    return state


def _basic_strategy(state: GameState) -> Action:
    """Hit below 17 (hard or soft), stand otherwise."""
    value = state.active_hand.value
    if value.total < 17:
        return Action.HIT
    return Action.STAND


def _print_events(events: Iterable[GameEvent], *, console: Console) -> None:
    for event in events:
        match event:
            case BetPlaced(bet=bet, bankroll=bankroll):
                console.print(f"  bet [accent]{bet}[/]  bankroll {bankroll}")
            case CardDealt(card=card, to=to, hand_index=idx):
                where = "you " if to == "player" else "dealer"
                if to == "player" and idx > 0:
                    where = f"you[{idx}]"
                console.print(f"  {where}: [phosphor]{card}[/]")
            case PlayerActed(action=action):
                console.print(f"  action: [bold]{action.value.upper()}[/]")
            case DealerRevealed(hole_card=hc):
                console.print(f"  dealer reveals: [phosphor]{hc}[/]")
            case InsuranceOffered(max_insurance=mx):
                console.print(f"  insurance offered (max {mx}); demo declines")
            case InsuranceResolved(insurance_bet=ib, won=won):
                tag = "[success]paid[/]" if won else "[danger]lost[/]"
                console.print(f"  insurance {ib} {tag}")
            case HandResolved(
                settlement=settlement,
                bankroll_after=bankroll_after,
            ):
                tag = _outcome_tag(settlement.outcome)
                console.print(
                    f"  outcome: {tag}  net {settlement.net:+d}  "
                    f"bankroll {bankroll_after}"
                )
            case SessionEnded(final_bankroll=final, reason=reason):
                console.print(f"  session ended ({reason}) at bankroll {final}")


def _outcome_tag(outcome: Outcome) -> str:
    palette = {
        Outcome.WIN: "[bold success]WIN[/]",
        Outcome.BLACKJACK: "[bold success]BLACKJACK[/]",
        Outcome.LOSS: "[bold danger]LOSS[/]",
        Outcome.BUST: "[bold danger]BUST[/]",
        Outcome.PUSH: "[bold warning]PUSH[/]",
        Outcome.SURRENDER: "[bold warning]SURRENDER[/]",
    }
    return palette[outcome]


def _print_summary(state: GameState, *, console: Console) -> None:
    table = Table(
        title="[bold phosphor]Demo Summary[/]",
        show_header=False,
        border_style="phosphor-dim",
    )
    table.add_row("Final bankroll", str(state.bankroll))
    table.add_row("Hands played", str(state.hands_played))
    table.add_row("Blackjacks", str(state.blackjacks))
    console.print()
    console.print(table)
