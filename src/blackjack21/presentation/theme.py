"""Theme palettes for blackjack21.

Each named theme is a flat ``dict[str, str]`` of theme-key → either
a colour hex (used as foreground) or a compound ``"fg on bg"`` style
string (Rich themes cannot reference theme keys after ``on``, so the
card-paper styles bake their own hex).

Four built-in themes:

- ``premiere``  — casino-green felt, gold accents (default).
- ``phosphor``  — homage to the v1.0 CRT amber-green look.
- ``midnight``  — navy blue felt, silver accents.
- ``ruby``      — deep red felt, gold accents, ivory cards.

The Rich palette returned by :func:`build_theme` feeds Rich's
``Console.push_theme``. The Textual chrome (button borders, panel
borders, etc.) reads the same hex values from a tiny TCSS preamble
that :func:`build_tcss` injects in front of the static rules.
"""

from __future__ import annotations

from rich.theme import Theme

# ---- per-theme palettes --------------------------------------------

_PREMIERE: dict[str, str] = {
    "bg": "#0A2E1A",
    "bg-soft": "#0F3D24",
    "surface": "#14492C",
    "felt-edge": "#073A1F",
    "phosphor": "#95D5A7",
    "phosphor-dim": "#0A4D2B",
    "accent": "#D4AF37",
    "accent-dim": "#A88729",
    "success": "#95D5A7",
    "warning": "#E9C349",
    "danger": "#FF8A80",
    "muted": "#7A8C82",
    "ink": "#E5E2E1",
    "chip-red": "#E53935",
    "chip-green": "#95D5A7",
    "chip-black": "#2A2A2A",
    "chip-purple": "#B19CD9",
    # Card paper stays warm cream across themes for legibility, only
    # the suit-red can shift slightly.
    "card-paper": "#F5F1E6",
    "card-ink": "#1A1A1A",
    "suit-red": "#D32F2F",
    "suit-black": "#1A1A1A",
    "card-back-bg": "#0A4D2B",
}

_PHOSPHOR: dict[str, str] = {
    "bg": "#0A1410",
    "bg-soft": "#0F1F18",
    "surface": "#152A22",
    "felt-edge": "#061410",
    "phosphor": "#7CFFB2",
    "phosphor-dim": "#3FA875",
    "accent": "#FFD86B",
    "accent-dim": "#B89544",
    "success": "#5CFFB2",
    "warning": "#FFB347",
    "danger": "#FF6B6B",
    "muted": "#5A6F66",
    "ink": "#E6FFE9",
    "chip-red": "#FF6B6B",
    "chip-green": "#5CFFB2",
    "chip-black": "#1F1F1F",
    "chip-purple": "#C5A8FF",
    "card-paper": "#F0EBD3",
    "card-ink": "#1A1A1A",
    "suit-red": "#D32F2F",
    "suit-black": "#1A1A1A",
    "card-back-bg": "#152A22",
}

_MIDNIGHT: dict[str, str] = {
    "bg": "#0A1230",
    "bg-soft": "#101A3F",
    "surface": "#162050",
    "felt-edge": "#070C24",
    "phosphor": "#A8C5FF",
    "phosphor-dim": "#3A4F8C",
    "accent": "#D6D6E0",
    "accent-dim": "#8C8FAA",
    "success": "#A8C5FF",
    "warning": "#FFD37A",
    "danger": "#FF8A80",
    "muted": "#5F6A85",
    "ink": "#E5E2F5",
    "chip-red": "#E53935",
    "chip-green": "#5CDD9E",
    "chip-black": "#2A2A33",
    "chip-purple": "#B19CD9",
    "card-paper": "#F5F1E6",
    "card-ink": "#1A1A1A",
    "suit-red": "#D32F2F",
    "suit-black": "#1A1A1A",
    "card-back-bg": "#162050",
}

_RUBY: dict[str, str] = {
    "bg": "#2A0A0A",
    "bg-soft": "#3A1010",
    "surface": "#4A1818",
    "felt-edge": "#1A0606",
    "phosphor": "#FFB6A8",
    "phosphor-dim": "#7A1F1F",
    "accent": "#E0BB5A",
    "accent-dim": "#A88729",
    "success": "#FFD194",
    "warning": "#FFE49E",
    "danger": "#FFB4AB",
    "muted": "#8A6F6A",
    "ink": "#FFE9E2",
    "chip-red": "#E53935",
    "chip-green": "#5CDD9E",
    "chip-black": "#2A2A2A",
    "chip-purple": "#B19CD9",
    "card-paper": "#FAF5E8",
    "card-ink": "#1A1A1A",
    "suit-red": "#D32F2F",
    "suit-black": "#1A1A1A",
    "card-back-bg": "#4A1818",
}

THEMES: dict[str, dict[str, str]] = {
    "premiere": _PREMIERE,
    "phosphor": _PHOSPHOR,
    "midnight": _MIDNIGHT,
    "ruby": _RUBY,
}

DEFAULT_THEME = "premiere"

# Back-compat: existing callers that imported PALETTE keep the
# default Premiere palette.
PALETTE: dict[str, str] = dict(_PREMIERE)


def _rich_palette(theme_name: str) -> dict[str, str]:
    """Return the Rich-style palette dict for ``theme_name``.

    Adds the compound card styles (``card-face`` / ``card-face-red`` /
    ``card-back``) since Rich themes can't reference theme keys after
    ``on``; we bake the hex values.
    """
    base = THEMES.get(theme_name, _PREMIERE)
    paper = base["card-paper"]
    suit_red = base["suit-red"]
    suit_black = base["suit-black"]
    back_bg = base["card-back-bg"]
    accent = base["accent"]
    return {
        **base,
        "card-face": f"{suit_black} on {paper}",
        "card-face-red": f"{suit_red} on {paper}",
        "card-back": f"{accent} on {back_bg}",
    }


def build_theme(theme_name: str = DEFAULT_THEME) -> Theme:
    """Return the Rich :class:`Theme` for the named blackjack21 palette."""
    return Theme(_rich_palette(theme_name))


# ---- TCSS palette header -------------------------------------------

# TCSS uses ``$name`` variables; the static rules in
# ``assets/blackjack.tcss`` reference these. We prepend a small
# ``$name: #HEX;`` block per theme so the same TCSS body works for
# all four palettes.
_TCSS_VARS: tuple[str, ...] = (
    "bg",
    "bg-soft",
    "surface",
    "felt-edge",
    "phosphor",
    "phosphor-dim",
    "accent",
    "accent-dim",
    "success",
    "warning",
    "danger",
    "muted",
    "ink",
    "chip-red",
    "chip-green",
    "chip-black",
    "chip-purple",
)


def tcss_variable_block(theme_name: str = DEFAULT_THEME) -> str:
    """Return a TCSS preamble that declares every ``$var`` for the theme."""
    palette = THEMES.get(theme_name, _PREMIERE)
    lines = [f"${var}: {palette[var]};" for var in _TCSS_VARS if var in palette]
    return "\n".join(lines) + "\n"
