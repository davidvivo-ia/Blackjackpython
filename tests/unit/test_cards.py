"""Tests for :mod:`blackjack21.domain.cards`."""

from __future__ import annotations

from blackjack21.domain.cards import Card, Rank, Suit, standard_deck


def test_suit_glyphs_unique() -> None:
    glyphs = {s.glyph for s in Suit}
    assert glyphs == {"♠", "♥", "♦", "♣"}


def test_suit_is_red() -> None:
    assert Suit.HEARTS.is_red
    assert Suit.DIAMONDS.is_red
    assert not Suit.SPADES.is_red
    assert not Suit.CLUBS.is_red


def test_rank_hard_values() -> None:
    assert Rank.ACE.hard_value == 1
    assert Rank.TWO.hard_value == 2
    assert Rank.TEN.hard_value == 10
    assert Rank.JACK.hard_value == 10
    assert Rank.QUEEN.hard_value == 10
    assert Rank.KING.hard_value == 10


def test_rank_predicates() -> None:
    assert Rank.ACE.is_ace
    assert Rank.JACK.is_face
    assert Rank.QUEEN.is_face
    assert Rank.KING.is_face
    assert not Rank.TEN.is_face


def test_card_repr_unicode_and_ascii() -> None:
    c = Card(Rank.ACE, Suit.SPADES)
    assert str(c) == "A♠"
    assert c.to_ascii() == "AS"


def test_card_is_hashable_and_orderable() -> None:
    a = Card(Rank.TWO, Suit.CLUBS)
    b = Card(Rank.THREE, Suit.CLUBS)
    assert hash(a) != hash(b)
    assert a < b
    assert {a, b} == {b, a}


def test_standard_deck_has_52_unique_cards() -> None:
    deck = standard_deck()
    assert len(deck) == 52
    assert len(set(deck)) == 52
