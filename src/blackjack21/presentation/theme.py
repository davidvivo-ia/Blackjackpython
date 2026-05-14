"""Shared Rich theme for the demo and any non-TUI renders.

The TUI gets its colors from Textual CSS in
``src/blackjack21/assets/blackjack.tcss``; this module mirrors the
same palette for code that talks to plain :class:`rich.console.Console`.

Palette inspired by the "Premiere Blackjack" Stitch design: a deep
casino-green felt with gold accents for high-value actions and the
balance, plus pure white card faces with classic red/black suits.
"""

from __future__ import annotations

from rich.theme import Theme

PALETTE: dict[str, str] = {
    # Surfaces
    "bg": "#0A2E1A",
    "bg-soft": "#0F3D24",
    "surface": "#14492C",
    # Brand
    "phosphor": "#95D5A7",
    "phosphor-dim": "#0A4D2B",
    "accent": "#D4AF37",
    "accent-dim": "#A88729",
    # Card surfaces (fg styles)
    "card-ink": "#1A1A1A",
    "suit-red": "#D32F2F",
    "suit-black": "#1A1A1A",
    # Card surface compound styles — used as standalone markup to paint
    # both fg and bg (Rich themes can't reference theme keys after "on").
    "card-face": "#1A1A1A on #F5F1E6",
    "card-face-red": "#D32F2F on #F5F1E6",
    "card-back": "#D4AF37 on #0A4D2B",
    # Status
    "success": "#95D5A7",
    "warning": "#E9C349",
    "danger": "#FF8A80",
    "muted": "#7A8C82",
    "ink": "#E5E2E1",
}


def build_theme() -> Theme:
    """Return the Rich :class:`Theme` for blackjack21."""
    return Theme(PALETTE)
