# Procedencia del código original

## `basic/blackjack.bas`

- **Juego**: Black Jack (a.k.a. "21")
- **Fuente exacta**:
  <https://github.com/coding-horror/basic-computer-games/blob/main/10_Blackjack/blackjack.bas>
  (commit `main` HEAD a fecha de descarga 2026-05-12).
- **Origen primario**: David H. Ahl, *BASIC Computer Games* (Creative
  Computing Press, Morristown, NJ, 1978), entrada n.º 10 "Black Jack".
  Cabecera del listado: `BLACK JACK / CREATIVE COMPUTING  MORRISTOWN,
  NEW JERSEY`.
- **Autor**: atribuido a la redacción de *Creative Computing*; las
  versiones de Ahl recopilan listados publicados antes en la revista
  homónima.
- **Dialecto**: BASIC genérico de los años 70 (compatible con DEC/HP/IBM
  time-sharing y luego GW-BASIC / Microsoft BASIC). Usa `DEF FN`,
  `GOSUB`/`RETURN`, `ON … GOTO`, `MID$`, `INT(RND(1)*…)`, números de
  línea, sin tipos.
- **Año**: listado publicado entre 1973 y 1978; el libro recopilatorio
  es de 1978.
- **Licencia / estatus**: el repositorio `coding-horror/basic-computer-games`
  redistribuye los listados de Ahl, cuyos términos originales eran
  permisivos ("free to copy as long as not for profit") y que se
  consideran de facto dominio público / abandonware educativo. El
  proyecto que los aloja se publica bajo licencia Unlicense.
- **Selección**: el usuario solicitó explícitamente este juego, por lo
  que no se ha sustituido por un equivalente. Procede directamente al
  análisis arqueológico (Fase 0+1).

## Plataforma canónica para el análisis

Aunque el dialecto es portable, lo trataremos como **GW-BASIC / Microsoft
BASIC en IBM PC con consola monocromo 80×25**, que es el entorno más
fidedigno al ecosistema que popularizó *BASIC Computer Games*. No
existen versiones documentadas para ZX Spectrum, Amstrad CPC o C64 de
este listado concreto, así que el listado de Ahl es la versión canónica.
