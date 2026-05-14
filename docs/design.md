# Sistema de diseño

## Concepto

> Una mesa de blackjack iluminada por la pantalla CRT verde de un IBM
> 5151 a las dos de la mañana en una redacción de *Creative Computing*.

Fusión moderna-retro: la disposición y los tipos son contemporáneos,
pero la paleta y los detalles (scanline opcional, *blink* del cursor
del jugador, beeps sintetizados) homenajean al terminal monocromo
verde-fósforo donde se jugaba el listado original.

## Paleta

Diseñada en HSL para garantizar contraste WCAG AA sobre el fondo
principal. Cinco roles + variantes:

| Token | Hex | Rol |
| --- | --- | --- |
| `--bg` | `#0A1410` | Fondo principal (verde-negro fósforo apagado) |
| `--bg-soft` | `#0F1F18` | Tarjetas, paneles |
| `--surface` | `#152A22` | Mesa de juego |
| `--phosphor` | `#7CFFB2` | Primario (texto cartas, marcos) |
| `--phosphor-dim` | `#3FA875` | Texto secundario, separadores |
| `--accent` | `#FFD86B` | Apuestas, fichas, números de bankroll |
| `--success` | `#5CFFB2` | Ganas / blackjack |
| `--warning` | `#FFB347` | Push / seguro |
| `--danger` | `#FF6B6B` | Bust / pérdida |
| `--muted` | `#5A6F66` | Help text, footers |
| `--ink` | `#E6FFE9` | Texto general sobre fondos oscuros |

Contraste mínimo medido (sobre `--bg` o `--bg-soft`):

- `--ink` / `--phosphor`: ≥ 7.5 (AAA)
- `--accent`: ≥ 9.0 (AAA)
- `--danger`, `--success`, `--warning`: ≥ 4.8 (AA)

## Tipografía

- **UI**: la familia por defecto del terminal del usuario (la TUI no
  impone fuentes; respeta lo que el usuario haya configurado).
- **Monoespaciado**: ídem, pero las cartas y la mesa usan glifos Unicode
  monoespaciados estables (`♠ ♥ ♦ ♣` y dígitos).
- **Para terminales con Nerd Font**: el logo de la cabecera usa
  glifos de Nerd Font (deshabilitable con `--ascii`).
- Tamaños: la TUI escala con el tamaño del terminal; mínimo 80×24
  garantizado, recomendado 100×30 para el efecto completo.

## Espaciado

Sistema de 1ch / 1 row. Paddings en múltiplos de `[1, 2, 4]`. Cartas
de 7 columnas × 5 filas (incluyendo bordes); espacio entre cartas: 2.

## Iconografía

- Cartas dibujadas con bordes `╭ ╮ ╰ ╯ ─ │`.
- Palos en glifo Unicode con color: ♥ ♦ en `--danger`, ♠ ♣ en `--ink`.
- Fichas de apuesta como `◉` con color `--accent`.
- En modo `--ascii`, las cartas se dibujan con `+-+ | |` y los palos
  como letras `H D S C`.

## Estados clave

| Estado | Diseño |
| --- | --- |
| Splash | Logo "BLACKJACK 21" en ASCII art grande, fila de scanlines, "PRESS ENTER" |
| Bet | Panel central con bankroll, slider numérico y atajos `1/5/25/100/MAX` |
| Deal | Animación de reparto (2 cartas jugador, 1 cara/1 dorso dealer) |
| Player turn | Mesa con mano del jugador resaltada, botones `[H]it [S]tand [D]ouble [/]Split [I]nsurance` |
| Dealer turn | Cartas dealer reveladas una a una, beep por carta |
| Resolve | Banner grande de `WIN/LOSE/PUSH/BLACKJACK`, total con animación |
| Game over | Mensaje "BANKROLL ENDED" cuando el bankroll cae a 0 |
| Error | Línea inferior parpadea en `--danger` con el mensaje |
| Help (`?`) | Modal con reglas y atajos |

## Accesibilidad

- 100% navegable por teclado (la TUI Textual es teclado-first).
- No depende sólo del color: los resultados también se anuncian con
  palabra (`WIN`, `LOSE`, `PUSH`, `BLACKJACK`, `BUST`).
- `--no-color`: degrada a monocromo respetando los acentos por estilo
  (`bold`, `reverse`).
- `--ascii`: sustituye glifos por ASCII puro para terminales legacy.
- `--demo`: lectura no interactiva, sirve también de "fast-forward"
  para captura de partida.

## Toque distintivo memorable

**Phosphor flicker**: cuando una mano se resuelve, el banner
de resultado parpadea brevemente con la misma cadencia del cursor
del 5151 (≈ 540 ms encendido / 90 ms apagado, dos repeticiones).
Es discreto, configurable (`--no-flicker`) y exclusivo de la pantalla
de resolución. La sensación es la de un terminal real anunciando
algo.

## Mockup ASCII (estado *player turn*)

```
 ╭───────────────────────────────────────────────────────────────╮
 │  BLACKJACK 21                            BANKROLL  ◉ 1,000    │
 ╰───────────────────────────────────────────────────────────────╯

           DEALER                          showing 11 (soft)
           ╭─────╮  ╭─────╮
           │  A  │  │ ??  │
           │  ♣  │  │ ??  │
           │    A│  │  ?? │
           ╰─────╯  ╰─────╯

           YOU                             total 18 (hard)   bet 25
           ╭─────╮  ╭─────╮
           │  K  │  │  8  │
           │  ♠  │  │  ♥  │
           │    K│  │    8│
           ╰─────╯  ╰─────╯

   [H]it   [S]tand   [D]ouble   [/]Split   [I]nsurance   [Q]uit
```
