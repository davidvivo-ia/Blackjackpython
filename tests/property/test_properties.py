"""Property-based tests for the domain."""

from __future__ import annotations

import hypothesis.strategies as st
from hypothesis import given, settings

from blackjack21.domain.cards import Card, Rank, Suit, standard_deck
from blackjack21.domain.deck import RESHUFFLE_THRESHOLD, Deck
from blackjack21.domain.hand import evaluate
from blackjack21.infrastructure.rng import SystemShuffler

cards_strategy = st.lists(
    st.builds(Card, st.sampled_from(list(Rank)), st.sampled_from(list(Suit))),
    min_size=0,
    max_size=10,
)


@given(cards_strategy)
def test_evaluate_total_is_at_least_minimum_value(cards: list[Card]) -> None:
    """Total cannot be lower than the sum treating every Ace as 1."""
    v = evaluate(tuple(cards))
    hard = sum(c.rank.hard_value for c in cards)
    assert v.total >= hard


@given(cards_strategy)
def test_evaluate_total_never_exceeds_21_when_not_bust(cards: list[Card]) -> None:
    """If not bust, total is in [0, 21]."""
    v = evaluate(tuple(cards))
    if not v.is_bust:
        assert 0 <= v.total <= 21


@given(st.integers(min_value=0, max_value=10_000))
def test_shuffler_preserves_multiset(seed: int) -> None:
    """Shuffling a deck must preserve the multiset of cards."""
    sh = SystemShuffler(seed=seed)
    original = standard_deck()
    shuffled = sh.shuffled(original)
    assert sorted(shuffled) == sorted(original)
    assert len(shuffled) == 52


@given(st.integers(min_value=0, max_value=10_000))
@settings(max_examples=25)
def test_repeated_draws_preserve_total_cards(seed: int) -> None:
    """Drawing then discarding never loses cards."""
    sh = SystemShuffler(seed=seed)
    deck = Deck.fresh(sh)
    total = deck.remaining + len(deck.discard)
    drawn: list[Card] = []
    while deck.remaining > RESHUFFLE_THRESHOLD:
        card, deck = deck.draw(sh)
        drawn.append(card)
    assert deck.remaining + len(deck.discard) + len(drawn) == total
