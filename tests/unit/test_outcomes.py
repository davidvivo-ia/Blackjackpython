"""Settlement logic tests."""

from __future__ import annotations

import pytest

from blackjack21.domain.cards import Card, Rank, Suit
from blackjack21.domain.hand import Hand
from blackjack21.domain.outcomes import Outcome, settle


def hand(*ranks: Rank, bet: int = 10, **kwargs: object) -> Hand:
    cards = tuple(Card(r, Suit.SPADES) for r in ranks)
    return Hand(cards=cards, bet=bet, **kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("player", "dealer", "expected_outcome", "expected_net"),
    [
        ((Rank.KING, Rank.NINE), (Rank.KING, Rank.SEVEN), Outcome.WIN, 10),
        ((Rank.KING, Rank.SEVEN), (Rank.KING, Rank.NINE), Outcome.LOSS, -10),
        ((Rank.KING, Rank.NINE), (Rank.KING, Rank.NINE), Outcome.PUSH, 0),
        (
            (Rank.KING, Rank.SIX, Rank.SEVEN),
            (Rank.KING, Rank.NINE),
            Outcome.BUST,
            -10,
        ),
        (
            (Rank.KING, Rank.NINE),
            (Rank.KING, Rank.SIX, Rank.SEVEN),
            Outcome.WIN,
            10,
        ),
        ((Rank.ACE, Rank.KING), (Rank.KING, Rank.NINE), Outcome.BLACKJACK, 15),
        ((Rank.ACE, Rank.KING), (Rank.ACE, Rank.KING), Outcome.PUSH, 0),
        ((Rank.KING, Rank.NINE), (Rank.ACE, Rank.KING), Outcome.LOSS, -10),
    ],
)
def test_settle_paths(
    player: tuple[Rank, ...],
    dealer: tuple[Rank, ...],
    expected_outcome: Outcome,
    expected_net: int,
) -> None:
    s = settle(player=hand(*player), dealer=hand(*dealer))
    assert s.outcome is expected_outcome
    assert s.net == expected_net


def test_insurance_wins_on_dealer_blackjack() -> None:
    s = settle(
        player=hand(Rank.KING, Rank.NINE),
        dealer=hand(Rank.ACE, Rank.KING),
        insurance_bet=5,
    )
    assert s.outcome is Outcome.LOSS
    assert s.net == -10
    assert s.insurance_net == 10  # 2:1


def test_insurance_loses_on_no_blackjack() -> None:
    s = settle(
        player=hand(Rank.KING, Rank.NINE),
        dealer=hand(Rank.ACE, Rank.EIGHT),
        insurance_bet=5,
    )
    assert s.outcome is Outcome.PUSH
    assert s.net == 0
    assert s.insurance_net == -5


def test_split_hand_blackjack_pays_even_money() -> None:
    # Ace+King from a split is not a natural blackjack.
    player_h = Hand(
        cards=(Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)),
        bet=10,
        from_split=True,
    )
    dealer_h = hand(Rank.KING, Rank.SEVEN)
    s = settle(player=player_h, dealer=dealer_h)
    assert s.outcome is Outcome.WIN
    assert s.net == 10  # even money, not 3:2
