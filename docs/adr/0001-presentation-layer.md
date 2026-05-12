# ADR 0001 — Capa de presentación: Textual TUI

## Contexto

El original es un programa BASIC de consola con `PRINT`/`INPUT` puro:
sin gráficos, sin sprites, sin posicionamiento de cursor sofisticado.
El espíritu es el de un *terminal verde* en línea de comandos.

## Opciones consideradas

1. **CLI plana con Typer + Rich**: rápida de implementar pero pierde
   la sensación de "mesa" del juego; cada turno se renderiza como
   bloques sueltos en stdout.
2. **TUI con Textual**: respeta la naturaleza textual, permite mesa
   persistente con bindings, soporta CSS para la paleta y se adapta
   a la terminal del usuario.
3. **Gráfico con pygame-ce**: contradice el origen del juego (texto
   puro) y desperdicia complejidad en una mecánica que cabe en una
   pantalla.

## Decisión

**Textual TUI** como modo principal de juego. Mantenemos un sub-modo
CLI no interactivo (`--demo`) que vuelca eventos de partida en texto
plano y sirve a la vez para tests E2E y para grabar GIFs/SVGs.

## Consecuencias

- Necesitamos `textual` y `rich` como dependencias de producción.
- El sistema de diseño (paleta, espaciado, estados) se vive en CSS
  bajo `src/blackjack21/assets/`.
- La capa de aplicación expone eventos planos para que tanto la TUI
  como la salida `--demo` consuman el mismo flujo.
- Los tests visuales son responsabilidad del modo `--demo` con
  snapshots; no perseguimos snapshot testing de la propia TUI.
