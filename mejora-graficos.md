# mejora-graficos.md — Plan de mejora visual al máximo

> Foco exclusivo en gráficos. Complementa `mejora.md` (que cubre
> reglas, pedagogía, distribución) sin solaparse.

## 1. Estado visual actual (post `d94521a`)

Lo que ya tenemos:

- Cartas 11×9 con rank+palo en esquina superior izquierda y mirror
  inferior derecha, palo grande (o letra J/Q/K) en el centro, borde
  oro `ROUNDED`, fondo `card-paper` (#F5F1E6).
- Reverso felt-verde con patrón `◆ ✦ ◆`.
- Banner de outcome con `box.HEAVY` (doble para BJ), color por
  resultado, delta `+$25` / `−$50`.
- Fila de stats (BALANCE / CURRENT BET / HAND VALUE) con bordes oro.
- Fila de contadores (W L P BJ STREAK ±N) con color streak.
- Fichas con disco `●` y cuatro bordes de color (red/green/black/purple).
- Cabecera `♠ ♥ PREMIERE BLACKJACK ♦ ♣`.

Limitaciones que sí podemos atacar en terminal:

- Cartas numéricas muestran **una sola pip central** — las reales muestran
  N pips dispuestos en patrón clásico.
- J/Q/K muestran solo la letra — falta personalidad de figura.
- HIT / STAND / DOUBLE etc. son **bindings de teclado**, no botones — el
  mock de Stitch los muestra como pills clicables.
- Sin **animaciones**: cartas aparecen instantáneamente.
- Una sola **paleta** — no hay tema alternativo (CRT amber, midnight, etc.).
- Sin **textura de fieltro** en el fondo; un verde plano.
- Sin **sombras**: las cartas flotan sin profundidad.
- Apuesta pendiente solo como número — sin **pila de fichas visual**.
- Insurance todavía con `Input` de texto, no botones Yes/No.
- Layout **fijo a 80+ cols** — en ventanas estrechas se ve roto.

## 2. Objetivos

1. Que un screenshot del juego sea distinguible de un screenshot de un
   cliente nativo de casino.
2. Que cada acción tenga su feedback visual (animación o highlight).
3. Que jugar con ratón sea posible end-to-end (chips, deal, hit, etc.).
4. Que el usuario pueda elegir entre 3-4 estéticas distintas.
5. Que la TUI degrade con elegancia en terminales pequeñas (60 cols).

---

## Phase G1 — Pip patterns + cartas figura (1–2 días) ★ máximo impacto

### G1.1 Pips clásicos en 2-10

`render.py` se reescribe: en lugar de un solo palo centrado, dibujar
los **N pips en posición canónica**. Tabla canónica para 7-col×5-fila
(misma geometría actual):

```
2:   .  .         3:   ♠  .         4:   ♠  ♠         5:   ♠  ♠
     ♠  .              .  .              .  .              .  ♠
     .  .              ♠  .              .  .              .  .
     ♠  .              .  .              ♠  ♠              ♠  ♠
     .  .              .  .              .  .              .  .
                       ♠  .

6:   ♠ . ♠       7:   ♠ . ♠       8:   ♠ . ♠       9:   ♠ . ♠
     . . .            . ♠ .            ♠ . ♠            ♠ . ♠
     ♠ . ♠            ♠ . ♠            . . .            ♠ . ♠
     . . .            ♠ . ♠            ♠ . ♠            ♠ . ♠
     ♠ . ♠            . . .            ♠ . ♠            ♠ . ♠

A:   .  .  .  .       10: ♠ . ♠
     .  .  .  .           ♠ . ♠
     .  ♠  .  .           ♠ . ♠
     .  .  .  .           ♠ . ♠
     .  .  .  .           ♠ . ♠
```

Implementación: `_pip_grid: dict[int, list[str]]` con la disposición
para cada rank numérico. `render_card` elige entre pip-grid (números)
y face-glyph (J/Q/K/A).

Tests: para cada rank 2-10 verificar que el output contiene N palos.

### G1.2 J/Q/K con figura ASCII

Cada face card lleva un glyph central elaborado. Opciones:

| Rank | Glyph central | Idea |
|---|---|---|
| J | `♞`+letra J | Caballero/jack |
| Q | `♛`+letra Q | Corona reina |
| K | `♚`+letra K | Corona rey |

Para máxima personalidad, usar 3 líneas de "retrato" pseudo-figlet:

```
   ♛
  /Q\
   ‾
```

Pegado al palo del corner. Test: render con K shows "♚".

### G1.3 As con palo extra-grande

El As muestra el palo agrandado: usar el caracter unicode "filled
larger" o repetir el palo formando una bandera ASCII:

```
   ♠ ♠
   ♠♠♠
   ♠ ♠
```

### G1.4 Sombra inferior

Añadir una línea `▁▁▁▁▁▁▁▁▁` en gris bajo cada carta para sugerir
sombra. Implementado como una segunda fila del Group que envuelve el
Panel.

---

## Phase G2 — Botones de acción visibles (1 día) ★ paridad con el mock

Hoy las acciones son solo teclas. El mock de Stitch los pinta como
**pills horizontales** abajo del player-hand. Cambio:

- Durante `PLAYER_TURN`, mostrar 5 botones: `HIT` `STAND` `DOUBLE`
  `SPLIT` `SURRENDER`. Los no legales se renderizan en gris/disabled.
- Reuso de `Button.bet-btn`-style con colores semánticos:
  - HIT: green (`$phosphor`)
  - STAND: ink (`$ink`)
  - DOUBLE: gold (`$accent`)
  - SPLIT: gold-dim
  - SURRENDER: muted

Clic = misma acción que la tecla, vía `on_button_pressed`.

Botones desaparecen (`display: False`) en cualquier fase ≠ PLAYER_TURN.

Insurance también se sube a botones: `INSURANCE $X` (gold) + `NO THANKS`
en lugar del `Input`. Si el jugador quiere apostar menos del máximo,
chip-tap suma el insurance (reusa la misma fila).

---

## Phase G3 — Animaciones (2 días) ★ "está viva"

`textual.timer.Timer` para coreografía. Cada animación es opcional y
controlada por `--anim {none,fast,normal}` (default `fast`).

### G3.1 Reparto inicial

Al pulsar DEAL, las 4 cartas se reparten en secuencia:

1. tick 0ms: jugador-1 aparece (fade-in via CSS opacity transition)
2. tick 180ms: dealer-up
3. tick 360ms: jugador-2
4. tick 540ms: dealer-hole (back-of-card)

Estado intermedio: durante el reparto, el resto del UI queda
"frozen". Botones disabled.

### G3.2 Hit

Nueva carta del HIT entra deslizándose desde la derecha: 3 frames de
caracteres parciales antes de llegar a su posición.

Si la implementación es muy compleja, basta un fade-in.

### G3.3 Reveal de la hole card

En DEALER_TURN, el reverso felt-verde se reemplaza por la cara real
con un fade rápido (300ms). Luego dealer hace HIT cards una a una con
gap de 250ms.

### G3.4 Outcome banner zoom

El banner aparece con un pulso (fontaña/zoom): renderizar 3 frames
con escala creciente (1×1, 2×2, 4×4 caracteres por glyph) en 200ms
total. Implementable con tres updates consecutivos del `#status`.

### G3.5 Toggle global

`--anim none` para CI y para terminales lentos. Las animaciones nunca
deben modificar el estado lógico — son puramente cosméticas, y el
test E2E usa `--anim none`.

---

## Phase G4 — Temas alternativos (1 día)

`presentation/themes/` con paletas paralelas. CLI flag `--theme NAME`:

| Tema | Fondo | Acento | Carta | Inspiración |
|---|---|---|---|---|
| `premiere` (default) | casino green | gold | paper white | actual |
| `phosphor` | black | phosphor green | beige | CRT amber-green clásico (la v1.0) |
| `midnight` | navy blue | silver | white | Vegas alto-standing |
| `ruby` | dark red | gold | ivory | Asia luxury |

Cada tema es un dict en `PALETTE_VARIANTS` que mergea sobre el base.
TCSS usa los mismos nombres de variable, solo cambia su valor.

UI: Settings screen permite cambiar en caliente. Persistido en
`settings.json` (XDG).

---

## Phase G5 — Modales: history, settings, scores (1–2 días)

`textual.screen.ModalScreen` para pantallas secundarias:

### G5.1 History (`,`)

Tabla `rich.Table` con las últimas 50 manos. Columnas:
`#  bet  player→  dealer→  outcome  net  balance`.
Se rellena al persistir cada mano.

### G5.2 Settings (`.`)

Form con switches:
- Theme: dropdown
- Animations: none/fast/normal
- ASCII glyphs: on/off
- Show pip patterns: on/off
- Show stats counters: on/off

Cambios efectivos inmediatamente (excepto seed/rules → próxima sesión).

### G5.3 Hall of Fame (`-`)

Cumple la pantalla `clasificación` del mock:
- Top 5 biggest pots
- Top 5 longest win streaks
- Top 5 highest bankrolls reached

Sólo perfil local (por ahora). Persistido en `leaderboard.json`.

---

## Phase G6 — Pulido visual (1 día)

### G6.1 Textura de fieltro

Fondo no es verde plano sino salpicado de `·` o `▪` cada N celdas
con color `bg-soft` 50% — sutil, pero da textura. Implementable
como un widget de fondo posicionado absolutamente.

### G6.2 Highlight de chip seleccionado

Cuando añades una ficha al bet pendiente, esa denomination "pulsa"
durante 300ms (CSS animation o tres frames de border-color).

### G6.3 Streak fire

Si `_streak >= 5`, en la counter row poner `🔥 +5` con bg gradient
gold→red. Si streak `<= -5`, poner `❄ −5` con bg azul muted.

### G6.4 Sparkline de bankroll

Mini gráfica horizontal en la counter row mostrando los últimos 20
valores de bankroll con caracteres `▁▂▃▄▅▆▇█`:
```
$1,250  ▂▃▄▅▆▆▇█  (last 20 hands)
```
Sólo en pantallas anchas (>100 cols).

### G6.5 Pila de fichas para pending bet

En lugar de "CURRENT BET $125", mostrar:
```
CURRENT BET
  ●●●  $125
  100 25
```
Donde los `●` son del color de la denominación.

### G6.6 Insurance banner

Cuando el dealer muestra As, banner ámbar centrado entre las manos:
```
╔══════════════════════════════════╗
║   DEALER SHOWS A — INSURANCE?    ║
║   half-bet pays 2:1 on dealer BJ ║
║       [YES $X]    [NO THANKS]    ║
╚══════════════════════════════════╝
```

---

## Phase G7 — Layout responsivo (1 día)

Detectar `self.size.width` y elegir variante:

| Ancho | Modo |
|---|---|
| ≥ 120 | full: cartas 11×9, todo visible |
| 80-119 | compact: cartas 9×7, sin sparkline |
| 60-79 | tight: cartas 7×5, sin counter row |
| < 60 | ascii-fallback: forzar `--ascii`, layout single-column |

Implementado en `on_resize` re-componiendo la TCSS via media-query
o ramas explícitas.

---

## 8. Lo que NO haremos

- **Imágenes de verdad** (PNG en terminal vía Sixel/Kitty). Ya hay
  proyectos que lo intentan; rompe portabilidad y no aporta vs ASCII
  bien hecho.
- **Particle effects exuberantes** (confeti permanente, fuegos
  artificiales). Marca casino-amateur, no premiere.
- **3D pseudo-isométrico**. Costoso y feo en mono-espacio.
- **Cursor del ratón custom**. Limitación de Textual.
- **Música/sonido**. Ya descartado en `mejora.md`.

## 9. Estimación

| Fase | Esfuerzo | Riesgo | Prioridad |
|---|---|---|---|
| G1 Pips + faces + sombra | 1–2d | bajo | **HIGH** |
| G2 Botones de acción | 1d | bajo | **HIGH** |
| G3 Animaciones | 2d | medio (CI) | **HIGH** |
| G4 Temas | 1d | bajo | medium |
| G5 Modales | 1–2d | medio | medium |
| G6 Pulido | 1d | bajo | medium |
| G7 Responsive | 1d | medio (test) | medium |

Total: **8–10 días** de trabajo gráfico puro, en 7 PRs.

## 10. Próximo paso concreto

Empezar por **G1.1 (pip patterns)** porque:
- Es el cambio que más cambia la *foto*.
- Es contenido en `render.py`, sin tocar dominio.
- Es trivial de testear (count de glyphs por rank).
- Cierra el "uncanny valley" entre nuestras cartas y cartas reales.

Tras G1, **G2 (botones de acción)** porque iguala visualmente con el
mock de Stitch y permite jugar 100% con ratón.

Si dices "adelante", arranco por G1.
