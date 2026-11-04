# Pendientes y decisiones abiertas

Situación tras la primera construcción. Las cifras exactas, en `informes/resumen.md`.
Las tareas para resolverlo, en orden, en [`backlog.md`](backlog.md).

## Resuelto

- **Credencial en la exportación de ProIDEAC.** Una clave de bloque de saberes (Primaria,
  Educación Física, 1.º) contenía una clave de API antigua. Estaba ya revocada (confirmado el
  03-11-2026). Se ha eliminado igualmente de la copia del repositorio, y la CI bloquea cualquier
  cadena con formato de credencial. Conviene que el proceso de exportación de ProIDEAC no
  vuelva a introducir valores de este tipo.

## Errores heredados de la exportación

Resueltos. Los 140 errores de la primera construcción se han corregido desde los documentos
oficiales (correcciones 0001–0016, aprobadas el 03-11-2026) y con dos reglas del importador
(registros repetidos y códigos reconstruidos a partir del apartado). `config/incidencias_aceptadas.yaml`
está vacío. Quedan dos dudas de la aprobación (Filosofía III.1.8 y una posible errata en Cultura
Científica): ver la fase 2 de [`backlog.md`](backlog.md).

## Avisos relevantes

- **Encabezados de otra materia** (`encabezado_no_corresponde`, `texto_en_conflicto`): concentrados en 3.º ESO
  (Inglés, Física y Química, Historia y Geografía de Canarias, Cultura y Ciudadanía Digital…). El importador
  los descarta, pero conviene revisar esas materias completas contra su ODT.
- **Explicaciones de bloque idénticas entre cursos** (`explicacion_repetida_entre_cursos`): en Matemáticas ESO se
  confirmó que era un error (corrección 0002). En otras materias puede ser correcto: hay que revisarlo con los ODT.
- **Códigos de materia inconsistentes**: en tres materias el código del catálogo no coincide con el de sus
  identificadores (`TSA`/`TA7`, `PLW`/`LNT`, `VAL`/`EDK`). Se mantienen ambos en `config/materias.csv` y los
  identificadores no cambian (decisión del 04-11-2026).
- **Códigos de saber reconstruidos** (42): venían truncados o con punto final; se reparan a partir del número del texto.

## Cobertura

- Hay documentos oficiales sin materia en la exportación: *Juegos y Deportes Tradicionales de Canarias* y
  *Música, Expresión y Espectáculos* (optativas del Decreto 78/2025). Se crearán desde su ODT.
- Los ámbitos de diversificación de la exportación (`SMBS`, `SAMB`, `SAM3`) corresponden al Decreto 86/2025,
  con algunas diferencias de texto que se revisan con el contraste.
- No entran las concreciones del silbo gomero ni los currículos de Religión.

## Configuración por completar

- `config/descriptores.csv`: verificado contra el anexo 1 de cada decreto (03-11-2026).
- `CODEOWNERS`: sustituir los equipos marcados como PENDIENTE y activar la protección de la rama `main` (aplazado).
- `fuentes/manifiesto.yaml`: revisar las materias propuestas para cada documento y descargar los ODT.

## Integración con Omeka S

- Correspondencia entre los identificadores de este corpus y los `dcterms:identifier` de los ítems
  ya cargados (12.546 según la memoria del proyecto), para el modo de adopción del módulo.
