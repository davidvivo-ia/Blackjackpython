# Postmortem

Ahl publicó *Black Jack* en 1978 con 321 líneas de BASIC y cero
ceremonias: un bucle infinito, cinco arrays globales y unas
codificaciones numéricas tan apretadas que el comentario explicativo
ocupaba más bytes que el código que comentaban. Esta versión 2026
ocupa **menos volumen de implementación lógica** del que parece a
primera vista — la mayoría del repositorio son tests, documentación
y un sistema de diseño — pero introduce capas, tipos estrictos,
inmutabilidad y un TUI Textual con paleta phosphor green.

**Qué se ganó.** Reproducibilidad bit a bit con `--seed`, separación
limpia entre dominio puro y presentación, settlement explícito por
mano con casos discretos (`WIN/LOSS/PUSH/BUST/BLACKJACK/SURRENDER`),
persistencia XDG, accesibilidad teclado-first y un *demo headless*
que sirve a la vez como tutorial y como test E2E. La inferencia de
tipos estricta atrapa más bugs en la pantalla que cualquier listado
de revista de 1978 habría tolerado.

**Qué se perdió.** La **densidad poética** del original: 8 KiB de
BASIC en los que cada `GOSUB` reutiliza tres variables globales con
significados distintos según el contexto. La codificación
`Q+11*(Q>=22)` para representar soft/hard 11..21 es una pequeña
maravilla de aritmética bit-twiddling; aquí se sustituye por una
función pura de tres líneas que cualquier *type checker* entiende.
Lo que se gana en mantenibilidad se paga en *show-off*: el código
moderno es más amable, pero también menos sorprendente.

**Qué dice este ejercicio sobre el oficio en 40 años.** En 1978 el
constraint era la memoria; cada subrutina existía para no copiar
ocho líneas de `PRINT`. En 2026 el constraint es la cognición humana
sobre código que tiene que sobrevivir a múltiples colaboradores y
varios años; cada capa existe para no acoplar lógica de juego con IO
ni con la representación visual. Las herramientas
(`ruff`, `mypy`, `pytest`, `uv`, `textual`) son el equivalente
moderno de lo que el intérprete BASIC hacía por defecto (un único
proceso, un único contexto), excepto que ahora los garantes están
explícitos y son verificables. El espíritu — sentarse, programar el
21 y jugar partida tras partida hasta que el bankroll se acabe — es
exactamente el mismo. Solo que ahora también pasa los tests.
