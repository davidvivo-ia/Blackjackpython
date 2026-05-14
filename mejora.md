# mejora.md — Plan de mejora "máximo" para blackjack21

> Plan honesto, priorizado por **impacto / esfuerzo**. No incluye
> features que ya estén en `TODO.md` sin aportar nada nuevo; sí
> incluye trabajo que no estaba contemplado y que mueve este juego
> de "buen port" a "el mejor blackjack de terminal que existe".

## 1. Diagnóstico actual

Auditoría rápida (mayo 2026, post `0f33219`):

| Capa | Estado | Hueco |
|---|---|---|
| `domain/` | sólido, inmutable, 131 tests | falta `Action.SURRENDER` (el `Outcome` ya existe), multi-deck, resplit configurable |
| `application/` | use_cases + events + strategy | falta `analytics` (stats acumuladas) y `counter` (Hi-Lo) |
| `infrastructure/` | persistence + rng + paths | sin perfiles, sin migraciones, sin log estructurado real |
| `presentation/` | TUI Premiere + CLI Typer + demo | sin panel de stats, sin historial, sin ajustes en vivo, sin animaciones |
| **CI** | Actions con ruff + mypy + pytest matrix | sin badge, sin coverage upload, sin release workflow |
| **Distribución** | `uv sync` + doble clic `blackjack.py` | sin wheel publicado, sin binario standalone |
| **Pedagogía** | HINT lee la tabla de basic strategy | sin explicación, sin contador, sin drill |

Lo que **funciona muy bien** y no tocaremos: arquitectura hexagonal,
inmutabilidad, theming, seed determinista, bootstrap en Windows,
`render.py` con cartas paper-white.

## 2. Objetivos del plan

1. **Reglas casino reales** configurables (multi-deck, H17/S17, surrender, resplit, DAS).
2. **Experiencia de mesa** completa (stats en vivo, historial, animaciones, settings).
3. **Pedagogía única**: contador Hi-Lo opcional + HINT con EV + modo drill.
4. **Progresión**: perfiles, achievements locales, hall of fame (como la mock de Stitch).
5. **Distribución profesional**: PyPI + binario + asciinema.
6. **Robustez de release**: property tests, fuzz persistence, coverage ≥ 90%.

Cada fase es independiente y se puede mergear sola. Empuja una rama y
PR por fase para mantener el historial legible.

---

## 3. Fase A — Reglas casino completas (1–2 días)

**Objetivo:** que las reglas dejen de ser un único conjunto BASIC-original y se
puedan elegir como en un casino real.

### A.1 `Action.SURRENDER` cableado de extremo a extremo

- `domain/actions.py`: añadir `SURRENDER = "surrender"`.
- `domain/actions.legal_actions`: legal sólo en la **primera decisión**, gobernado por `rules.allow_surrender` (Late Surrender por defecto).
- `domain/state.py::apply_action`: rama nueva que marca `hand.surrendered=True` y avanza.
- `domain/outcomes.py::settle`: ya soporta `SURRENDER` (pago −½ de la apuesta) — solo confirmar.
- `presentation/tui.py`: binding `u` (Sur**rend**er), botón opcional, mensaje "SURRENDER -½".
- `application/strategy.py`: incorporar reglas de basic strategy para LS (hard 16 vs 9/10/A, hard 15 vs 10).
- **Test:** 6 escenarios pinchando cada cell del chart de surrender + 1 e2e Pilot.

### A.2 Multi-deck shoe (1 / 2 / 4 / 6 / 8 barajas)

- `domain/deck.py`: `Deck.fresh(shuffler, num_decks: int = 1)` repite `standard_deck()` `num_decks` veces.
- `RESHUFFLE_THRESHOLD` se sustituye por **penetración** (`rules.shoe_penetration: float = 0.75`): se reshufflea al `(1−p)·total`.
- `cli.py`: `--decks 6` en `play`.
- **Impacto:** cambia probabilidades y estrategia (basic strategy varía ligerísimamente por nº de barajas). Documentar en README.
- **Test:** property — un shoe de N barajas tiene `N×52` cartas exactas, cada palo×rango aparece `N` veces.

### A.3 Reglas configurables vía CLI y settings

Exponer en `GameRules` y `cli.py play`:

| Flag | Default | Variantes |
|---|---|---|
| `--decks INT` | 1 | 1, 2, 4, 6, 8 |
| `--h17` / `--s17` | s17 | dealer hits soft 17 sí/no |
| `--surrender` | true | LS sí/no |
| `--das` | true | Double after split |
| `--resplit-max INT` | 1 | 1, 2, 3, 4 (split máximo) |
| `--min-bet INT` | 1 | |
| `--max-bet INT` | 500 | |
| `--bankroll INT` | 1000 | bankroll inicial al crear sesión |

Persistir en `~/.local/share/blackjack21/rules.json` (separado de `session.json`).

### A.4 Resplit

- `hand.from_split` ya existe. Sustituir el booleano por contador `split_count: int = 0`.
- `legal_actions`: permitir SPLIT mientras `split_count < rules.resplit_max`.
- **Caveat:** Aces splited reciben **una carta** y stand obligatorio (regla universal). Ya está.

**Salida de fase A:** archivo `tests/integration/test_rules_variants.py` con un grid 2×2×2 de combinaciones que ejercita una mano completa por configuración.

---

## 4. Fase B — Experiencia de mesa (2–3 días)

### B.1 Panel de estadísticas en vivo

`application/analytics.py` (nuevo): agregador inmutable que consume
`GameEvent` y mantiene:

```python
@dataclass(frozen=True, slots=True)
class SessionAnalytics:
    hands_played: int
    blackjacks: int
    wins: int
    losses: int
    pushes: int
    busts: int
    current_streak: int          # + ganadora, − perdedora
    longest_win_streak: int
    longest_loss_streak: int
    biggest_pot: int
    total_wagered: int
    net_profit: int

    @property
    def win_rate(self) -> float: ...
    @property
    def expected_value_pct(self) -> float: ...  # net_profit / total_wagered
```

- `SessionStats` actual (`hands_played / blackjacks / biggest_pot`) se renombra a `SessionAnalytics` y se amplía.
- Migración del JSON con `version: 2` en el wrapper. Si encuentra `version: 1`, lee los 3 campos viejos y rellena el resto a cero.
- **TUI:** panel lateral colapsable con tabla `rich.table.Table` actualizada en cada `_refresh()`.
- **Test:** dispara 50 manos seed=42 vía `--demo` y verifica las cifras.

### B.2 Historial de manos

`Vertical` colapsable a la derecha (`#history-panel`) con `ListView` de
las últimas 10 manos: `─ #34  bet $25  T♠+K♥ vs J♦+9♣  +$25 (WIN)`.
Persistir las últimas 50 entradas en `session.json`.

### B.3 Animaciones reales

`textual.timer` ya está disponible:

- Reparto inicial: dealer / jugador / dealer / jugador con 200ms entre cartas.
- HIT: la nueva carta aparece con `fade-in` (Textual soporta CSS `transition`).
- DEALER_TURN: revelar la hole card con un fade, luego cartas con 250ms gap.
- Outcome: banner central grande con drop-shadow (Rich `Panel` con `box.HEAVY` + texto centrado).

Implementar como **modo opcional** (`--anim none|fast|normal`). Default `fast`. Tests no-anim para CI.

### B.4 Settings screen

Pantalla nueva accesible por `,` (coma):

- Toggle ASCII / Unicode glyphs.
- Toggle H17 / S17 (solo aplica a nueva sesión).
- Toggle animaciones.
- Toggle counter overlay (fase C).
- "Reset session" con confirmación.

Textual `ModalScreen`. **Importante:** los cambios de reglas que afectan al
RNG/estado sólo se aplican a la próxima sesión, no a la actual.

### B.5 Outcome banner pulido

Sustituir `[bold accent]WIN[/] - press N` por un `Panel` centrado con
`box.DOUBLE_EDGE`, anchura 24, fondo translúcido, texto a 20+ caracteres.
Para `BLACKJACK` añadir un *outline* en oro (Rich `Style(color="accent", bold=True, frame=True)`).

---

## 5. Fase C — Pedagogía (2–3 días) ★ valor diferencial

Esto es lo que **ningún otro blackjack de terminal tiene** y es donde
podemos plantar bandera. La diferencia entre un buen port y la
referencia del nicho.

### C.1 HINT con explicación EV

Hoy `T` dice `TIP: basic strategy says DOUBLE`. Subimos a:

```
TIP: DOUBLE
  Hard 11 vs dealer 6 → EV +0.667 (best move).
  HIT alt EV: +0.232.  STAND alt EV: −0.292.
```

EVs precomputadas en tabla estática (no calculamos en runtime). Tabla
en `application/strategy_ev.py` con valores publicados (Wong / Schlesinger
para single deck S17 DAS). Sólo mostrar la línea "alt" si tu acción
elegida diverge de la óptima.

### C.2 Contador Hi-Lo opcional

`application/counter.py`:

```python
@dataclass(frozen=True, slots=True)
class CountState:
    running_count: int
    decks_remaining: float
    @property
    def true_count(self) -> float:
        return self.running_count / max(0.5, self.decks_remaining)
```

- Cada `CardDealt` event suma `+1` (2–6), `0` (7–9), `−1` (10–A).
- `decks_remaining = deck.remaining / 52`.

**UI overlay** (toggle desde Settings, `K` desde la mesa):

```
COUNT  RC +6  TC +2.4   BET RAMP: 4u
```

`BET RAMP` calculado con tabla 1-2-4-8-12 unidades según TC.

**Caveat ético:** documentar en README que esto **no funciona** contra
casas reales con CSM (continuous shuffle machine) ni con barajas que
se reshufflean cada mano (que es nuestro caso por defecto). Es modo
pedagógico — exige `--decks 6 --penetration 0.75` para que sirva.

### C.3 Modo "drill"

`uv run blackjack21 drill --topic hard-totals`:

- Generador determinista que te lanza N situaciones aleatorias del
  topic elegido (hard-totals, soft-totals, pairs, surrender).
- Tú respondes con `H/S/D/P/U`.
- Te puntúa contra basic strategy. Al final: % acierto y matriz de
  errores ("fallas hard 16 vs 10 el 40% de las veces").

Es **el modo killer** para enseñar el juego. Se vende a sí mismo en
el README con un asciinema.

### C.4 Probabilidades en pantalla

Toggle en Settings: muestra al lado del HAND VALUE actual:

```
HAND VALUE  16 (hard)
P(bust on HIT) = 61.5%
```

Cálculo: tras quitar las cartas vistas, contar las que harían que el
total > 21. Es exacto, no aproximación, porque el deck es finito y
conocido (no estamos contando, solo contamos las cartas que ya
salieron en la mesa).

---

## 6. Fase D — Progresión y meta (1–2 días)

### D.1 Perfiles

`infrastructure/profiles.py`: `~/.local/share/blackjack21/profiles/<name>.json`.
`blackjack21 play --profile alice`. Por defecto, perfil `default`.

### D.2 Achievements

`application/achievements.py` con un set fijo:

| ID | Nombre | Condición |
|---|---|---|
| `first_bj` | First Blackjack | 1 BJ natural |
| `streak_5` | Hot Hand | 5 victorias seguidas |
| `bankrupt_recovered` | Phoenix | bajar de $50 y volver a $1000 |
| `card_counter` | Card Counter | jugar 100 manos con counter on |
| `purist` | Purist | terminar una sesión sin ningún error de basic strategy |
| `whale` | Whale | apostar el máximo 10 veces |
| `marathon` | Marathon | jugar 100 manos |

Pop-up toast al desbloquear. Vista de logros desde Settings.

### D.3 Hall of fame local

`infrastructure/leaderboard.py`: tabla con `top biggest pot`, `top bankroll`,
`top win streak` por perfil. Vista `blackjack21 scores`.

No multiplayer / no red. Solo local. Match con la pantalla `clasificación` del mock.

---

## 7. Fase E — Distribución (1 día)

### E.1 Release a PyPI

- `.github/workflows/release.yml`: trigger en `v*` tag, build `uv build`,
  publish con `pypi-publish` action y trusted publishing (sin tokens).
- Verificar que el paquete `pip install blackjack21` funciona en venv limpio.

### E.2 Binario standalone

- `pyinstaller --onefile --name blackjack21 blackjack.py` por OS (3 jobs en CI).
- Artefactos al release de GitHub: `blackjack21-linux`, `blackjack21-macos`, `blackjack21-windows.exe`.
- README: sección "Instalación sin Python".

### E.3 README pro

- Banner con asciinema (`agg blackjack.cast --output blackjack.gif`).
- Badges: PyPI, CI, coverage, license.
- Sección "Why this exists" con la cita de Ahl.
- GIFs cortos por cada modo (play / demo / drill / counter).
- Tabla comparativa con otros blackjack-en-terminal del mercado (`pyblackjack`, `bjsim`, etc.) destacando lo nuestro.

---

## 8. Fase F — Robustez (1 día)

### F.1 Property tests para strategy

Hypothesis genera `(hand, upcard)` aleatorios y verifica:
- `recommend(state) ∈ state.legal_actions()` (cae bien).
- Recomendación es estable bajo permutación de cartas (no depende del orden).
- `surrender` solo aparece cuando es legal.

### F.2 Mutation testing

`mutmut run --paths-to-mutate src/blackjack21/domain src/blackjack21/application`.
Threshold: ≥ 85% mutantes capturados. Añadir a CI nightly (no por PR — tarda).

### F.3 Fuzz de persistence

Inyectar JSON corruptos, truncos, con tipos incorrectos. Aserción:
nunca crashea, siempre retorna `None` o un `SavedSession` válido.

### F.4 Coverage ≥ 90%

Subir el threshold de `--cov-fail-under=80` a `90`.

---

## 9. Lo que NO haremos (para no sobre-ingeniar)

- **Multi-jugador en una sola TUI**. El dominio lo soporta pero la coreografía visual de 4 jugadores en terminal es horror. Si alguien lo quiere de verdad, abre la puerta a un modo "host + web".
- **Sonido**. La promesa de v1.2 en `TODO.md`. En terminal el `\a` (BEL) es feo y depende de la config del usuario. Si lo hacemos, opt-in y solo en ganar/perder grande, nunca cada deal.
- **Inteligencia artificial real (red neuronal, MCTS)**. Basic strategy es **matemáticamente óptima** para este juego sin counting; añadir una red sería peor y más caro. La pedagogía vale más.
- **Web app**. Ya descartado en la conversación. La TUI es el target.
- **Casino mode (apuestas con dinero real)**. Nunca. Aquí dejamos clavada la línea.
- **Networking / multiplayer online**. Out of scope. Re-evaluable como spin-off "blackjack21-server".

---

## 10. Criterios de "máximo" (DoD del plan completo)

Al cerrar las 6 fases:

- [ ] Pasa `ruff + mypy --strict + pytest --cov-fail-under=90` en 3 versiones de Python.
- [ ] Reglas configurables cubren las 7 variantes principales (multi-deck, H17, surrender, DAS, resplit, BJ pay 3:2 / 6:5, min/max bet).
- [ ] Modo `drill` lanzable en 1 comando, con métricas al final.
- [ ] Counter Hi-Lo on/off, RC + TC en tiempo real.
- [ ] 7 achievements implementados.
- [ ] Hall of fame local funciona, perfil multi.
- [ ] `pip install blackjack21` funciona, binario standalone disponible en releases.
- [ ] README incluye asciinema de cada modo.
- [ ] Mutation testing pasa al 85%.

---

## 11. Estimación y orden recomendado

| Fase | Esfuerzo | Riesgo | Empezar tras |
|---|---|---|---|
| A — Reglas | 1–2d | bajo | hoy |
| B — UX | 2–3d | medio (animaciones en CI) | A |
| C — Pedagogía | 2–3d | bajo | A (B en paralelo) |
| D — Progresión | 1–2d | bajo | B |
| E — Distribución | 1d | bajo (config CI) | en cualquier momento tras A |
| F — Robustez | 1d | bajo | F al final |

Total: **8–12 días de trabajo enfocado**, en 6 PRs independientes.

## 12. Próximo paso concreto

Si dices "adelante", arranco por **Fase A.1 (SURRENDER)** porque:
- está medio cableado (Outcome existe);
- desbloquea inmediatamente la entrada de strategy con surrender;
- da una victoria visible en 2 horas, con tests al cierre.

A partir de ahí, vamos fase a fase, PR a PR.
