# ADR 0005 — Persistencia: JSON en XDG_DATA_HOME

## Contexto

El original no persiste nada: cada arranque empieza con el bankroll a
cero. Para la versión 2026 queremos:

- Recordar el bankroll entre sesiones.
- Guardar estadísticas básicas (manos jugadas, blackjacks, mayor
  pozo).
- Permitir borrar el estado fácilmente.

## Opciones consideradas

1. **SQLite**: sobreingeniería para 1 KiB de datos.
2. **TOML**: bien para configuración, peor para colecciones.
3. **JSON en `~/.local/share/blackjack21/session.json` (XDG)**:
   ligero, legible, portable, fácil de borrar.

## Decisión

**JSON XDG**. La ruta resuelta es:

```
${XDG_DATA_HOME:-$HOME/.local/share}/blackjack21/session.json
```

con permisos `0600`. Esquema validado con `pydantic v2`. El comando
`blackjack21 reset` lo borra.

## Consecuencias

- Una dependencia mínima (`pydantic`).
- Compatible con Linux, macOS (respetando XDG si está definido) y
  Windows (usando `pathlib.Path.home() / "AppData" / "Local"`).
- Documentado en `README.md`.
