# blackjack21

> *Black Jack* (Ahl, 1978) reinterpretado como software de 2026.
> TUI con [Textual](https://textual.textualize.io), dominio puro,
> partidas reproducibles con seed, paleta de fósforo verde.

```text
                    BLACK JACK
            CREATIVE COMPUTING  MORRISTOWN, NJ
```

## Demo

```text
───────────────────── BLACKJACK 21  ·  seed=42  ·  hands=3 ─────────────────────

Hand 1  ·  bankroll 1000  ·  bet 25
  bet 25  bankroll 1000
  you : T♠
  dealer: J♥
  you : K♥
  dealer: 4♠
  action: STAND
  dealer reveals: 4♠
  dealer: 9♥
  outcome: WIN  net +25  bankroll 1025

Hand 2  ·  bankroll 1025  ·  bet 25
  ...
  outcome: BLACKJACK  net +37  bankroll 1062

      Demo Summary
┌────────────────┬──────┐
│ Final bankroll │ 1037 │
│ Hands played   │ 3    │
│ Blackjacks     │ 1    │
└────────────────┴──────┘
```

## Características

- **Dominio inmutable** y puro: `dataclass(frozen=True, slots=True)`,
  cero IO, 100% testeable.
- **Reglas clásicas** del listado original:
  - 1 baraja de 52 cartas, *reshuffle* automático con descarte.
  - Apuestas 1..500, bankroll inicial 1000.
  - Acciones `Hit`, `Stand`, `Double down`, `Split`, `Insurance`.
  - Dealer planta en 17+ (S17, incluido soft 17).
  - Pago de blackjack natural 3:2.
- **TUI** Textual con paleta phosphor green, atajos de teclado y
  modo `--ascii` para terminales legacy.
- **Modo `--demo --seed 42`**: partida determinista bit a bit,
  útil para tests E2E y para grabar.
- **Persistencia XDG**: el bankroll y las estadísticas se guardan en
  `${XDG_DATA_HOME:-~/.local/share}/blackjack21/session.json`.

## Instalación

```bash
uv sync
```

## Uso

```bash
# Jugar (TUI Textual)
uv run blackjack21 play

# Partida determinista (sin entrada de usuario)
uv run blackjack21 play --demo --seed 42

# Reiniciar bankroll y estadísticas
uv run blackjack21 reset

# Diagnóstico de terminal
uv run blackjack21 doctor
```

### Windows: doble clic y listo

`blackjack.py` es autocontenido. Requisitos:

1. Python 3.11 o superior instalado (marca *"Add Python to PATH"* en
   el instalador). Disponible en <https://www.python.org/downloads/>.
2. Descarga / clona este repositorio en cualquier carpeta.

A partir de ahí:

- **Doble clic sobre `blackjack.py`** → la primera vez instala las
  dependencias en tu usuario (`pip install --user typer rich textual
  pydantic structlog`) y arranca la TUI. Las siguientes veces
  arrancan al instante.
- Si prefieres pasar argumentos (modo demo, doctor, etc.) sin
  abrir terminal, crea un acceso directo con `python blackjack.py
  play --demo --seed 42` como destino.

> Si tras el doble clic la ventana se cierra sola, abre `cmd.exe` y
> lanza `python blackjack.py` desde la carpeta del repo: verás el
> error completo y el script hace `input("Pulsa Enter…")` antes de
> salir si algo falla.

> **Nota sobre terminales**: Textual rinde bien en *Windows Terminal*
> y PowerShell modernos. El `cmd.exe` clásico es funcional pero
> degrada los colores y algunos glifos Unicode; en ese caso pasa
> `--ascii` (planeado para v1.1) o usa Windows Terminal.

### Atajos de teclado (TUI)

| Tecla | Acción |
| --- | --- |
| `H` | Hit |
| `S` | Stand |
| `D` | Double down |
| `/` | Split |
| `I` | Insurance (sólo si el dealer muestra As) |
| `?` | Ayuda |
| `Q` | Salir guardando |

## Desarrollo

```bash
uv sync --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy --strict src
uv run pytest --cov=src --cov-report=term-missing
```

## Procedencia

El listado BASIC original se preserva intacto en `legacy/basic/blackjack.bas`.
Procedencia completa en [`legacy/SOURCES.md`](legacy/SOURCES.md).
Análisis arqueológico en
[`docs/original_program_analysis.md`](docs/original_program_analysis.md).

## Licencia

MIT — ver [`LICENSE`](LICENSE).
