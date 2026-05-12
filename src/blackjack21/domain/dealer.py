"""Dealer policy: deterministic, follows :class:`GameRules`."""

from __future__ import annotations

from blackjack21.domain.deck import Deck
from blackjack21.domain.hand import Hand
from blackjack21.domain.rules import GameRules
from blackjack21.domain.shuffler import Shuffler


def dealer_should_hit(hand: Hand, rules: GameRules) -> bool:
    """Whether the dealer must draw another card under ``rules``."""
    value = hand.value
    if value.is_bust:
        return False
    if value.total < rules.dealer_stands_on:
        return True
    if value.total == rules.dealer_stands_on and value.is_soft:
        return rules.dealer_hits_soft_17
    return False


def play_dealer(
    hand: Hand,
    deck: Deck,
    *,
    rules: GameRules,
    shuffler: Shuffler,
) -> tuple[Hand, Deck]:
    """Run the dealer's mandatory draws and return the final hand + deck."""
    current = hand
    current_deck = deck
    while dealer_should_hit(current, rules):
        card, current_deck = current_deck.draw(shuffler)
        current = current.add(card)
    return current, current_deck
