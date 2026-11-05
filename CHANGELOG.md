# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versiones: **parche** = correcciones de texto; **menor** = nodos nuevos o retirados;
**mayor** = cambio de marco normativo o del modelo de datos.

## [Sin publicar]

### Añadido
- Estructura inicial del repositorio, esquema JSON y flujos de validación y publicación.
- Base: exportación n.º 1 de ProIDEAC (sin la credencial que contenía; ver `fuentes/proideac/exportacion-1/LEEME.md`).
- Manifiesto con los 105 documentos oficiales enlazados desde las páginas de la Consejería.
- Documento de Matemáticas de ESO y su contraste con el corpus.
- Correcciones 0001 y 0002 (Matemáticas ESO).
- Documentos oficiales de Matemáticas, Valores Cívicos y Éticos (Primaria), Tecnología y Digitalización (ESO)
  y de diez materias de Bachillerato, y su contraste con el corpus.
- Correcciones 0003–0016: textos de saber y enunciados de competencia ausentes en la exportación,
  descriptor CE7 de Valores Cívicos (Primaria) y saberes perdidos o mal codificados en Matemáticas (Primaria),
  Filosofía y Bioestadística. Se crean 6 saberes y se retira `sb:BBIE02SBIII.1.2` (pasa a III.3.2).
- `contrastar` deduce las secciones de los documentos y propone correcciones (`--proponer`).
- Documentos oficiales de diez materias de ESO y de Educación Física de Primaria, y su contraste con el corpus.
- Correcciones 0017–0035: 196 explicaciones de bloque copiadas de otro curso, 22 textos de saber de otra
  materia (3.º ESO), título y descripción de los bloques de saberes de Lengua Castellana (ESO), un saber de
  Lengua Castellana de 3.º ESO y el enunciado de la competencia 2 de Segunda Lengua Extranjera.

- Documentos oficiales de Infantil y de los ámbitos de diversificación; correcciones 0036–0041 (explicaciones de bloque copiadas de otro curso en Infantil y ámbitos, y bloques de saberes del Ámbito Lingüístico y Social).
- Optativas de 1.º de Bachillerato creadas desde su documento oficial: Juegos y Deportes Tradicionales de Canarias (`BJUI`) y Música, Expresión y Espectáculos (`BMUW`) (correcciones 0042 y 0043, herramienta `materia_desde_odt`).
- Licencia de los datos (CC BY 4.0) y verificación de `config/descriptores.csv` contra los anexos 1.
- Correcciones 0044–0136: 771 textos de la versión publicada en el BOC, 175 de puntuación publicada, 104 de espacios, 36 explicaciones copiadas de otro curso, 22 títulos y descripciones de bloques de saberes y 4 textos ausentes. Texto de los cinco decretos en el BOC (`fuentes/boletines/`).
- Correcciones 0137–0210: textos cortados y de otro curso, descriptores y saberes numerados de forma distinta.
- Correcciones 0211–0233: las 127 diferencias que el BOC no permitía decidir se corrigen con el documento oficial, que es la referencia; se rehacen los bloques de saberes en los que faltaban o sobraban saberes. El contraste queda sin diferencias por explicar.
- Pruebas automáticas (`tests/`, pytest) del importador, el lector de ODT, el texto del BOC, el contraste y las correcciones, ejecutadas en la CI.
- `contrastar --estricto`: la CI falla si queda alguna diferencia sin explicar.
- Una corrección con `valor: null` quita el campo.
- Correcciones 0234–0254: 183 textos con la puntuación del documento oficial (el BOC no permitía decidirla).
- Correcciones 0255–0262: 24 diferencias entre el BOC y el ODT validadas una a una; prevalece el ODT (ver `docs/pendientes.md`). Se retiran 3 saberes que el ODT omite.
- `contrastar` comprueba con qué número imprime el BOC cada criterio e informa aparte de las erratas: 24 criterios 5.1 y 6.1 intercambiados en Segunda Lengua Extranjera (ESO), documentados en `docs/pendientes.md`.

- Nodo `MateriaCurso` (`asig:SMAT01`): la materia en un curso, del que cuelgan los bloques de ese curso; atajo `materia_curso` en sus nodos.
- Enunciados de competencia por curso (`enunciados_curso`) cuando el documento oficial los varía (correcciones 0263–0266).
- Nodos retirados como obsoletos (`accion: retirar`, `obsoleto`, `sustituido_por`).
- Correcciones 0267–0269: enunciados de competencia de Griego I y II, Antropología y Sociología y Cultura Científica (la competencia 2 repetía la 1).

### Cambiado
- Los bloques competenciales y de saberes cuelgan de su `MateriaCurso`, no de la materia (los identificadores no cambian).
- `contrastar` ya no da por explicada una competencia con otro enunciado en otro curso: el modelo guarda el de cada curso.
- Todos los textos se normalizan a Unicode NFC al importar (587 textos de la exportación traían las tildes descompuestas); no cambia ningún texto a la vista.
- Licencias: datos con CC BY 4.0 (con la aclaración del art. 13 TRLPI sobre los textos normativos) y código con GPL-3.0; `curriculo.json` incluye la licencia en su cabecera.
- El importador trata como aviso un saber repetido de forma idéntica y reconstruye el código de un saber
  repetido cuyo texto indica otro apartado (`sb:BBIE02SBIII.3.1`).
- `config/incidencias_aceptadas.yaml` queda vacío: el corpus no tiene errores.
