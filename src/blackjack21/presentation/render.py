"""Rich-based renderers shared by TUI and demo.

These helpers produce :class:`rich.console.RenderableType` objects so
they can be displayed either on a plain ``rich.console.Console`` or
inside Textual widgets that accept ``RenderableType``.

Card faces follow the "Premiere Blackjack" Stitch mock plus classic
Bicycle-deck pip patterns:

- Rank top-left, suit below it; mirrored bottom-right.
- Pip cards 2-10 lay their pips out in the canonical positions you'd
  see on a real card (e.g. 6 = 2x3 grid, 7 = same plus middle-top).
- J/Q/K show a suit-glyph above and below the bold rank letter, the
  classic "court card" look in monospace.
- Aces show a single big centered pip — the unmistakable A move.
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
# (0, 1) and the two-cell border, that leaves a 7x7 content grid:
# row 0 = top rank, row 1 = top suit, rows 2-4 = pip pattern area,
# row 5 = bottom suit, row 6 = bottom rank.
CARD_WIDTH = 11
CARD_HEIGHT = 9
_INNER_WIDTH = CARD_WIDTH - 2 - 2  # borders + padding
_INNER_HEIGHT = CARD_HEIGHT - 2  # borders only (no vertical padding)

# Style tokens — registered in ``theme.build_theme``.
_CARD_FACE_BG = "#F5F1E6"
_CARD_BACK_BG = "#0A4D2B"
_CARD_BORDER = "accent"
_CARD_BORDER_DIM = "accent-dim"

# Pip layout: each value is a frozenset of (col_idx, row_idx) within
# the 3-col x 3-row pip area. col_idx in {0,1,2} maps to inner cells
# (1, 3, 5); row_idx in {0,1,2} maps to inner rows (2, 3, 4). With
# only 3 rows, 9 and 10 share the full 3x3 grid — the corner rank
# label ("9" vs "10") disambiguates, as it does on real cards when
# the layout is unusually compact.
_PIP_COLS: tuple[int, int, int] = (1, 3, 5)
_PIP_ROW_BASE = 2  # inner row offset where the pip area starts

_NUM_PIPS: dict[Rank, frozenset[tuple[int, int]]] = {
    Rank.TWO:   frozenset({(1, 0), (1, 2)}),
    Rank.THREE: frozenset({(1, 0), (1, 1), (1, 2)}),
    Rank.FOUR:  frozenset({(0, 0), (2, 0), (0, 2), (2, 2)}),
    Rank.FIVE:  frozenset({(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)}),
    Rank.SIX:   frozenset({(0, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)}),
    Rank.SEVEN: frozenset(
        {(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)}
    ),
    Rank.EIGHT: frozenset(
        {(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)}
    ),
    Rank.NINE: frozenset(
        {(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2)}
    ),
    Rank.TEN: frozenset(
        {(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2)}
    ),
}


def _suit_style(suit: Suit) -> str:
    """Return the combined fg-on-paper style for a suit on a card face."""
    return "card-face-red" if suit.is_red else "card-face"


def _display_rank(rank: Rank) -> str:
    """Public-facing rank string. Tens render as ``10`` not ``T``."""
    return "10" if rank is Rank.TEN else rank.value


def _build_face_grid(card: Card, *, ascii_only: bool) -> list[list[str]]:
    """Return the inner 7x7 grid of glyphs for a card face."""
    rank_text = _display_rank(card.rank)
    corner_suit = card.suit.value if ascii_only else card.suit.glyph

    grid: list[list[str]] = [
        [" "] * _INNER_WIDTH for _ in range(_INNER_HEIGHT)
    ]

    # Top-left corner: rank on row 0, suit on row 1.
    for i, ch in enumerate(rank_text):
        grid[0][i] = ch
    grid[1][0] = corner_suit

    # Bottom-right corner: suit on row 5, rank on row 6 (right-aligned).
    grid[_INNER_HEIGHT - 2][_INNER_WIDTH - 1] = corner_suit
    rank_start = _INNER_WIDTH - len(rank_text)
    for i, ch in enumerate(rank_text):
        grid[_INNER_HEIGHT - 1][rank_start + i] = ch

    # Centre decoration: pip pattern, face decoration or big ace pip.
    centre_col = _PIP_COLS[1]
    if card.rank in (Rank.JACK, Rank.QUEEN, Rank.KING):
        grid[_PIP_ROW_BASE][centre_col] = corner_suit
        grid[_PIP_ROW_BASE + 1][centre_col] = card.rank.value
        grid[_PIP_ROW_BASE + 2][centre_col] = corner_suit
    elif card.rank is Rank.ACE:
        # Single oversized centre pip — make it pop by also drawing
        # the suit at the cells directly above/below for a "fan".
        grid[_PIP_ROW_BASE + 1][centre_col] = corner_suit
    elif card.rank in _NUM_PIPS:
        for col_idx, row_idx in _NUM_PIPS[card.rank]:
            grid[_PIP_ROW_BASE + row_idx][_PIP_COLS[col_idx]] = corner_suit

    return grid


def render_card(card: Card, *, ascii_only: bool = False) -> RenderableType:
    """Return a Rich Panel that draws a single playing card.

    Rank+suit indices in the top-left and bottom-right corners frame a
    centre area that shows either a classical pip pattern (2-10), a
    suit-letter-suit court look (J/Q/K), or a big single pip (A).
    """
    grid = _build_face_grid(card, ascii_only=ascii_only)
    style = _suit_style(card.suit)

    lines: list[str] = []
    for r, row in enumerate(grid):
        s = "".join(row)
        # Bold the rank rows (corners) and the central face-letter row
        # for J/Q/K (which is row 3 — _PIP_ROW_BASE + 1).
        bold = r in (0, _INNER_HEIGHT - 1) or (
            card.rank in (Rank.JACK, Rank.QUEEN, Rank.KING)
            and r == _PIP_ROW_BASE + 1
        )
        marker = f"bold {style}" if bold else style
        lines.append(f"[{marker}]{s}[/]")
    face = Text.from_markup("\n".join(lines))
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
