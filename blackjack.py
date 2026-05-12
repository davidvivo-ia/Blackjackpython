"""Launcher para Windows (y cualquier sistema con Python 3.13+).

Permite ejecutar el juego con ``python blackjack.py`` sin necesidad
de instalar el paquete ni usar ``uv``. Internamente delega en el
mismo Typer ``app`` que la consola-script ``blackjack21``.

El nombre del fichero homenajea al listado original
``blackjack.bas`` de Ahl (1978), preservado en ``legacy/basic/``.

Uso típico en Windows::

    py blackjack.py play
    py blackjack.py play --demo --seed 42
    py blackjack.py doctor

Si arrancas haciendo doble clic, se entra directamente en la TUI
(equivalente a ``blackjack.py play``).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite que el launcher funcione sin pip install / uv sync,
# añadiendo src/ al sys.path si está disponible.
_HERE = Path(__file__).resolve().parent
_SRC = _HERE / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from blackjack21.presentation.cli import app  # noqa: E402


def main() -> None:
    """Arranca la CLI. Sin argumentos abre la TUI directamente."""
    if len(sys.argv) == 1:
        sys.argv.append("play")
    app()


if __name__ == "__main__":
    main()
