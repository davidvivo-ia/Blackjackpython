"""Hi-Lo counter unit tests."""

from __future__ import annotations

from dataclasses import replace

from blackjack21.application.counter import HiLoCount, compute
from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.domain.deck import Deck
from blackjack21.domain.hand import Hand
from blackjack21.domain.rules import GameRules
from blackjack21.domain.state import GameState, Phase
from blackjack21.infrastructure.rng import IdentityShuffler


def _state(
    *,
    discard: tuple[Card, ...] = (),
    player_cards: tuple[Card, ...] = (),
    dealer_cards: tuple[Card, ...] = (),
    phase: Phase = Phase.PLAYER_TURN,
    num_decks: int = 1,
) -> GameState:
    rules = GameRules(num_decks=num_decks)
    base = Deck.fresh(IdentityShuffler(), num_decks=num_decks)
    deck = replace(base, discard=discard)
    return GameState(
        rules=rules,
        bankroll=1000,
        deck=deck,
        dealer=Hand(cards=dealer_cards),
        player_hands=(Hand(cards=player_cards, bet=10),) if player_cards else (),
        phase=phase,
    )


def test_running_count_sums_visible_cards() -> None:
    """4 low (each +1) and 2 high (each -1) → RC +2."""
    discard = (
        Card(Rank.TWO, Suit.SPADES),
        Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.SIX, Suit.DIAMONDS),
        Card(Rank.THREE, Suit.CLUBS),
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.KING, Suit.HEARTS),
    )
    state = _state(discard=discard)
    c = compute(state)
    assert c.running == +2
    assert c.cards_seen == 6


def test_seven_to_nine_are_neutral() -> None:
    discard = (
        Card(Rank.SEVEN, Suit.SPADES),
        Card(Rank.EIGHT, Suit.HEARTS),
        Card(Rank.NINE, Suit.DIAMONDS),
    )
    c = compute(_state(discard=discard))
    assert c.running == 0
    assert c.cards_seen == 3


def test_hole_card_is_excluded_during_player_turn() -> None:
    """Dealer hole card stays hidden while the player decides."""
    dealer = (
        Card(Rank.SIX, Suit.SPADES),    # visible → +1
        Card(Rank.TEN, Suit.HEARTS),    # hole, hidden
    )
    c = compute(
        _state(dealer_cards=dealer, phase=Phase.PLAYER_TURN)
    )
    assert c.running == 1
    assert c.cards_seen == 1


def test_hole_card_revealed_after_player_turn() -> None:
    dealer = (
        Card(Rank.SIX, Suit.SPADES),    # +1
        Card(Rank.TEN, Suit.HEARTS),    # -1
    )
    c = compute(_state(dealer_cards=dealer, phase=Phase.DEALER_TURN))
    assert c.running == 0
    assert c.cards_seen == 2


def test_true_count_divides_by_decks_remaining() -> None:
    count = HiLoCount(running=6, cards_seen=156, decks_in_shoe=6)
    # 6 decks * 52 = 312 cards, 156 seen -> 156 unseen -> 3 decks remain.
    assert count.decks_remaining == 3.0
    assert count.true_count == 2.0


def test_decks_remaining_never_drops_below_half() -> None:
    """Avoid divide-by-zero when the shoe runs out."""
    count = HiLoCount(running=4, cards_seen=312, decks_in_shoe=6)
    assert count.decks_remaining == 0.5
    assert count.true_count == 8.0


def test_player_hand_counts_too() -> None:
    state = _state(
        player_cards=(
            Card(Rank.TEN, Suit.SPADES),   # -1
            Card(Rank.FIVE, Suit.HEARTS),  # +1
        ),
        dealer_cards=(Card(Rank.FOUR, Suit.SPADES), Card(Rank.NINE, Suit.HEARTS)),
        phase=Phase.PLAYER_TURN,
    )
    # Player visible: -1 +1 = 0
    # Dealer visible (only upcard 4): +1
    c = compute(state)
    assert c.running == 1
    assert c.cards_seen == 3
