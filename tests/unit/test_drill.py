"""Drill-mode pure-logic tests."""

from __future__ import annotations

import random

import pytest

from blackjack21.application.drill import (
    Topic,
    expected_action,
    grade,
    parse_action,
    random_situation,
    score,
)
from blackjack21.domain.actions import Action
from blackjack21.domain.cards import Rank


@pytest.mark.parametrize("topic", list(Topic))
def test_random_situation_produces_player_turn_state(topic: Topic) -> None:
    rng = random.Random(42)
    situation = random_situation(topic, rng)
    assert len(situation.hand.cards) >= 2
    # The strategy must accept it (i.e. it's a valid live PLAYER_TURN spot).
    rec = expected_action(situation)
    assert isinstance(rec, Action)


def test_pairs_topic_only_yields_pairs() -> None:
    rng = random.Random(0)
    for _ in range(20):
        s = random_situation(Topic.PAIRS, rng)
        assert s.hand.is_pair


def test_soft_topic_always_contains_an_ace() -> None:
    rng = random.Random(0)
    for _ in range(20):
        s = random_situation(Topic.SOFT, rng)
        assert any(c.rank is Rank.ACE for c in s.hand.cards)


def test_hard_topic_never_yields_pair_or_soft() -> None:
    rng = random.Random(0)
    for _ in range(30):
        s = random_situation(Topic.HARD, rng)
        assert not s.hand.is_pair
        assert not s.hand.value.is_soft


def test_surrender_topic_yields_hard_14_15_or_16() -> None:
    rng = random.Random(0)
    for _ in range(20):
        s = random_situation(Topic.SURRENDER, rng)
        assert s.hand.value.total in (14, 15, 16)


def test_parse_action_maps_letters_case_insensitive() -> None:
    assert parse_action("h") is Action.HIT
    assert parse_action("S") is Action.STAND
    assert parse_action("d") is Action.DOUBLE
    assert parse_action("p") is Action.SPLIT
    assert parse_action("U") is Action.SURRENDER
    assert parse_action("hit") is Action.HIT  # only first char matters
    assert parse_action("") is None
    assert parse_action("x") is None


def test_grade_flags_correct_vs_wrong() -> None:
    rng = random.Random(99)
    situation = random_situation(Topic.PAIRS, rng)
    expected = expected_action(situation)
    other = Action.HIT if expected is not Action.HIT else Action.STAND
    assert grade(situation, expected).correct
    assert not grade(situation, other).correct


def test_score_counts_correct_and_total() -> None:
    rng = random.Random(7)
    situations = [random_situation(Topic.ALL, rng) for _ in range(5)]
    correct_answers = [grade(s, expected_action(s)) for s in situations]
    assert score(correct_answers) == (5, 5)
    # Mix one wrong answer in.
    wrong = grade(
        situations[0],
        Action.HIT
        if expected_action(situations[0]) is not Action.HIT
        else Action.STAND,
    )
    assert score([*correct_answers[1:], wrong]) == (4, 5)
