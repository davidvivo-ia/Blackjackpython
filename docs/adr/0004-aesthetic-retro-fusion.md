# ADR 0004 — Estética: phosphor green fusion

## Contexto

El original es texto monocromo sobre teletype/CRT. Hay dos extremos:

1. **Réplica pura** (todo verde sobre negro, sin más).
2. **Modernización plana** (estética GitHub-card sin homenaje retro).

Buscamos un punto medio que el usuario sienta como "el blackjack de
Ahl, pero hecho en 2026".

## Opciones consideradas

1. **Mono verde estricto**: nostálgico pero monótono.
2. **Paleta completa moderna**: pierde el alma del original.
3. **Fusion phosphor**: fondo verde-negro fósforo + acentos modernos
   (rojo coral, amarillo ámbar, verde claro) en roles muy
   específicos (apuestas, alertas, resultados). Glifos Unicode para
   palos. Flicker sutil de banner de resultado.

## Decisión

**Fusion phosphor** (opción 3). La paleta arranca en `--bg`
`#0A1410` (negro-verde) con `--phosphor` `#7CFFB2` como primario,
y reservamos color "no fósforo" para señales modernas (apuesta,
peligro, éxito). Documentado en `docs/design.md`.

## Consecuencias

- La TUI es legible en cualquier terminal con 256 colores; en
  terminales de 8 colores degrada con gracia gracias a Textual.
- El flag `--no-color` y `--ascii` cubren accesibilidad y terminales
  legacy.
- Necesitamos un CSS Textual (`src/blackjack21/assets/blackjack.tcss`).
