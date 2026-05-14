"""Rich-based renderers shared by TUI and demo.

These helpers produce :class:`rich.console.RenderableType` objects so
they can be displayed either on a plain ``rich.console.Console`` or
inside Textual widgets that accept ``RenderableType``.

Card faces follow the "Premiere Blackjack" Stitch mock: near-white
paper with classic red/black suit colors, gold border, rank+suit
stacked in the top-left and mirrored in the bottom-right, and a big
suit/face mark centered — exactly like a real playing card.
"""

from __future__ import annotations

from rich.align import Align
from rich.box import ROUNDED
from rich.columns import Columns
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.domain.hand import Hand, evaluate

# Card geometry: 11 cells wide x 9 cells tall outer. With padding
# (0, 1) and the two-cell border, that leaves a 7x7 content grid
# which is plenty of room for the corner pips and a big centre mark.
CARD_WIDTH = 11
CARD_HEIGHT = 9
_INNER_WIDTH = CARD_WIDTH - 2 - 2  # borders + padding

# Style tokens — registered in ``theme.build_theme``.
_CARD_FACE_BG = "#F5F1E6"
_CARD_BACK_BG = "#0A4D2B"
_CARD_BORDER = "accent"
_CARD_BORDER_DIM = "accent-dim"


def _suit_style(suit: Suit) -> str:
    """Return the combined fg-on-paper style for a suit on a card face."""
    return "card-face-red" if suit.is_red else "card-face"


def _display_rank(rank: Rank) -> str:
    """Public-facing rank string. Tens render as ``10`` not ``T``."""
    return "10" if rank is Rank.TEN else rank.value


def _centre_glyph(card: Card, ascii_only: bool) -> str:
    """Return what goes on the big centre row of the card.

    Aces and number cards show the suit glyph; face cards show their
    rank letter so a quick glance distinguishes a J of spades from an
    A of spades without reading the corners.
    """
    if card.rank in (Rank.JACK, Rank.QUEEN, Rank.KING):
        return card.rank.value
    return card.suit.value if ascii_only else card.suit.glyph


def render_card(card: Card, *, ascii_only: bool = False) -> RenderableType:
    """Return a Rich Panel that draws a single playing card.

    The face is a 7-line grid laid out like a real card::

        A
        ♠

             ♠

                  ♠
                  A

    Top-left has the rank stacked above the suit; the bottom-right
    has the same pair mirrored. The big centre mark is the suit for
    pip cards, or the rank letter for J/Q/K.
    """
    rank_text = _display_rank(card.rank)
    corner_suit = card.suit.value if ascii_only else card.suit.glyph
    centre = _centre_glyph(card, ascii_only)
    style = _suit_style(card.suit)

    blank = " " * _INNER_WIDTH
    lines = (
        rank_text.ljust(_INNER_WIDTH),
        corner_suit.ljust(_INNER_WIDTH),
        blank,
        centre.center(_INNER_WIDTH),
        blank,
        corner_suit.rjust(_INNER_WIDTH),
        rank_text.rjust(_INNER_WIDTH),
    )
    face = Text.from_markup(
        f"[bold {style}]{lines[0]}[/]\n"
        f"[{style}]{lines[1]}[/]\n"
        f"[{style}]{lines[2]}[/]\n"
        f"[bold {style}]{lines[3]}[/]\n"
        f"[{style}]{lines[4]}[/]\n"
        f"[{style}]{lines[5]}[/]\n"
        f"[bold {style}]{lines[6]}[/]"
    )
    return Panel(
        face,
        width=CARD_WIDTH,
        height=CARD_HEIGHT,
        border_style=_CARD_BORDER,
        style=f"on {_CARD_FACE_BG}",
        padding=(0, 1),
        box=ROUNDED,
    )


def render_back(*, ascii_only: bool = False) -> RenderableType:
    """Render a face-down card.

    Felt-green background with a gold diamond pattern that reads as
    the casino-house style of the design mock — the same vibe as the
    leather chip in the chip row.
    """
    if ascii_only:
        pattern = (
            "# # # # #\n"
            " # # # # \n"
            "# # X # #\n"
            " # # # # \n"
            "# # # # #\n"
            " # # # # \n"
            "# # # # #"
        )
    else:
        pattern = (
            "◆ ◆ ◆ ◆\n"
            " ◆ ◆ ◆ \n"
            "◆ ◆ ◆ ◆\n"
            " ◆ ✦ ◆ \n"
            "◆ ◆ ◆ ◆\n"
            " ◆ ◆ ◆ \n"
            "◆ ◆ ◆ ◆"
        )
    face = Text(pattern, style="card-back")
    return Panel(
        Align.center(face, vertical="middle"),
        width=CARD_WIDTH,
        height=CARD_HEIGHT,
        border_style=_CARD_BORDER_DIM,
        style=f"on {_CARD_BACK_BG}",
        padding=(0, 1),
        box=ROUNDED,
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
        text = f"DEALER SHOWS {_display_rank(up.rank)}"
        if up.rank is Rank.ACE:
            text += " (soft 11)"
        return Text(text, style="bold accent-dim")
    value = evaluate(hand.cards, from_initial_deal=from_initial_deal)
    label = f"HAND VALUE {value.total}"
    if value.is_bust:
        return Text(label + "  BUST", style="bold danger")
    if value.is_blackjack:
        return Text(label + "  BLACKJACK", style="bold accent")
    qualifier = "soft" if value.is_soft else "hard"
    return Text(f"{label} ({qualifier})", style="bold accent-dim")


def _row(items: list[RenderableType]) -> RenderableType:
    """Lay panels side-by-side."""
    return Columns(items, padding=(0, 1), expand=False)
