# blackjack21

> *Black Jack* (Ahl, 1978) reinterpretado como software de 2026.
> TUI con [Textual](https://textual.textualize.io), dominio puro,
> partidas reproducibles con seed, paleta casino-green / oro y
> modo entrenamiento de basic strategy.

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
- **Reglas configurables**:
  - 1 a 8 barajas en el shoe (`--decks N`), 75% de penetración en
    multi-deck.
  - Dealer S17 por defecto, H17 disponible (`--h17`).
  - Acciones `Hit`, `Stand`, `Double`, `Split`, **`Surrender`**, `Insurance`.
  - Pago de blackjack natural 3:2.
- **TUI** Textual con cartas grandes (pip patterns clásicos, J/Q/K
  con piezas de ajedrez, As con explosión), banner de outcome,
  botones de acción clicables, modal de historial y de info.
- **Cuatro temas visuales** (`--theme premiere|phosphor|midnight|ruby`).
- **Modo `--demo --seed 42`**: partida determinista bit a bit,
  útil para tests E2E y para grabar.
- **Modo `drill`**: entrena basic strategy con quizzes aleatorios y
  un breakdown de errores al final.
- **Tip durante el juego**: pulsa `T` para que la TUI te diga la
  jugada de basic strategy con una explicación de una línea
  (`TIP STAND — hard 16 vs dealer 6`).
- **Perfiles + achievements + hall of fame**: bankroll y stats
  persisten por perfil (`--profile NAME`); 7 logros locales
  (first blackjack, hot hand, phoenix, whale, marathon, big pot,
  high roller). `blackjack21 scores` te lo enseña todo.
- **Persistencia XDG**: bankroll, stats y logros en
  `${XDG_DATA_HOME:-~/.local/share}/blackjack21/session.json`
  (o `profiles/<name>.json` para perfiles nombrados).

## Instalación

```bash
uv sync
```

## Uso

```bash
# Jugar (TUI Textual, tema premiere por defecto)
uv run blackjack21 play

# Otras estéticas
uv run blackjack21 play --theme phosphor    # CRT verde
uv run blackjack21 play --theme midnight    # Vegas azul
uv run blackjack21 play --theme ruby --h17  # rojo + dealer H17

# Reglas casino reales
uv run blackjack21 play --decks 6 --h17

# Perfiles
uv run blackjack21 play --profile alice
uv run blackjack21 scores --profile alice
uv run blackjack21 reset --profile alice

# Modo entrenamiento de basic strategy
uv run blackjack21 drill --topic hard --rounds 20 --seed 7
uv run blackjack21 drill --topic pairs
uv run blackjack21 drill --topic surrender

# Partida determinista (sin entrada de usuario)
uv run blackjack21 play --demo --seed 42

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
| `U` | Surrender (si el variante lo permite) |
| `I` | Decline insurance |
| `Y` | Take full insurance |
| `N` | Next hand |
| `T` | Tip — basic strategy para la mano actual |
| `,` | Modal de historial (últimas manos) |
| `.` | Modal de info de sesión y reglas |
| `?` | Ayuda en la barra de mensajes |
| `Q` | Salir guardando |

### Windows: doble clic y listo

`blackjack.py` es autocontenido. Requisitos:

1. Python 3.11 o superior instalado (marca *"Add Python to PATH"* en
   el instalador). Disponible en <https://www.python.org/downloads/>.
2. Descarga / clona este repositorio en cualquier carpeta.

A partir de ahí:

- **Doble clic sobre `blackjack.py`** → la primera vez instala las
  dependencias en tu usuario (`pip install --user typer rich textual
  pydantic structlog`) y arranca la TUI. Si la primera ejecución no
  ve las dependencias recién instaladas, el launcher se reinicia
  automáticamente.
- Si prefieres pasar argumentos (modo demo, doctor, etc.) sin
  abrir terminal, crea un acceso directo con `python blackjack.py
  play --demo --seed 42` como destino.

> **Nota sobre terminales**: Textual rinde bien en *Windows Terminal*
> y PowerShell modernos. El `cmd.exe` clásico y algunas fuentes
> (Consolas en algunos sistemas) degradan los glifos `♠♥♦♣`. En ese
> caso lanza con `--ascii` para usar letras `S H D C` en su lugar:
>
> ```bash
> python blackjack.py play --ascii
> ```

## Desarrollo

```bash
uv sync --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy --strict src
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=90
```

## Procedencia

El listado BASIC original se preserva intacto en `legacy/basic/blackjack.bas`.
Procedencia completa en [`legacy/SOURCES.md`](legacy/SOURCES.md).
Análisis arqueológico en
[`docs/original_program_analysis.md`](docs/original_program_analysis.md).

## Licencia

MIT — ver [`LICENSE`](LICENSE).
