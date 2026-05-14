"""CLI smoke test for the ``drill`` subcommand."""

from __future__ import annotations

import random

from typer.testing import CliRunner

from blackjack21.application.drill import (
    Topic,
    expected_action,
    random_situation,
)
from blackjack21.presentation.cli import app

runner = CliRunner()


def _correct_letter(action: object) -> str:
    """Map an Action to its drill-CLI single-letter key."""
    return {
        "hit": "H",
        "stand": "S",
        "double": "D",
        "split": "P",
        "surrender": "U",
    }[str(action.value if hasattr(action, "value") else action)]


def test_drill_with_seed_scores_all_correct_when_answering_with_strategy() -> None:
    """Replay the same seed and pre-answer with the expected action each round."""
    seed = 42
    rounds = 4
    # Re-run the exact same generation so we know the expected sequence.
    rng = random.Random(seed)
    situations = [
        random_situation(Topic.HARD, rng) for _ in range(rounds)
    ]
    answers = [_correct_letter(expected_action(s)) for s in situations]
    stdin = "\n".join(answers) + "\n"
    result = runner.invoke(
        app,
        ["drill", "--topic", "hard", "--rounds", str(rounds), "--seed", str(seed)],
        input=stdin,
    )
    assert result.exit_code == 0, result.stdout
    assert f"SCORE {rounds}/{rounds}" in result.stdout
    assert "100.0%" in result.stdout


def test_drill_invalid_letter_reprompts_then_accepts() -> None:
    """Garbage input must reprompt without crashing."""
    seed = 1
    rng = random.Random(seed)
    s = random_situation(Topic.HARD, rng)
    correct = _correct_letter(expected_action(s))
    result = runner.invoke(
        app,
        ["drill", "--topic", "hard", "--rounds", "1", "--seed", str(seed)],
        input=f"xx\n{correct}\n",
    )
    assert result.exit_code == 0
    assert "Invalid" in result.stdout
    assert "SCORE 1/1" in result.stdout
