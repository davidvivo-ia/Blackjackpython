# ADR 0003 — RNG inyectado y determinismo

## Contexto

El programa original usa `RND(1)` global sin `RANDOMIZE`, lo que hace
la primera baraja determinista en muchos intérpretes. Queremos:

- Reproducir partidas con `--seed N`.
- Tener un modo `--demo --seed 42` que ejecute siempre exactamente
  la misma secuencia para snapshot tests.
- Aislar el dominio de `random.random()` global.

## Opciones consideradas

1. **`random.shuffle()` global**. Simple, pero el comportamiento de
   `random.seed()` cambió entre versiones de Python y obliga a
   `monkeypatch` en tests.
2. **`numpy.random.Generator`**. Determinista entre versiones pero
   añade una dependencia pesada para algo trivial.
3. **`random.Random(seed)` inyectado como `Shuffler`**: estable,
   ligero, sin dependencias externas. Soporta `getstate/setstate` si
   queremos snapshot del azar.

## Decisión

**Definimos un `Shuffler` protocol y dos implementaciones**:

- `SystemShuffler(seed: int | None)`: usa `random.Random(seed)`.
- `FrozenShuffler(cards: Iterable[Card])`: ignora azar y devuelve
  cartas en orden fijo (para tests de propiedad y demo).

Toda la baraja consume `Shuffler.shuffled(cards)`, nunca
`random.shuffle`.

## Consecuencias

- Tests deterministas con `pytest` sin `monkeypatch`.
- `--demo --seed N` reproducible bit a bit entre máquinas con Python
  3.13+.
- El protocolo es de una sola función, suficiente y mínimo.
