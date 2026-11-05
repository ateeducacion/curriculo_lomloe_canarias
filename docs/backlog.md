# Backlog hasta la versión 1.0.0

Plan de trabajo para llevar el corpus de la 0.x a la 1.0.0. Complementa
[`pendientes.md`](pendientes.md), que recoge el estado y las decisiones abiertas; aquí
están las tareas, en orden, con su criterio de cierre.

Leyenda: `[x]` hecha · `[ ]` pendiente · **Depende de** indica qué tiene que estar antes.
Los ODT se descargan desde las páginas de currículos de la Consejería:

- Infantil: <https://www.gobiernodecanarias.org/educacion/web/infantil/informacion/contenidos/>
- Primaria: <https://www.gobiernodecanarias.org/educacion/web/primaria/informacion/contenidos/curriculos/index.html>
- ESO: <https://www.gobiernodecanarias.org/educacion/web/secundaria/informacion/ordenacion-curriculo/curriculos-de-la-educacion-secundaria-obligatoria-eso/index.html>
- Bachillerato: <https://www.gobiernodecanarias.org/educacion/web/bachillerato/informacion/ordenacion_curriculo_competencias/curriculo_bach_lomce/index.html>

Los enlaces directos a cada ODT están en `fuentes/manifiesto.yaml` (`url_odt`).

## Fase 1 — Poner en marcha el repositorio

- [x] Estructura inicial, CI de validación y de publicación, credencial de la exportación retirada.

## Fase 2 — Cerrar los 140 errores heredados

Objetivo: `config/incidencias_aceptadas.yaml` vacío.

Reparto de los 140 errores por documento:

| Documento (`id` del manifiesto) | Materias | Errores |
|---|---|---|
| `primaria-matematicas` | PMAT | 32 `saber_sin_texto` + 2 `ce_sin_enunciado` |
| `bachillerato-filosofia` | BFIL | 30 `saber_sin_texto` |
| `bachillerato-historia-de-la-filosofia` | BHFI | 5 `saber_sin_texto` |
| `bachillerato-griego-i-y-ii` | BGRO, BGRE | 12 `saber_sin_texto` |
| `bachillerato-latin-i-y-ii` | BLAI, BLII | 12 `saber_sin_texto` |
| `bachillerato-cultura-cientifica` | BCUF | 4 `saber_sin_texto` |
| `bachillerato-matematicas-i-y-ii` | BMTI, BMII | 8 `ce_sin_enunciado` |
| `bachillerato-matematicas-aplicadas-a-las-ciencias-sociales-i-y-ii` | BMCI, BAII | 8 `ce_sin_enunciado` |
| `bachillerato-matematicas-generales` | BMZT | 4 `ce_sin_enunciado` |
| `bachillerato-bioestadistica` | BBIE | 2 `ce_sin_enunciado` + 1 `codigo_duplicado` |
| `primaria-educacion-en-valores-civicos-y-eticos` | PEDK | 4 `descriptor_desconocido` (CE7) |
| `eso-tecnologia-y-digitalizacion` | SUEC | 1 `codigo_duplicado` |
| `eso-matematicas` (ya descargado) | SMAT, SMMA, SMMB | 15 `ce_sin_enunciado` (corrección 0001 propuesta) |

Tareas:

- [x] **2.1 Descargar y registrar los 12 ODT** de la tabla en `fuentes/documentos/<etapa>/`
  y ejecutar `python -m herramientas.registrar_fuentes` (03-11-2026).
- [x] **2.2 Adaptar el lector de ODT** (`herramientas/odt.py`) al formato de Bachillerato
  (varias materias o cursos por documento: I y II) y de Primaria (ciclos en lugar de cursos,
  saberes de tercer nivel).
  Cierre: `odt.leer` devuelve competencias, bloques y saberes de los 12 documentos sin avisos
  de secciones no encontradas. **Depende de** 2.1.
  Hecho: secciones sin rótulo «Bloques competenciales», filas de criterio sin punto o sin
  espacio, descriptores con punto final y párrafos en `list-header`.
- [x] **2.3 Detectar las secciones automáticamente** a partir de los cursos de cada materia
  (`config/materias.csv`), en lugar de escribirlas a mano en el manifiesto. Las `secciones`
  manuales siguen valiendo para los casos especiales.
  Cierre: `contrastar` procesa los documentos descargados sin `secciones` en el manifiesto,
  y `eso-matematicas` da el mismo resultado que hoy. **Depende de** 2.2.
- [x] **2.4 Generar correcciones desde el contraste**: opción
  `python -m herramientas.contrastar --proponer` que escribe `correcciones/NNNN-*.yaml` en
  estado `propuesta`, con motivo, fuente (documento y sha256) y los cambios, una por documento.
  No sobrescribe correcciones existentes.
  Cierre: genera ficheros válidos para `herramientas/correcciones.py`. **Depende de** 2.3.
  Hecho: los saberes se emparejan por contenido; los tramos ambiguos van a «revisar a mano».
- [x] **2.5 Proponer las correcciones** de los 12 documentos con 2.4 y revisar a mano los casos que
  no son de texto:
  - `descriptor_desconocido` CE7 (PEDK): ver en el ODT qué descriptor es; si es una errata,
    corrección; si existe, añadirlo a `config/descriptores.csv`.
  - `codigo_duplicado` (`sb:BBIE02SBIII.1.1`, `sb:SUEC02SBIV.6`): ver en el ODT si el segundo
    es otro saber con el código mal puesto.

  **Depende de** 2.4.

  Hecho: correcciones 0003–0012 (generadas, 124 incidencias) y 0013–0016 (manuales: CE7 es
  CE2; saberes perdidos por códigos truncados en Matemáticas de Primaria; III.1.8 de
  Filosofía; III.3.2 de Bioestadística). Los dos duplicados se resuelven en el importador:
  el de Tecnología y Digitalización era un registro idéntico (ahora es un aviso) y el de
  Bioestadística, un saber de III.3 exportado como III.1.1 (ahora se reconstruye su código a
  partir del texto). Simulando la aprobación de todas se resuelven las 140 incidencias.
- [x] **2.6 Aprobación** de las correcciones (0001, 0002 y las nuevas) por la persona responsable
  del currículo (`estado: aprobada`, `aprobada_por`). Hecho: 0001–0016 aprobadas el 03-11-2026.
- [x] **2.7 Reconstruir y vaciar** `config/incidencias_aceptadas.yaml`:
  `python -m herramientas.construir` y retirar las incidencias resueltas.
  Cierre: lista vacía y CI en verde. **Depende de** 2.6. Hecho: el corpus no tiene ningún error.

Notas de la aprobación:

- 0015 (Filosofía III.1.8) se aprueba con los códigos planos de ProIDEAC y el nuevo III.1.8.7,
  aunque el documento anida tres de esos saberes bajo III.1.8.4. Si se decide respetar la
  jerarquía del documento, hará falta otra corrección (cambia identificadores).
- 0012 (Cultura Científica) se aprueba con el texto del documento, que repite «Contaminación
  lumínica» en II.2.4.1 y II.2.4.3. Queda por confirmar con la Consejería si es una errata.

## Fase 3 — Revisar las materias con encabezados contaminados

Objetivo: explicar los avisos `encabezado_no_corresponde` y `texto_en_conflicto`, y las 175
`explicacion_repetida_entre_cursos`. **Depende de** 2.2–2.4.

- [x] **3.1 Descargar y registrar el segundo lote**:
  - ESO: Lengua Extranjera, Física y Química, Historia y Geografía de Canarias, Cultura y
    Ciudadanía Digital, Lengua Castellana y Literatura, Educación Plástica, Segunda Lengua
    Extranjera, Educación Física, Geografía e Historia, Economía Personal y Social.
  - Primaria: Educación Física.

  Hecho (03-11-2026). El lector ya admite descripciones de bloque de saberes (Lengua
  Castellana) y rótulos de curso compartidos por varias materias (Segunda Lengua Extranjera).
- [x] **3.2 Contrastar y proponer correcciones** de los textos mezclados entre materias.
  Hecho: `contrastar --proponer` detecta además textos de saber de otra materia, explicaciones
  copiadas de otro curso y bloques con título y descripción juntos. Correcciones 0017–0033
  (generadas) y 0034–0035 (manuales), pendientes de aprobación. Con todas aprobadas, 107 de
  los 110 avisos `encabezado_no_corresponde` y `texto_en_conflicto` quedan explicados (el nodo
  coincide con el documento). Los avisos seguirán apareciendo porque los produce el importador
  al leer la exportación; los otros 3 son de Educación Física de Primaria (ver 3.7).
- [x] **3.3 Clasificar las explicaciones repetidas entre cursos** de las materias descargadas:
  las 196 que el documento distingue se corrigen (avisos: de 171 a 110). Los 110 que quedan
  son de materias sin documento descargado: se revisarán al contrastarlas (5.1).
  Nota: tras corregir Infantil, el aviso cuenta también los cursos de un mismo ciclo, que
  comparten la explicación oficial (Infantil y Primaria). Conviene que la regla los excluya.
- [x] **3.4 Aprobación** de 0017–0035 y reconstrucción. Hecho: aprobadas el 03-11-2026.
- [ ] **3.5 Códigos incoherentes con la numeración del texto**: 88 registros de la exportación
  (casi todos de 3.º ESO, más Historia de Canarias y Bioestadística) tienen un código cuyo
  apartado no coincide con el número de su encabezado. Hoy el importador solo reconstruye el
  código cuando además choca con otro (caso de Bioestadística). Decidir si la regla se extiende.
- [x] **3.6 Comparar saberes por contenido en el informe de contraste**, como ya hace
  `--proponer`: la comparación por número da falsos positivos cuando la exportación y el
  documento anidan distinto (Matemáticas de Primaria, Filosofía).
  Hecho (04-11-2026): los saberes de cada bloque se alinean por contenido antes de
  compararlos (diferencias: de 895 a 819). Al emparejar bien afloran textos cortados y de
  otra versión; con la búsqueda exacta en el BOC, correcciones 0137–0165 (29 ficheros).
- [x] **3.7 Diferencias de versión**: en Educación en Valores Cívicos y Éticos y en Educación
  Física de Primaria, el ODT y la exportación difieren en muchos textos, explicaciones y
  descriptores. Comprobar cuál corresponde al Decreto 211/2022 publicado en el BOC.
  Hecho (04-11-2026): los ODT son la versión publicada. En Primaria, donde difieren, el texto
  del ODT está en el BOC y el de la exportación no en 410 casos, y al revés en 6. Los textos
  de los cinco decretos están en `fuentes/boletines/` y `contrastar --proponer` los usa (5.1).
- [x] **3.8 Descriptores de bloque**: en Plástica, Historia de Canarias, Lengua Castellana y
  Educación Física de Primaria los descriptores de algunos bloques no coinciden con la
  cabecera de la tabla del documento. Comprobar si el importador los toma de los criterios.
  Hecho (04-11-2026): sí, el corpus calcula los del bloque como la unión de los de sus
  criterios. El contraste compara el bloque con esa unión en el documento; en 97 bloques es
  la cabecera del documento la que no cuadra con sus propios criterios, y eso se anota como
  incoherencia del documento, no como diferencia del corpus. Los descriptores de criterio se
  deciden con el BOC (lista completa): correcciones 0166–0175. Errata en el BOC: «CCE3» en
  Lengua Castellana de 1.º y 2.º de Primaria (criterio 7.2), que se deja como está.
- [ ] **3.9 Restos menores**: dobles espacios o espacios de no separación (Economía Personal y
  Social, Física y Química, Cultura y Ciudadanía Digital) y una descripción de bloque truncada
  en Cultura y Ciudadanía Digital (`sb:SCUJ03SBV`).

## Fase 4 — Completar la configuración y las decisiones

- [x] **4.1 Descriptores**: descargar los anexos 1 (PDF, enlaces en `anexos_competencias` del
  manifiesto), verificar `config/descriptores.csv` y marcar `verificado: si`.
  Hecho: coinciden Primaria (34), ESO (34, columna izquierda del anexo del Decreto 30/2023) y
  Bachillerato (38, columna derecha, con CPSAA1, CPSAA3, CCEC3 y CCEC4 desdoblados). Infantil
  tiene 8 competencias sin descriptores; su anexo abrevia «CEC» la que el corpus llama CCEC
  (anotado en la columna `nota`).
- [x] **4.2 Cobertura** (decisiones de la persona responsable, 04-11-2026):
  - [x] Optativas que faltan en la exportación (*Juegos y Deportes Tradicionales de Canarias*,
    *Música, Expresión y Espectáculos*): crearlas desde su ODT. Códigos `JUI` y `MUW` (1.º de
    Bachillerato), asignados el 04-11-2026. Correcciones 0042 y 0043 propuestas, generadas con
    `herramientas.materia_desde_odt`; aprobadas el 04-11-2026.
  - [x] ¿Los ámbitos de diversificación de la exportación (`SMBS`, `SAMB`, `SAM3`) corresponden al
    Decreto 86/2025? Sí: de 139 competencias y criterios, 119 son idénticos al ODT y casi todos
    los demás son retoques menores. Difieren de verdad la competencia 4 del Ámbito Lingüístico y
    Social y dos criterios del Ámbito Práctico, y hay saberes del ODT que la exportación no trae
    (revisar a mano, junto con 3.6).
  - [x] ¿Entran el silbo gomero y Religión? No (registrado en `excluidos` del manifiesto).
- [x] **4.3 Modelo** (decisiones del 04-11-2026):
  - [x] ¿Se unifican las competencias de Matemáticas A y B con las de Matemáticas? No: se
    mantienen sus propios nodos y no cambia ningún identificador.
  - [x] Códigos de materia inconsistentes: `TSA`/`TA7`, `PLW`/`LNT`, `VAL`/`EDK`. Se conservan
    los identificadores de ProIDEAC; el catálogo mantiene las dos columnas.
- [x] **4.4 Licencia del corpus y fecha de la exportación** de ProIDEAC (`config/corpus.yaml`).
  Datos CC BY 4.0 con la aclaración del art. 13 TRLPI (`LICENCIA-DATOS.md`); código GPL-3.0.
  Fecha de la exportación: desconocida (se anota la de incorporación, 03-11-2026).
- [x] **4.5 Formatos de Infantil y de los ámbitos**: descargar un ODT de cada y adaptar el lector.
  Hecho con los 6 documentos (3 áreas de Infantil y 3 ámbitos): ciclos de Infantil, criterios de
  Infantil en una sola fila y sin descriptores, bloques de saberes «Bloque I. …» y `secciones`
  manuales para los ámbitos. Correcciones propuestas 0036–0041 (explicaciones copiadas de otro
  curso, 55 en total, y título y descripción de bloques en el Ámbito Lingüístico y Social). Aprobadas el 04-11-2026.
- [ ] **4.6 CODEOWNERS** con los equipos reales y protección de la rama `main`. Aplazado
  (04-11-2026): no bloquea la 1.0.0.

## Fase 5 — Preparar la 1.0.0

- [x] **5.1 Contrastar los 105 documentos.** Ninguna diferencia sin explicar: o hay corrección,
  o una nota que justifica que el corpus es correcto. **Depende de** fases 2–4.
  Hecho (05-11-2026): «sin explicar: 0» en `informes/contraste.md`; 218 diferencias, todas
  explicadas automáticamente con el BOC, y 77 de 105 documentos coinciden por completo.
  `contrastar --proponer` compara con el texto del BOC (limpio de los descriptores que pdftotext
  intercala en las tablas) y propone el texto del documento cuando es el publicado: versión y
  puntuación publicadas, solo espacios, textos cortados y de otro curso (correcciones
  0044–0136 y 0176–0210). Todos los textos se normalizan a NFC: 587 de la exportación traían
  las tildes descompuestas. Las 127 diferencias que el BOC no decidía se resolvieron con el
  criterio aprobado de que el ODT oficial es la referencia y el corpus debe reflejarlo
  (correcciones 0211–0233, una por documento): textos, descripciones, explicaciones y
  descriptores toman el valor del documento, y los bloques de saberes con saberes que faltaban
  o sobraban se rehacen con los saberes y la numeración del documento. Una corrección con
  `valor: null` quita el campo (descripciones de bloque que el documento no tiene).
- [x] **5.2 Pruebas automáticas** (pytest) del importador, el lector de ODT, el contraste y las
  correcciones, ejecutadas en la CI.
  Hecho (05-11-2026): 30 pruebas en `tests/` (importador, lector de ODT con documentos mínimos
  construidos en memoria, texto del BOC, contraste y correcciones), con `requirements-dev.txt`.
  Las dos CI ejecutan `pytest` y `contrastar --estricto`, que falla si queda alguna diferencia
  sin explicar.
- [ ] **5.3 Exportación RDF**: salida SKOS en Turtle en la publicación, con el modelo acordado
  para Omeka S.
- [ ] **5.4 Revisar la documentación** (README, modelo, contribuir, pendientes).
- [ ] **5.5 Publicar v1.0.0**: CHANGELOG, `version` en `config/corpus.yaml`, etiqueta `v1.0.0`.
