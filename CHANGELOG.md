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

### Cambiado
- El importador trata como aviso un saber repetido de forma idéntica y reconstruye el código de un saber
  repetido cuyo texto indica otro apartado (`sb:BBIE02SBIII.3.1`).
- `config/incidencias_aceptadas.yaml` queda vacío: el corpus no tiene errores.
