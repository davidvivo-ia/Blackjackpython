"""Launcher autocontenido para Windows (y cualquier OS con Python 3.11+).

Pensado para "doble clic y listo". No necesita ``uv``, no necesita
``pip install -e .`` previo, no necesita activar un venv. La primera
vez que se ejecuta:

1. Detecta si faltan ``typer``, ``rich``, ``textual``, ``pydantic`` o
   ``structlog`` en el Python actual.
2. Si faltan, los instala con ``pip install --user`` y vuelve a
   importarlos.
3. Arranca la TUI (``play``) o el sub-comando que pases por argumentos.

Si la importacion del juego revienta o el proceso termina con error,
se hace ``input("Pulsa Enter para cerrar...")`` para que la ventana
de la consola no se cierre antes de que puedas leer el mensaje (algo
que pasa al hacer doble clic en .py en Windows).

El nombre del fichero homenajea al listado original ``blackjack.bas``
de Ahl (1978), preservado en ``legacy/basic/``.

Uso desde linea de comandos (opcional)::

    py blackjack.py             # abre la TUI
    py blackjack.py play --demo --seed 42
    py blackjack.py doctor
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

# Paquetes que el juego necesita para funcionar.
_REQUIRED = ("typer", "rich", "textual", "pydantic", "structlog")

# Anade src/ al sys.path para no requerir 'pip install -e .'.
_HERE = Path(__file__).resolve().parent
_SRC = _HERE / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _missing_packages() -> list[str]:
    missing: list[str] = []
    for name in _REQUIRED:
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append(name)
    return missing


def _bootstrap_dependencies() -> None:
    """Instala las dependencias que falten en el Python actual."""
    missing = _missing_packages()
    if not missing:
        return
    print(f"Instalando dependencias: {', '.join(missing)} ...")
    cmd = [sys.executable, "-m", "pip", "install", "--user", *missing]
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as exc:
        print(f"\nNo se pudieron instalar las dependencias automaticamente: {exc}")
        print("Pruebalo manualmente con:")
        print(f"  {sys.executable} -m pip install {' '.join(missing)}")
        raise
    importlib.invalidate_caches()


def _pause_on_exit() -> None:
    """Evita que la ventana se cierre antes de leer el mensaje."""
    try:
        input("\nPulsa Enter para cerrar...")
    except (EOFError, KeyboardInterrupt):
        pass


def _check_python_version() -> None:
    if sys.version_info < (3, 11):
        print(
            f"blackjack21 necesita Python 3.11 o superior. "
            f"Tienes {sys.version.split()[0]}."
        )
        print("Descarga una version compatible en https://www.python.org/downloads/")
        _pause_on_exit()
        sys.exit(1)


def main() -> None:
    _check_python_version()
    _bootstrap_dependencies()

    # Importa la app DESPUES del bootstrap para que las deps esten listas.
    from blackjack21.presentation.cli import app

    if len(sys.argv) == 1:
        sys.argv.append("play")

    try:
        app()
    except SystemExit as exc:  # Typer sale con SystemExit normalmente.
        if exc.code not in (None, 0):
            _pause_on_exit()
        raise
    except BaseException:
        import traceback

        traceback.print_exc()
        _pause_on_exit()
        raise


if __name__ == "__main__":
    main()
