"""Smoke tests for the card renderer."""

from __future__ import annotations

import io

from rich.console import Console

from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.domain.hand import Hand
from blackjack21.presentation.render import render_back, render_card, render_hand
from blackjack21.presentation.theme import build_theme


def render(item: object) -> str:
    buf = io.StringIO()
    Console(file=buf, width=80, theme=build_theme(), legacy_windows=False).print(item)
    return buf.getvalue()


def test_render_card_unicode() -> None:
    text = render(render_card(Card(Rank.ACE, Suit.SPADES)))
    assert "A" in text
    assert "♠" in text


def test_render_card_ascii() -> None:
    text = render(render_card(Card(Rank.KING, Suit.HEARTS), ascii_only=True))
    assert "K" in text
    assert "H" in text


def test_render_back_ascii_and_unicode() -> None:
    text_ascii = render(render_back(ascii_only=True))
    text_unicode = render(render_back())
    assert "#" in text_ascii
    assert text_unicode  # any content


def test_render_hand_hides_dealer_hole() -> None:
    hand = Hand(
        cards=(Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)),
        bet=10,
    )
    visible = render(render_hand(hand))
    hidden = render(render_hand(hand, hide_first=True))
    assert "BLACKJACK" in visible
    assert "DEALER SHOWS" in hidden
