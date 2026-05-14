# Changelog

Todos los cambios relevantes se documentan en este archivo. Sigue
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
[Semantic Versioning](https://semver.org/lang/es/).

## [1.1.0] — 2026-05-14

Sprint "Premiere Blackjack". Reglas casino reales, repaletización a
casino-green + oro, modo entrenamiento de basic strategy, perfiles +
achievements, y un puñado de mejoras de robustez.

### Reglas (Fase A)

- `Action.SURRENDER` cableada de extremo a extremo (dominio,
  estrategia, TUI con tecla `U`, settlement -½ apuesta).
- Multi-deck shoe 1/2/4/6/8 (`--decks N`) con 75% de penetración en
  multi-deck; baraja simple conserva el threshold 15 del original.
- `--h17 / --s17`, `--no-surrender` configurables desde CLI.
- Basic strategy ampliada con surrenders textbook (hard 16 vs 9/10/A,
  hard 15 vs 10) y fallback a HIT cuando la regla está deshabilitada.

### Experiencia de mesa (Fase B)

- Cabecera `♠ ♥ PREMIERE BLACKJACK ♦ ♣`.
- Stats row de 3 celdas: BALANCE / CURRENT BET (con stack visual de
  fichas `●●●` por denominación) / HAND VALUE (con `bust on hit XX%`
  durante el turno del jugador).
- Counter row en vivo: W / L / P / BJ / STREAK con 🔥 al ≥ +5 y ❄ al
  ≤ -5.
- Section titles `── ♠ DEALER ♥ ──` y `── ♦ YOU ♣ ──` con Rule oro.
- Banner de outcome de 10 filas con sparkle decorativo encima/debajo:
  `★ ✦ ★` para WIN/BJ (oro, doble-edge box para BJ),
  `✗ X ✗` para LOSS/BUST (rojo),
  `= ─ =` para PUSH (ámbar),
  `↩ · ↩` para SURRENDER.
- Insurance ahora es un Panel ámbar centrado con título y atajos en
  vez de un input de texto.
- Modal de historial (`,`): tabla con las últimas 50 manos.
- Modal de info de sesión (`.`): reglas, glifos, win-rate, etc.

### Cartas (Fase G visual)

- Cartas crecen a 11×9 con esquinas duplicadas (rank/suit arriba-izda
  + invertido abajo-dcha) y borde redondeado oro.
- Pip patterns clásicos para 2-9 (1, 2, 3, 4, 5, 6, 7, 8, 9 palos
  visibles según el rank); el 10 comparte la rejilla 3×3 del 9 y se
  distingue por el rótulo "10" en esquina (igual que cartas Bicycle
  cuando el espacio es muy compacto).
- J / Q / K muestran `♞ J ♞` / `♛ Q ♛` / `♚ K ♚` en el centro.
- As con explosión 5-pip (cruz centrada).
- Sombra `▔` bajo cada carta (oro mate) para sugerir profundidad.
- Reverso felt-verde con patrón `◆ ✦ ◆`.

### Botones (Fase G2)

- Fila de acciones HIT / STAND / DOUBLE / SPLIT / SURRENDER durante
  PLAYER_TURN, con grey-out por legalidad. Click = misma acción que
  la tecla.
- Insurance YES / NO THANKS durante AWAITING_INSURANCE.
- Fichas $5 / $25 / $100 / $500 con disco ● y borde de color por
  denominación.

### Pedagogía (Fase C)

- Tecla `T` (tip): `recommend` + `explain` con razonamiento legible
  (`hard 16 vs dealer 6 → STAND`).
- `bust on hit X%` en el HAND VALUE del jugador, exacto contra las
  cartas que quedan en el shoe.
- `--counter`: overlay Hi-Lo con running count, true count (oro/rojo
  por signo) y decks restantes. Pedagógico, nunca alimenta a la
  estrategia.
- Subcomando nuevo `blackjack21 drill --topic [hard|soft|pairs|
  surrender|all] --rounds N --seed N`: quizz interactivo de basic
  strategy con score y tabla de errores al final.

### Progresión (Fase D)

- `--profile NAME` separa bankroll/stats/logros por perfil; el
  perfil `default` mantiene el path legacy `session.json`.
- Subcomando `blackjack21 scores --profile NAME`: hall of fame con
  bankroll, biggest pot, longest streak, max/lowest bankroll, times
  bet max y los 7 logros con ★ por desbloqueado.
- 7 logros locales: First Blackjack, Hot Hand (5W streak),
  Phoenix (caer < $200 y volver a $1k), Whale (10 max bets),
  Marathon (100 manos), Big Pot (≥$500 net), High Roller (≥$5k).
- `SessionStats` y `SavedSession` extendidos con
  `longest_win_streak`, `max_bankroll_reached`, `lowest_bankroll`,
  `times_bet_max`, `unlocked_achievements`. `extra="ignore"` en
  Pydantic ⇒ los JSON de v1.0 cargan sin tocar.

### Temas (Fase G4)

- Cuatro paletas seleccionables con `--theme`:
  `premiere` (default, casino-green + oro),
  `phosphor` (CRT verde, homenaje v1.0),
  `midnight` (navy + plata),
  `ruby` (rojo + oro).
- TCSS rebuilt por instancia inyectando un bloque `$var: #HEX;` en
  cabecera; la misma hoja sirve para los cuatro temas.

### Robustez (Fase F)

- Property tests para `recommend` con Hypothesis (siempre legal,
  estable bajo permutación, surrender solo cuando la regla lo
  permite).
- Fuzz test de `JsonSessionStore.load()` ante bytes/textos
  arbitrarios; corregido un bug donde `UnicodeDecodeError` escapaba
  sin envolverse en `SessionCorruptError`.
- Coverage threshold 80 → 90 (al cierre: 91.24%).

### Distribución (Fase E parcial)

- README reescrito con todos los flags y atajos nuevos.
- `.github/workflows/release.yml`: PyPI Trusted Publisher en push de
  tag `v*`. Untested hasta el primer release real.

### No incluido en este sprint (decisión consciente)

- Animaciones de reparto/hit/reveal — riesgo de inestabilidad en
  Pilot, requieren toggle `--anim none` y coreografía de timers.
- Layout responsivo por ancho de terminal — proyecto en sí mismo.
- Binario standalone PyInstaller — frágil con Textual/Rich y no
  verificable sin runners por OS.
- EV numérico en HINT — necesita tabla estática grande para ROI bajo.
- Multi-jugador en TUI (1..7) — el dominio lo soporta pero la
  coreografía visual es harina de otro costal.

### Métricas

- 223 tests passing (179 al inicio del sprint).
- Coverage 91.24%.
- mypy --strict + ruff sin avisos.

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
