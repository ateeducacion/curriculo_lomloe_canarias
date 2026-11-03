# Pendientes y decisiones abiertas

Situación tras la primera construcción. Las cifras exactas, en `informes/resumen.md`.
Las tareas para resolverlo, en orden, en [`backlog.md`](backlog.md).

## Resuelto

- **Credencial en la exportación de ProIDEAC.** Una clave de bloque de saberes (Primaria,
  Educación Física, 1.º) contenía una clave de API antigua. Estaba ya revocada (confirmado el
  03-11-2026). Se ha eliminado igualmente de la copia del repositorio, y la CI bloquea cualquier
  cadena con formato de credencial. Conviene que el proceso de exportación de ProIDEAC no
  vuelva a introducir valores de este tipo.

## Errores heredados de la exportación (aceptados provisionalmente)

| Regla | Casos | Qué ocurre | Cómo se resuelve |
|---|---|---|---|
| `ce_sin_enunciado` | 39 | Matemáticas (Primaria, ESO y Bachillerato) y Bioestadística: los bloques competenciales agrupan dos competencias y la exportación solo conserva el enunciado de la primera | Correcciones desde los ODT. Las de Matemáticas ESO ya están propuestas (0001) |
| `saber_sin_texto` | 95 | Saberes de tercer nivel (p. ej. `BCUF01SBII.2.4.1`) cuyo texto no está en la exportación | Correcciones desde los ODT |
| `descriptor_desconocido` | 4 | Descriptor `CE7` en Educación en Valores Cívicos y Éticos de Primaria (5.º y 6.º) | Comprobar en el ODT qué descriptor es |
| `codigo_duplicado` | 2 | Dos saberes con el mismo código | Comprobar en el ODT |

## Avisos relevantes

- **Encabezados de otra materia** (`encabezado_no_corresponde`, `texto_en_conflicto`): concentrados en 3.º ESO
  (Inglés, Física y Química, Historia y Geografía de Canarias, Cultura y Ciudadanía Digital…). El importador
  los descarta, pero conviene revisar esas materias completas contra su ODT.
- **Explicaciones de bloque idénticas entre cursos** (`explicacion_repetida_entre_cursos`): en Matemáticas ESO se
  confirmó que era un error (corrección 0002). En otras materias puede ser correcto: hay que revisarlo con los ODT.
- **Códigos de materia inconsistentes**: en tres materias el código del catálogo no coincide con el de sus
  identificadores (`TSA`/`TA7`, `PLW`/`LNT`, `VAL`/`EDK`). Se mantienen ambos en `config/materias.csv`.
- **Códigos de saber reconstruidos** (42): venían truncados o con punto final; se reparan a partir del número del texto.

## Cobertura

- Hay documentos oficiales sin materia en la exportación: *Juegos y Deportes Tradicionales de Canarias* y
  *Música, Expresión y Espectáculos* (optativas del Decreto 78/2025).
- Comprobar si los ámbitos de diversificación de la exportación (`SMBS`, `SAMB`, `SAM3`) corresponden al
  Decreto 86/2025 o a una versión anterior.
- Decidir si entran las concreciones del silbo gomero y los currículos de Religión (publicados por el BOE).

## Configuración por completar

- `config/descriptores.csv`: lista construida a partir de los códigos usados en la exportación;
  **verificar contra el anexo 1 de cada decreto** (columna `verificado`).
- `config/corpus.yaml`: fecha de la exportación de ProIDEAC.
- `CODEOWNERS`: sustituir los equipos marcados como PENDIENTE y activar la protección de la rama `main`.
- Licencia del repositorio.
- `fuentes/manifiesto.yaml`: revisar las materias propuestas para cada documento y descargar los ODT.
- Lector de ODT: adaptarlo a los formatos de Infantil, Primaria y ámbitos cuando se descarguen.

## Integración con Omeka S

- Correspondencia entre los identificadores de este corpus y los `dcterms:identifier` de los ítems
  ya cargados (12.546 según la memoria del proyecto), para el modo de adopción del módulo.
