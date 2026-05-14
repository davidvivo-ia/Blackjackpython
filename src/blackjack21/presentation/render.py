"""Rich-based renderers shared by TUI and demo.

These helpers produce :class:`rich.console.RenderableType` objects so
they can be displayed either on a plain ``rich.console.Console`` or
inside Textual widgets that accept ``RenderableType``.

Card faces follow the "Premiere Blackjack" Stitch mock: a near-white
paper surface with classic red/black suit colors and a gold-ish
border that reads as a felt-table chip rim.
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

# Style tokens — these reference Rich theme styles registered in
# :func:`blackjack21.presentation.theme.build_theme`. Card faces are
# near-white paper with classic red/black suits; a gold border ties
# them into the casino-table chrome.
_CARD_FACE_BG = "#F5F1E6"
_CARD_BACK_BG = "#0A4D2B"
_CARD_BORDER = "accent"
_CARD_BORDER_DIM = "accent-dim"


def _suit_style(suit: Suit) -> str:
    """Return the combined fg-on-paper style for a suit on a card face."""
    return "card-face-red" if suit.is_red else "card-face"


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

    The panel is a fixed 9 by 5 rectangle so multiple cards align. The
    face is a near-white paper surface so the rank/suit pop in classic
    red/black against a casino-green table.
    """
    rank = card.rank.value
    suit_glyph = card.suit.value if ascii_only else card.suit.glyph
    style = _suit_style(card.suit)
    face = Text.from_markup(
        f"[bold {style}]{_padded_rank_left(rank)}[/]\n"
        f"[{style}]{_padded_suit(suit_glyph)}[/]\n"
        f"[bold {style}]{_padded_rank_right(rank)}[/]"
    )
    return Panel(
        face,
        width=CARD_WIDTH,
        height=CARD_HEIGHT,
        border_style=_CARD_BORDER,
        style=f"on {_CARD_FACE_BG}",
        padding=(0, 1),
    )


def render_back(*, ascii_only: bool = False) -> RenderableType:
    """Render a face-down card.

    The back is felt-green with a gold diamond pattern, echoing the
    casino-house style of the design mock.
    """
    pattern = (
        "# # #\n # # \n# # #" if ascii_only else "◆ ◆ ◆\n ◆ ◆ \n◆ ◆ ◆"
    )
    face = Text(pattern, style="card-back")
    return Panel(
        Align.center(face, vertical="middle"),
        width=CARD_WIDTH,
        height=CARD_HEIGHT,
        border_style=_CARD_BORDER_DIM,
        style=f"on {_CARD_BACK_BG}",
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
        text = f"DEALER SHOWS {up.rank.value}"
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

