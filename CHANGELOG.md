# Changelog

Todos los cambios relevantes se documentan en este archivo. Sigue
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
[Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] — 2026-05-12

### Preservado del original

- Una sola baraja de 52 cartas con descarte y *reshuffle*.
- Apuestas 1..500 por mano.
- Acciones del jugador: Hit, Stand, Double down, Split, Insurance.
- Dealer planta en 17 o más (S17 incluyendo soft 17).
- Pago de blackjack natural 3:2.
- Bucle de manos consecutivas con bankroll acumulado.

### Modernizado

- Lenguaje: Python 3.13+ con `dataclass(frozen=True, slots=True)`.
- Capa de presentación: Textual TUI con paleta phosphor green.
- Modo `--demo --seed N` reproducible.
- Persistencia opcional del bankroll en `XDG_DATA_HOME`.
- Tipado estricto (`mypy --strict`).
- Cobertura ≥ 80% en el dominio.

### Añadido

- Comando `blackjack21 reset` para borrar el estado guardado.
- Comando `blackjack21 doctor` para diagnosticar el terminal.
- Tecla `Q` para abandonar guardando el bankroll.
- Modo `--ascii` para terminales sin Unicode.

### Licencias creativas

- TUI por defecto en lugar de prompts línea-a-línea: el formato CLI
  está reservado al modo `--demo` y a los tests E2E.
- Multi-jugador (1..7) del original queda en `TODO.md` para v1.1;
  v1.0 ofrece sólo 1 jugador para focalizar el diseño.
- El "blackjack natural" se detecta automáticamente tras el reparto
  inicial (en el original había que recordar pulsar `S` para
  cobrar 3:2).

### Bugs corregidos

- Reshuffle prematuro causado por `GOSUB 120` (línea 1810): la versión
  moderna usa una política explícita basada en cartas restantes.
- Sin salida limpia: añadido botón `Q` que persiste el estado.
- `Z(I)` sin `DIM` y `D$` con caracteres de control han sido
  reemplazados por estructuras tipadas y glifos Unicode legibles.
