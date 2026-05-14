# Análisis arqueológico del Black Jack original

## Encuadre

| Campo | Valor |
| --- | --- |
| Título | `BLACK JACK` |
| Cabecera del listado | `BLACK JACK / CREATIVE COMPUTING MORRISTOWN, NEW JERSEY` |
| Fuente | David H. Ahl, *BASIC Computer Games* (1978), juego nº 10 |
| Lenguaje | BASIC genérico Microsoft/DEC (sin extensiones específicas) |
| Plataforma canónica | Terminal de tiempo compartido (Teletype/CRT, 80 col) |
| Año estimado | 1973-1978 |
| Tamaño | 321 líneas, 1 fichero, ~8 KiB |
| Modo de juego | 1-7 jugadores humanos contra una banca controlada por la CPU |

### Sinopsis funcional

Juego clásico de *21*. La banca usa una baraja única de 52 cartas que se
re-baraja cuando quedan menos de dos cartas por jugador. En cada mano
cada jugador apuesta entre 1 y 500, recibe dos cartas y elige `H`it,
`S`tand, `D`ouble down o `/` (split). Se ofrece seguro si la banca
muestra un As. La banca paga 3:2 por blackjack natural y planta en
17+ (incluido soft 17). Las apuestas se acumulan en un total por jugador
a través de las manos.

### Lectura crítica

- **Concisión brutal**: 321 líneas implementan reparto, evaluación
  con ases blandos/duros, split, doble, seguro y blackjack natural.
  Toda la lógica gira alrededor de cinco arrays globales `P, Q, R, B, S`.
- **Idiomática de la época**: `GOSUB` en lugar de funciones, `ON … GOTO`
  para despachar acciones del jugador, codificación numérica densa de
  los totales (ver "Codificación de la mano" abajo).
- **Trampa famosa**: el bucle de re-shuffle (líneas 110-220) se ejecuta
  cuando `C<51`, y mete el discard pile encima de las cartas no
  repartidas con un Fisher-Yates. Es correcto en intención, frágil en
  los offsets.
- **Bug confirmado**: en la línea 1810 el código llama a `GOSUB 120`
  (`GOSUB 120` es la rama "RESHUFFLING…" pero la subrutina arranca en
  100). Saltarse las dos primeras líneas omite la guarda `IF C<51 THEN
  230`, así que en la práctica fuerza reshuffle aunque haya cartas.
  Llamarlo con 2N+1 ≥ 52 (≥6 jugadores) implica reshuffle cada mano.
- **Variable `Z(I)` no declarada**: se usa para apuestas/seguros sin
  `DIM`; los intérpretes Microsoft de la época toleraban índices hasta
  10 sin declarar, por lo que con 1-7 jugadores funciona, pero es
  apoyado en el comportamiento por defecto de la implementación.
- **`X1=10 MIN X` comentado pero implementado como `IF X1>10 THEN X1=10`**:
  el autor sabía que el operador `MIN` no era estándar.

## Grafo de flujo (ASCII)

```
                              +-----------+
                              | start 1500|
                              +-----+-----+
                                    |
                                    v
                         init deck D(1..52), C=53
                         opt. instructions
                                    |
                                    v
                              N players input
                                    |
        +---------------------------+----------------------------+
        |                                                        |
        v                                                        |
  reset hands, ask bets                                          |
        |                                                        |
        v                                                        |
  deal two rounds (GOSUB 100)                                    |
        |                                                        |
        v                                                        |
  insurance check (P(D1,1)==Ace)                                 |
        |                                                        |
        v                                                        |
  dealer blackjack? -- yes --> 3140 settle ------+               |
        |                                                        |
        no                                                       |
        |                                                        |
        v                                                        |
  for each player I (2360-2900):                                 |
     ON H GOTO Stand(2410) | Hit(2550) | Double(2510) | Split    |
       Stand: GOSUB 300 eval; check 21 -> Blackjack 1.5x         |
       Hit:   loop in 950 until stand or bust                    |
       Double: deal 1, double bet                                |
       Split: clone hand to I+D1, play 800 each                  |
        |                                                        |
        v                                                        |
  any player still alive? else announce dealer hole card -> 3140 |
        |                                                        |
        v                                                        |
  3010: dealer plays, hits while total < 17                      |
        |                                                        |
        v                                                        |
  3140: settle bets, print player/dealer running totals          |
        |                                                        |
        +----------> 1810 (next deal)                            |
                                                                 |
                              +----------------------------------+
                              | end of program (no normal exit)  |
                              +----------------------------------+
```

El programa no termina jamás de forma natural: bucle infinito entre
manos. La salida es vía Ctrl-C / `BREAK`. **[BUG]** No hay "cash out".

## Inventario de variables

| Var | Tipo | Uso |
| --- | --- | --- |
| `P(15,12)` | int | mano `I`, carta `J` (1=Ace,…,13=K). 15 manos por las hasta 14 plazas (7 jugadores+banca, hueco para splits) |
| `Q(15)` | int | total codificado de la mano `I` (ver más abajo) |
| `R(15)` | int | nº de cartas en la mano `I` |
| `C(52)` | int | mazo barajado, cartas pendientes (1=Ace,…,13=K, 4 de cada) |
| `D(52)` | int | descarte |
| `T(8)` | float | total acumulado por jugador (1..N) y banca (`D1=N+1`) |
| `S(7)` | float | resultado neto de la mano actual por jugador (seguro+win/loss) |
| `B(15)` | int | apuesta actual en la mano `I` |
| `Z(I)` | float | apuesta/seguro temporal leído del teclado (sin DIM) |
| `C` | int | índice de la carta superior del mazo (1..52, decrementa al repartir) |
| `D` | int | tamaño del descarte |
| `X` | int | carta extraída en la última llamada a `GOSUB 100` |
| `Q` | int | total parcial usado por las rutinas de suma |
| `D$` | str | tabla literal de glifos de carta (`"N A  2  3 …  K"`) |
| `I$` | str | tabla de respuestas legales `"H,S,D,/,"` |
| `H, H1, H$` | varios | parser de respuesta (H1=tamaño de tabla, H=índice elegido) |
| `AA, AB, AC` | float | display-decoding de totales para imprimir |
| `D1` | int | número de plazas (`= N+1`, banca al final) |
| `I, I1` | int | índices de mano (`I1=I+D1` para la mitad split) |
| `L1, L2` | int | flags / valores temporales (usado en blackjack-check y split) |

## Inventario de subrutinas

| Línea inicio | Propósito |
| --- | --- |
| 100-250 | **Repartir una carta**: re-baraja si `C<51`, devuelve en `X`. |
| 300-420 | **Evaluar mano `I`**: recalcula `Q(I)` desde `P(I,*)` y `R(I)`. |
| 500-620 | **Sumar carta `X` al total `Q`**: codificación dura/blanda. |
| 700-740 | **Imprimir carta `X`**: usa 3 chars (incluye separador `N`). |
| 750-780 | **Imprimir carta `X` (alt)**: 2 chars sin separador. |
| 800-940 | **Jugar el resto de una mano** (post-split): hit/stand. |
| 1100-1190 | **Añadir carta al final** de la mano `I`, evalúa busted. |
| 1200-1260 | **Descartar la mano `I`** al `D` pile. |
| 1300-1330 | **Imprimir total** de la mano `I`. |
| 1400-1490 | **Leer respuesta**: parser contra `I$` con `H1` opciones. |
| 1500+ | **Programa principal**. |
| 3400-3420 | Funciones idénticas para decodificar `Q`→display (`AA, AB, AC`). |

## IO y dispositivos

- **Entrada**: `INPUT` síncrono desde teclado vía teletipo.
- **Salida**: `PRINT` con `TAB(n)` para títulos y `;` para concatenar
  sin newline. Sin gráficos, sin colores, sin sonido.
- **Aleatoriedad**: `RND(1)` — pseudoaleatorio dependiente del
  intérprete; ningún `RANDOMIZE` previo, así que la baraja inicial es
  determinista entre arranques de algunos intérpretes.

## Algoritmos identificados

### Codificación de la mano

La constante `FNA(Q) = Q + 11*(Q>=22)` decodifica el almacén interno a
total mostrado. Aprovechando que en BASIC `(expr_booleana)` evalúa a
`-1` cuando es verdadera, los rangos significan:

| Rango `Q` | Significado | Decodificación |
| --- | --- | --- |
| 2..10 | hard 2..10 | igual |
| 11..21 | soft 11..21 (con As contado como 11) | igual |
| 22..32 | hard 11..21 (As ya degradado a 1, o sin As) | `Q-11` |
| ≥ 33 | bust | bandera |

La suma (línea 500) actualiza `Q` así:

- Si `Q < 11` y `X = 1` (As): `Q := Q + 11` (soft 11 fresco).
- Si `Q < 11` y `X > 1`: `Q := Q1 + 11` cuando `Q1 ≥ 11`, si no `Q := Q1`.
- Si `Q ≥ 11` (soft o hard 11..21): si la suma se pasa de 21, ajusta
  As de 11 a 1; si bust definitivo, marca `Q := -1` (luego 3100 lo
  convierte en `Q := Q-(Q<0)/2` para reaprovecharlo como "casi 17.5"
  en el cálculo del settle... más bien: si `Q<0`, se queda como -1 y
  el `SGN` lo trata como pérdida).

### Reshuffle Fisher-Yates parcial

Líneas 170-220: se aplica F-Y sólo al rango `[C, 52]` (las cartas no
repartidas + el descarte recién copiado). Es F-Y correcto, pero el bug
de `GOSUB 120` salta la guarda y lo dispara cuando no toca.

### Dealer policy

`AA > 16` planta. Como `AA` ya incluye soft (16 con As cuenta como 11
si cabe), **planta en soft 17**. Es la regla "S17" clásica, la más
común de la época.

### Pago de blackjack natural

`S(I) := S(I) + 1.5 * B(I)` y `B(I) := 0` (línea 2440-2470): solo se
acepta si el jugador respondió `S` antes de pedir otra carta. Si el
jugador respondió `H`/`D`/`/` con 21 natural, pierde el bonus.
**[LICENCIA CREATIVA]** lo conservaremos como "tradición Ahl" pero
detectaremos blackjack automáticamente.

## Bugs y rarezas

| Línea | Anomalía | Decisión |
| --- | --- | --- |
| 1810 | `GOSUB 120` (debería ser 100): salta la condición y fuerza reshuffle |  **Corregido**: la versión moderna reshufflea según política explícita (deck < 1/4) |
| 3100 | `Q := Q - (Q<0)/2` no tiene efecto útil con int (siempre `(Q<0)/2 = 0` o `-0.5` → trunca) | Eliminado de la versión moderna |
| 1830 | `Z(I) = 0` sin DIM | En Python usamos listas tipadas |
| 1520 | `D$` empieza por `"N"` (separador inventado) y `"7N 8"` introduce otra `N` | Sustituimos por glifos Unicode y *suits* simbólicos |
| 1830-1870 | re-inicializan a 1..15 todos los arrays cada mano, incluso fuera de rango activo | En Python sólo manos activas |
| 2120-2230 | Si el seguro está abierto, no se cobra el seguro si la banca acaba con blackjack natural sin contar el insurance bet correctamente cuando el jugador no apuesta (S(I) puede quedar como `0*…` y entrar en el SGN sin problema) | Ok, conservado |
| n/a | No existe "abandono / cash-out". Se sale con BREAK | En la versión moderna hay tecla `Q` para salir |
| 2452-2480 | El blackjack se paga después de descartar la mano del jugador, lo que impide que el dealer use el resultado como referencia | Conservado: misma semántica al liquidar |

## Bugs corregidos en la versión moderna

1. **Reshuffle prematuro forzado por `GOSUB 120`**: se sustituye por una
   regla determinista "rebarajar cuando `cartas_restantes < umbral`".
2. **Sin salida limpia**: la versión 2026 expone una tecla / botón
   para abandonar la sesión guardando el balance.
3. **Blackjack solo al *Stand***: la versión 2026 detecta blackjack
   natural automáticamente tras el reparto inicial; el jugador no tiene
   que recordar pulsar `S` para cobrar 3:2.
4. **Splitting limitado a un nivel**: el original sólo permite un split
   (y duplica el array `P` con `I+D1`); conservamos esta limitación
   por fidelidad y porque la TUI v1.0 está pensada para un único
   jugador (multi-split queda en `TODO.md` para v1.1).

## Decisiones de portabilidad

- **Multi-jugador**: el original soporta 1..7. La versión 2026 v1.0
  soporta **1 jugador** en la TUI por foco de diseño; el dominio sí
  soporta `N` jugadores y el `--demo` también es 1 jugador. Multi en
  TUI queda en `TODO.md`.
- **`D$` con glifos `N` y formato 3 chars** → glifos `♠ ♥ ♦ ♣` Unicode
  y nombres `A 2 3 … T J Q K` con `T` para diez.
- **`RND(1)` global** → `random.Random` inyectado con `seed`
  reproducible (modo `--seed`).
- **Apuestas 1..500** → conservadas; añadimos bankroll inicial 1000.
- **Sin instrucciones interactivas** → reemplazadas por una pantalla
  de ayuda accesible con `?`.
