"""Hand-outcome banners — the big visual reward after each round.

Rich panels with bold typography and outcome-specific borders so the
result reads at a glance: WIN/BLACKJACK in gold, LOSS/BUST in red,
PUSH/SURRENDER in amber. The label sits between two rows of sparkle
decoration that match the outcome's mood (stars for wins, crosses
for losses, etc.).
"""

from __future__ import annotations

from rich.align import Align
from rich.box import DOUBLE_EDGE, HEAVY
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from blackjack21.domain.outcomes import Outcome

_LABELS: dict[Outcome, str] = {
    Outcome.WIN: "W I N",
    Outcome.BLACKJACK: "B L A C K J A C K",
    Outcome.LOSS: "L O S S",
    Outcome.BUST: "B U S T",
    Outcome.PUSH: "P U S H",
    Outcome.SURRENDER: "S U R R E N D E R",
}

_SPARKLES: dict[Outcome, str] = {
    Outcome.WIN: "★ ✦ ★ ✦ ★",
    Outcome.BLACKJACK: "✦ ★ ✦ ★ ✦ ★ ✦",
    Outcome.LOSS: "✗ X ✗ X ✗",
    Outcome.BUST: "✗ X ✗ X ✗",
    Outcome.PUSH: "= ─ = ─ =",
    Outcome.SURRENDER: "↩ · ↩ · ↩",
}

_COLORS: dict[Outcome, tuple[str, str]] = {
    # (border / accent, label fg style)
    Outcome.WIN: ("accent", "bold accent"),
    Outcome.BLACKJACK: ("accent", "bold reverse accent"),
    Outcome.LOSS: ("danger", "bold danger"),
    Outcome.BUST: ("danger", "bold danger"),
    Outcome.PUSH: ("warning", "bold warning"),
    Outcome.SURRENDER: ("warning", "bold warning"),
}


def outcome_banner(outcome: Outcome, net: int) -> RenderableType:
    """Return a banner panel for a settled hand."""
    border, label_style = _COLORS[outcome]
    label = _LABELS[outcome]
    sparkles = _SPARKLES[outcome]
    sign = "+" if net >= 0 else "−"  # noqa: RUF001  typographic minus is intentional
    delta = f"{sign}${abs(net):,}"
    sparkle_top = Text(sparkles, style=border, justify="center")
    title = Text(label, style=label_style, justify="center")
    sparkle_bot = Text(sparkles, style=border, justify="center")
    money = Text(delta, style=f"bold {border}", justify="center")
    hint = Text("press N for next hand", style="muted", justify="center")
    body = Group(
        sparkle_top, Text(""), title, Text(""), sparkle_bot, Text(""), money, hint
    )
    box_style = DOUBLE_EDGE if outcome is Outcome.BLACKJACK else HEAVY
    return Panel(
        Align.center(body, vertical="middle"),
        border_style=border,
        style="on #0F3D24",  # matches $bg-soft in blackjack.tcss
        box=box_style,
        padding=(0, 4),
        height=10,
    )
