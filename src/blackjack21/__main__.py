"""Command-line entry point.

Wires the Typer ``app`` so that ``python -m blackjack21`` and the
console-script ``blackjack21`` both work.
"""

from __future__ import annotations

from blackjack21.presentation.cli import app

__all__ = ["app"]


if __name__ == "__main__":
    app()
