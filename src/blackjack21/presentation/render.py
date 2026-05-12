"""Rich-based renderers shared by TUI and demo.

These helpers produce :class:`rich.console.RenderableType` objects so
they can be displayed either on a plain ``rich.console.Console`` or
inside Textual widgets that accept ``RenderableType``.
"""

from __future__ import annotations

from rich.align import Align
from rich.columns import Columns
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.domain.hand import Hand, evaluate

CARD_WIDTH = 9  # 9 cells outer = 5 cells of usable content with padding (0, 1)
CARD_HEIGHT = 5
_INNER_WIDTH = CARD_WIDTH - 2 - 2  # 2 cells border + 2 cells padding


def _suit_color(suit: Suit) -> str:
    return "danger" if suit.is_red else "ink"


def _padded_rank_left(rank: str) -> str:
    """Render the rank in the top-left of the card."""
    return rank.ljust(_INNER_WIDTH)


def _padded_rank_right(rank: str) -> str:
    """Render the rank in the bottom-right of the card."""
    return rank.rjust(_INNER_WIDTH)


def _padded_suit(suit_glyph: str) -> str:
    """Render the suit centered."""
    return suit_glyph.center(_INNER_WIDTH)


def render_card(card: Card, *, ascii_only: bool = False) -> RenderableType:
    """Return a rich Panel that draws a single card.

    The panel is a fixed 9 by 5 rectangle so multiple cards align. Inside
    we render the rank in the top-left and bottom-right corners and the
    suit glyph centered on the middle row.
    """
    rank = card.rank.value
    if ascii_only:
        suit_glyph = card.suit.value
        face = Text.from_markup(
            f"[bold]{_padded_rank_left(rank)}[/]\n"
            f"{_padded_suit(suit_glyph)}\n"
            f"[bold]{_padded_rank_right(rank)}[/]"
        )
    else:
        color = _suit_color(card.suit)
        face = Text.from_markup(
            f"[bold {color}]{_padded_rank_left(rank)}[/]\n"
            f"[{color}]{_padded_suit(card.suit.glyph)}[/]\n"
            f"[bold {color}]{_padded_rank_right(rank)}[/]"
        )
    return Panel(
        face,
        width=CARD_WIDTH,
        height=CARD_HEIGHT,
        border_style="phosphor-dim",
        padding=(0, 1),
    )


def render_back(*, ascii_only: bool = False) -> RenderableType:
    """Render a face-down card."""
    pattern = "###\n###\n###" if ascii_only else "░▒▓\n▓▒░\n░▒▓"
    face = Text(pattern, style="phosphor-dim")
    return Panel(
        Align.center(face, vertical="middle"),
        width=CARD_WIDTH,
        height=CARD_HEIGHT,
        border_style="phosphor-dim",
        padding=(0, 1),
    )


def render_hand(
    hand: Hand,
    *,
    hide_first: bool = False,
    from_initial_deal: bool = True,
    ascii_only: bool = False,
) -> RenderableType:
    """Render a row of cards plus a one-line total summary."""
    pieces: list[RenderableType] = []
    for i, card in enumerate(hand.cards):
        if hide_first and i == 1:
            pieces.append(render_back(ascii_only=ascii_only))
        else:
            pieces.append(render_card(card, ascii_only=ascii_only))
    row = _row(pieces)
    summary = _hand_summary(
        hand, hide_first=hide_first, from_initial_deal=from_initial_deal
    )
    return Group(row, summary)


def _hand_summary(
    hand: Hand, *, hide_first: bool, from_initial_deal: bool
) -> RenderableType:
    if hide_first and len(hand.cards) >= 1:
        up = hand.cards[0]
        text = f"showing {up.rank.value}"
        if up.rank is Rank.ACE:
            text += " (soft 11)"
        return Text(text, style="muted")
    value = evaluate(hand.cards, from_initial_deal=from_initial_deal)
    label = f"total {value.total}"
    if value.is_bust:
        return Text(label + "  BUST", style="bold danger")
    if value.is_blackjack:
        return Text(label + "  BLACKJACK", style="bold success")
    qualifier = "soft" if value.is_soft else "hard"
    return Text(f"{label} ({qualifier})", style="phosphor-dim")


def _row(items: list[RenderableType]) -> RenderableType:
    """Lay panels side-by-side."""
    return Columns(items, padding=(0, 1), expand=False)
