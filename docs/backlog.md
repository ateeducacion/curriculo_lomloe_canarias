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
- [ ] **2.2 Adaptar el lector de ODT** (`herramientas/odt.py`) al formato de Bachillerato
  (varias materias o cursos por documento: I y II) y de Primaria (ciclos en lugar de cursos,
  saberes de tercer nivel).
  Cierre: `odt.leer` devuelve competencias, bloques y saberes de los 12 documentos sin avisos
  de secciones no encontradas. **Depende de** 2.1.
- [ ] **2.3 Detectar las secciones automáticamente** a partir de los cursos de cada materia
  (`config/materias.csv`), en lugar de escribirlas a mano en el manifiesto. Las `secciones`
  manuales siguen valiendo para los casos especiales.
  Cierre: `contrastar` procesa los documentos descargados sin `secciones` en el manifiesto,
  y `eso-matematicas` da el mismo resultado que hoy. **Depende de** 2.2.
- [ ] **2.4 Generar correcciones desde el contraste**: opción
  `python -m herramientas.contrastar --proponer` que escribe `correcciones/NNNN-*.yaml` en
  estado `propuesta`, con motivo, fuente (documento y sha256) y los cambios, una por documento.
  No sobrescribe correcciones existentes.
  Cierre: genera ficheros válidos para `herramientas/correcciones.py`. **Depende de** 2.3.
- [ ] **2.5 Proponer las correcciones** de los 12 documentos con 2.4 y revisar a mano los casos que
  no son de texto:
  - `descriptor_desconocido` CE7 (PEDK): ver en el ODT qué descriptor es; si es una errata,
    corrección; si existe, añadirlo a `config/descriptores.csv`.
  - `codigo_duplicado` (`sb:BBIE02SBIII.1.1`, `sb:SUEC02SBIV.6`): ver en el ODT si el segundo
    es otro saber con el código mal puesto.

  **Depende de** 2.4.
- [ ] **2.6 Aprobación** de las correcciones (0001, 0002 y las nuevas) por la persona responsable
  del currículo (`estado: aprobada`, `aprobada_por`).
- [ ] **2.7 Reconstruir y vaciar** `config/incidencias_aceptadas.yaml`:
  `python -m herramientas.construir` y retirar las incidencias resueltas.
  Cierre: lista vacía y CI en verde. **Depende de** 2.6.

## Fase 3 — Revisar las materias con encabezados contaminados

Objetivo: explicar los avisos `encabezado_no_corresponde` y `texto_en_conflicto`, y las 175
`explicacion_repetida_entre_cursos`. **Depende de** 2.2–2.4.

- [ ] **3.1 Descargar y registrar el segundo lote**:
  - ESO: Lengua Extranjera, Física y Química, Historia y Geografía de Canarias, Cultura y
    Ciudadanía Digital, Lengua Castellana y Literatura, Educación Plástica, Segunda Lengua
    Extranjera, Educación Física, Geografía e Historia, Economía Personal y Social.
  - Primaria: Educación Física.
- [ ] **3.2 Contrastar y proponer correcciones** de los textos mezclados entre materias.
- [ ] **3.3 Clasificar las explicaciones repetidas entre cursos**: corrección si el ODT las
  distingue; nota justificativa si también son iguales en el ODT.
- [ ] **3.4 Aprobación** y reconstrucción.

## Fase 4 — Completar la configuración y las decisiones

- [ ] **4.1 Descriptores**: descargar los anexos 1 (PDF, enlaces en `anexos_competencias` del
  manifiesto), verificar `config/descriptores.csv` y marcar `verificado: si`.
- [ ] **4.2 Cobertura** (decisiones de la persona responsable):
  - [ ] Optativas que faltan en la exportación (*Juegos y Deportes Tradicionales de Canarias*,
    *Música, Expresión y Espectáculos*): crearlas desde su ODT.
  - [ ] ¿Los ámbitos de diversificación de la exportación (`SMBS`, `SAMB`, `SAM3`) corresponden al
    Decreto 86/2025?
  - [ ] ¿Entran el silbo gomero y Religión?
- [ ] **4.3 Modelo** (decisiones):
  - [ ] ¿Se unifican las competencias de Matemáticas A y B con las de Matemáticas?
  - [ ] Códigos de materia inconsistentes: `TSA`/`TA7`, `PLW`/`LNT`, `VAL`/`EDK`.
- [ ] **4.4 Licencia del corpus y fecha de la exportación** de ProIDEAC (`config/corpus.yaml`).
- [ ] **4.5 Formatos de Infantil y de los ámbitos**: descargar un ODT de cada y adaptar el lector.
- [ ] **4.6 CODEOWNERS** con los equipos reales y protección de la rama `main`.

## Fase 5 — Preparar la 1.0.0

- [ ] **5.1 Contrastar los 105 documentos.** Ninguna diferencia sin explicar: o hay corrección,
  o una nota que justifica que el corpus es correcto. **Depende de** fases 2–4.
- [ ] **5.2 Pruebas automáticas** (pytest) del importador, el lector de ODT, el contraste y las
  correcciones, ejecutadas en la CI.
- [ ] **5.3 Exportación RDF**: salida SKOS en Turtle en la publicación, con el modelo acordado
  para Omeka S.
- [ ] **5.4 Revisar la documentación** (README, modelo, contribuir, pendientes).
- [ ] **5.5 Publicar v1.0.0**: CHANGELOG, `version` en `config/corpus.yaml`, etiqueta `v1.0.0`.
