# blackjack21

> *Black Jack* (Ahl, 1978) reinterpretado como software de 2026.
> TUI con [Textual](https://textual.textualize.io), dominio puro,
> partidas reproducibles con seed, paleta de fósforo verde.

```text
                    BLACK JACK
            CREATIVE COMPUTING  MORRISTOWN, NJ
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
