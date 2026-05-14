"""Pip-pattern regression: each rank paints the right number of suits."""

from __future__ import annotations

import io
import re

import pytest
from rich.console import Console

from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.presentation.render import render_card
from blackjack21.presentation.theme import build_theme

# We count suit glyphs in the rendered output. Spades is unambiguous —
# the only ♠ characters are the two corner indices plus the centre
# decoration (pips for number cards, suit-letter-suit for J/Q/K, big
# single pip for the Ace).
_CORNER_SUITS = 2  # top-left + bottom-right


def _render(card: Card) -> str:
    buf = io.StringIO()
    Console(
        file=buf, width=80, theme=build_theme(), legacy_windows=False
    ).print(render_card(card))
    return buf.getvalue()


def _count_suits(rendered: str, suit_glyph: str) -> int:
    return rendered.count(suit_glyph)


@pytest.mark.parametrize(
    ("rank", "expected_pips"),
    [
        (Rank.TWO, 2),
        (Rank.THREE, 3),
        (Rank.FOUR, 4),
        (Rank.FIVE, 5),
        (Rank.SIX, 6),
        (Rank.SEVEN, 7),
        (Rank.EIGHT, 8),
        (Rank.NINE, 9),
    ],
)
def test_number_cards_paint_expected_pip_count(
    rank: Rank, expected_pips: int
) -> None:
    out = _render(Card(rank, Suit.SPADES))
    total = _count_suits(out, "♠")
    pips = total - _CORNER_SUITS
    assert pips == expected_pips, (
        f"{rank.value} of spades should show {expected_pips} pips; "
        f"saw {pips} (rendered: {out!r})"
    )


def test_ace_renders_5_pip_splash() -> None:
    """The Ace explodes into a 5-pip plus-sign so it dominates the centre."""
    out = _render(Card(Rank.ACE, Suit.SPADES))
    pips = _count_suits(out, "♠") - _CORNER_SUITS
    assert pips == 5


_FACE_PIECES = {
    Rank.JACK: "♞",
    Rank.QUEEN: "♛",
    Rank.KING: "♚",
}


@pytest.mark.parametrize(
    "rank", [Rank.JACK, Rank.QUEEN, Rank.KING]
)
def test_face_cards_show_chess_piece_decoration_and_letter(
    rank: Rank,
) -> None:
    out = _render(Card(rank, Suit.SPADES))
    # No extra suits in the centre (only the two corner indices).
    pips = _count_suits(out, "♠") - _CORNER_SUITS
    assert pips == 0
    clean = re.sub(r"\x1b\[[0-9;]*m", "", out)
    # The chess piece appears twice (above and below the rank).
    assert clean.count(_FACE_PIECES[rank]) == 2
    assert rank.value in clean


def test_ten_renders_label_with_two_chars_in_corners() -> None:
    """The 10 must render with "10" in both corners, not "T"."""
    out = _render(Card(Rank.TEN, Suit.SPADES))
    clean = re.sub(r"\x1b\[[0-9;]*m", "", out)
    # Two corner labels => "10" appears at least twice.
    assert clean.count("10") >= 2
    assert "T" not in clean.replace("10", "")  # ensure no stray T


def test_red_suits_use_red_styling() -> None:
    """Hearts/diamonds should appear with the red suit color when ANSI is on."""
    buf = io.StringIO()
    Console(
        file=buf,
        width=80,
        theme=build_theme(),
        legacy_windows=False,
        force_terminal=True,
        color_system="truecolor",
    ).print(render_card(Card(Rank.SEVEN, Suit.HEARTS)))
    out = buf.getvalue()
    # The compound theme style for red is hex #D32F2F.
    assert "211;47;47" in out, f"Expected red RGB 211;47;47 in: {out!r}"
