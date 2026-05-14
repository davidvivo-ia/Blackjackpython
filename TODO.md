# TODO — v1.1 y posteriores

## Prioritarios para v1.1

1. **Multi-jugador en TUI**: el dominio ya soporta 1..7 jugadores; falta
   la coreografía de turnos en la TUI Textual y la disposición visual
   de varias manos simultáneas.
2. **Re-split**: el dominio actual conserva la limitación del original
   (un único split por mano inicial). Exponer regla configurable.
3. **Surrender (late) y *Even money***: añadir como acciones opcionales
   detrás de un flag de variante.
4. **Estadísticas históricas**: rachas, mejor pozo, número de
   blackjacks, mostrar en pantalla post-mano.

## Mejoras menores

- Animación real de reparto en TUI (timeline con `textual.timer`).
- Locale: cadenas en `es` con fallback a `en`.
- Theme switcher: variante "amber" homenajeando los CRT ámbar.
- Replay de partida desde el JSON XDG.

## Limitaciones conocidas v1.0

- TUI mono-jugador. El dominio acepta más, la UI no.
- Sin sonido (planeado para v1.2 vía beeps `numpy` + `sounddevice`).
- El modo `--demo` no anima; va al final tras imprimir eventos.
