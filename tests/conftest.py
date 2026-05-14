"""Shared pytest fixtures and helpers."""

from __future__ import annotations

import pytest

from blackjack21.infrastructure.rng import IdentityShuffler, SystemShuffler


@pytest.fixture
def identity_shuffler() -> IdentityShuffler:
    return IdentityShuffler()


@pytest.fixture
def seeded_shuffler() -> SystemShuffler:
    return SystemShuffler(seed=42)
