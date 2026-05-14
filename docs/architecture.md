# Arquitectura

`blackjack21` se estructura en cuatro capas concéntricas, con
dependencias dirigidas hacia el dominio:

```
+----------------------------------------------------------------+
|                       presentation/                            |
|     Textual TUI · CLI Typer · renderers de tabla y cartas      |
+----------------------------+-----------------------------------+
                             | depends on
                             v
+----------------------------------------------------------------+
|                       application/                             |
|  Casos de uso: PlayHand, PlaceBet, ResolveDealer, GameSession  |
+----------------------------+-----------------------------------+
                             | depends on
                             v
+----------------------------------------------------------------+
|                         domain/                                |
|     Card · Deck · Hand · Bet · Action · GameRules · Outcome    |
|     Inmutable, sin IO, sin random.random()                     |
+----------------------------+-----------------------------------+
                             ^
                             | injected via ports
                             |
+----------------------------+-----------------------------------+
|                    infrastructure/                             |
|   RandomShuffler (RNG inyectado) · JsonSessionStore (XDG)      |
+----------------------------------------------------------------+
```

## Reglas de dependencia

- `domain/` no importa **nada** de las demás capas y nada de IO.
- `application/` importa de `domain/` y define puertos (Protocols) que
  implementan `infrastructure/` y opcionalmente `presentation/`.
- `infrastructure/` puede importar de `domain/` y `application/`.
- `presentation/` orquesta `application/` e `infrastructure/`.

## Puntos de entrada

- `python -m blackjack21` → CLI Typer.
- `python -m blackjack21 play` → arranca la TUI.
- `python -m blackjack21 play --demo --seed 42` → corre la partida
  determinista (modo demo, sin entrada de usuario).
- `python -m blackjack21 doctor` → diagnostica entorno (terminal,
  colores, anchura).

## Flujo de una mano

```
GameSession.start()
   |
   v
PlaceBet(player, amount) -- valida 1 <= bet <= bankroll, <= 500
   |
   v
DealInitial(session) -- usa Deck.draw() inyectado de Shuffler
   |
   v
ResolveInsurance(session) -- si dealer up-card == Ace
   |
   v
PlayPlayerHand(session, action) -- bucle externo en presentation
   |          |
   |          +-- Action.HIT     -> Hand.add(card); detect bust
   |          +-- Action.STAND   -> end of player turn
   |          +-- Action.DOUBLE  -> 1 card + bet*=2 + stand
   |          +-- Action.SPLIT   -> bifurca a dos manos
   |
   v
ResolveDealer(session) -- planta en 17+ (S17)
   |
   v
SettleHand(session) -> Outcome por cada mano del jugador
   |
   v
session.bankroll += net; persist via SessionStore
```

## Modelo de datos del dominio (inmutable)

- `Rank` y `Suit`: `StrEnum`.
- `Card(rank, suit)`: `frozen=True, slots=True`.
- `Hand(cards: tuple[Card, ...], bet: int, doubled: bool, surrendered: bool, from_split: bool)` — inmutable: cualquier transición devuelve una nueva `Hand`.
- `HandValue(total: int, is_soft: bool, is_blackjack: bool, is_bust: bool)` — derivado puro de `Hand`.
- `Deck(cards: tuple[Card, ...], discard: tuple[Card, ...])` con
  `Deck.draw() -> tuple[Card, Deck]` (estilo functional).
- `GameRules`: dataclass `frozen=True` con constantes (`MIN_BET=1`,
  `MAX_BET=500`, `DEALER_STANDS_ON=17`, `BLACKJACK_PAYOUT=Fraction(3,2)`,
  `INITIAL_BANKROLL=1000`).
- `GameState`: snapshot completo (jugador, dealer, mazo, fase). Las
  transiciones devuelven `GameState` nuevo (event-sourcing ligero).

## Eventos de aplicación

`application/events.py` define `GameEvent` (union de dataclasses):
`BetPlaced`, `CardDealt`, `PlayerAction`, `DealerAction`, `HandResolved`,
`SessionEnded`. La TUI se suscribe a este flujo para animar/reproducir
la partida; el modo `--demo` los serializa en stdout para tests E2E.

## Inyección de dependencias

- `Shuffler` protocol con dos implementaciones: `SystemShuffler` (usa
  `random.Random` semillable) y `FrozenShuffler` (acepta una lista fija
  de cartas, usado en tests).
- `SessionStore` protocol con `JsonSessionStore` (XDG_DATA_HOME) y
  `InMemorySessionStore` (tests).
- `Clock` protocol para timestamps reproducibles.

## Manejo de errores

Jerarquía propia en `domain/errors.py`:

```
BlackjackError
├── InvalidBetError
├── InvalidActionError
├── DeckExhaustedError
└── SessionCorruptError
```

La presentación captura `BlackjackError` y muestra mensajes humanos;
cualquier otra excepción es bug y se propaga.

## Tests

- `tests/unit/`: dominio puro (Card, Hand, Deck, GameRules, settle).
- `tests/property/`: `hypothesis` sobre evaluación de manos
  (todo total se decodifica correctamente; reshuffle preserva
  multiset de cartas; pago de blackjack es ≥ pago normal).
- `tests/integration/`: casos de uso completos contra `FrozenShuffler`.
- `tests/e2e/`: ejecuta `--demo --seed 42` y compara contra un
  snapshot golden.
