# ADR 0002 — Modelo de dominio inmutable

## Contexto

El original muta cinco arrays globales (`P, Q, R, B, S`) cada turno.
En Python 2026 buscamos:

- Lógica de juego trivialmente testeable sin mocks ni IO.
- Eventos reproducibles para `--demo --seed`.
- Inmutabilidad por defecto (`frozen=True, slots=True`).

## Opciones consideradas

1. **OOP clásica con `Hand.add()` mutador**. Sencillo pero mezcla
   estado y reglas, dificulta tests de propiedades.
2. **Modelo inmutable con transiciones puras**: cada `Hand.hit(card)`
   devuelve una nueva `Hand`; cada `GameState.apply(action)` devuelve
   nuevo `GameState`. Permite event-sourcing trivial y *time travel*
   en debug.
3. **Modelo basado en `pydantic`**: añade validación pero pena de
   rendimiento y `frozen=True` con validators frena demasiado.

## Decisión

**Modelo inmutable con `dataclass(frozen=True, slots=True)`** en
`domain/`. Usaremos `pydantic` v2 sólo en frontera de IO
(`infrastructure/persistence/`) para serializar `SavedSession`.

## Consecuencias

- Cada acción del jugador es una función pura `GameState -> GameState`.
- Necesitamos `tuple[...]` en lugar de `list[...]` para mantenerse
  hashable y comparable.
- La capa de presentación recibe eventos en lugar de tirar de `Hand`
  mutable; reduce acoplamiento.
- `mypy --strict` valida exhaustivamente: cualquier ramo no cubierto
  por `match` falla en tiempo de tipos.
