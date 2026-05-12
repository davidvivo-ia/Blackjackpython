"""Shared Rich theme for the demo and any non-TUI renders.

The TUI gets its colors from Textual CSS in
``src/blackjack21/assets/blackjack.tcss``; this module mirrors the
same palette for code that talks to plain :class:`rich.console.Console`.
"""

from __future__ import annotations

from rich.theme import Theme

PALETTE: dict[str, str] = {
    "bg": "#0A1410",
    "bg-soft": "#0F1F18",
    "surface": "#152A22",
    "phosphor": "#7CFFB2",
    "phosphor-dim": "#3FA875",
    "accent": "#FFD86B",
    "success": "#5CFFB2",
    "warning": "#FFB347",
    "danger": "#FF6B6B",
    "muted": "#5A6F66",
    "ink": "#E6FFE9",
}


def build_theme() -> Theme:
    """Return the Rich :class:`Theme` for blackjack21."""
    return Theme(PALETTE)
