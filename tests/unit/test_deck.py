"""Tests for the immutable :class:`Deck`."""

from __future__ import annotations

from collections.abc import Iterable

from blackjack21.domain.cards import Card, Rank, Suit, standard_deck
from blackjack21.domain.deck import RESHUFFLE_THRESHOLD, Deck
from blackjack21.domain.errors import DeckExhaustedError


class IdentityShuffler:
    def shuffled(self, cards: Iterable[Card]) -> tuple[Card, ...]:
        return tuple(cards)


class ReverseShuffler:
    def shuffled(self, cards: Iterable[Card]) -> tuple[Card, ...]:
        return tuple(reversed(tuple(cards)))


def test_fresh_deck_has_52_cards() -> None:
    d = Deck.fresh(IdentityShuffler())
    assert d.remaining == 52
    assert d.discard == ()


def test_draw_returns_top_card_and_new_deck() -> None:
    d = Deck.fresh(IdentityShuffler())
    expected_top = standard_deck()[0]
    card, d2 = d.draw(IdentityShuffler())
    assert card == expected_top
    assert d2.remaining == 51
    assert d.remaining == 52  # original unchanged


def test_reshuffle_when_below_threshold() -> None:
    cards = standard_deck()
    # Deck near exhaustion, with a discard pile waiting.
    deck = Deck(
        cards=cards[:RESHUFFLE_THRESHOLD],
        discard=cards[RESHUFFLE_THRESHOLD:],
    )
    pre_total = deck.remaining + len(deck.discard)
    drawn, after = deck.draw(IdentityShuffler())
    assert drawn in cards
    assert after.remaining + len(after.discard) == pre_total - 1
    # discard cleared into the deck after reshuffle
    assert after.discard == ()


def test_discard_extends_pile() -> None:
    d = Deck.fresh(IdentityShuffler())
    pile = (Card(Rank.ACE, Suit.SPADES),)
    d2 = d.discard_cards(pile)
    assert d2.discard == pile
    assert d2.remaining == 52


def test_discard_empty_is_noop() -> None:
    d = Deck.fresh(IdentityShuffler())
    assert d.discard_cards(()) is d


def test_exhausted_deck_raises() -> None:
    empty = Deck(cards=())
    try:
        empty.draw(IdentityShuffler())
    except DeckExhaustedError:
        pass
    else:
        raise AssertionError("expected DeckExhaustedError")
