"""Theme palette sanity checks."""

from __future__ import annotations

import pytest

from blackjack21.presentation.theme import (
    DEFAULT_THEME,
    THEMES,
    build_theme,
    tcss_variable_block,
)


def test_four_themes_are_exposed() -> None:
    assert set(THEMES) == {"premiere", "phosphor", "midnight", "ruby"}
    assert DEFAULT_THEME == "premiere"


@pytest.mark.parametrize("name", list(THEMES))
def test_each_theme_carries_the_full_palette(name: str) -> None:
    palette = THEMES[name]
    required = {
        "bg", "bg-soft", "surface", "felt-edge",
        "phosphor", "phosphor-dim", "accent", "accent-dim",
        "success", "warning", "danger", "muted", "ink",
        "chip-red", "chip-green", "chip-black", "chip-purple",
        "card-paper", "card-ink", "suit-red", "suit-black", "card-back-bg",
    }
    missing = required - palette.keys()
    assert not missing, f"{name} is missing keys: {missing}"
    # Every value must be a hex colour string.
    for key, value in palette.items():
        assert value.startswith("#"), f"{name}.{key} = {value!r} is not hex"


@pytest.mark.parametrize("name", list(THEMES))
def test_build_theme_resolves_card_face_compound_style(name: str) -> None:
    theme = build_theme(name)
    style = theme.styles.get("card-face")
    assert style is not None
    # The compound style must carry a background color (the card paper).
    assert style.bgcolor is not None


@pytest.mark.parametrize("name", list(THEMES))
def test_tcss_variable_block_declares_each_var(name: str) -> None:
    block = tcss_variable_block(name)
    for var in ("bg", "bg-soft", "accent", "phosphor"):
        assert f"${var}:" in block, f"{name}: {var} not declared"


def test_unknown_theme_falls_back_to_premiere() -> None:
    """An unknown theme name doesn't crash; it uses Premiere."""
    block = tcss_variable_block("does-not-exist")
    # Same content as Premiere
    assert block == tcss_variable_block("premiere")
