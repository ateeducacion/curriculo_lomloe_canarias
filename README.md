# Currículo LOMLOE de Canarias

Fuente única y versionada del currículo LOMLOE de Canarias (Infantil, Primaria, ESO y
Bachillerato) en un formato estructurado y validado, pensada para que otros sistemas
—empezando por el repositorio de REA en Omeka S— la consuman sin tener que mantener su
propia copia.

> **Estado:** versión 1.1.1 (08-11-2026), con las URIs resolubles en GitHub Pages. Los 105 documentos oficiales están contrastados
> con el corpus: 104 coinciden por completo y el otro solo difiere en 4 erratas de
> descriptores del propio documento. Decisiones abiertas y erratas detectadas en las fuentes:
> [`docs/pendientes.md`](docs/pendientes.md). Plan de trabajo: [`docs/backlog.md`](docs/backlog.md).

## Contenido

| Tipo de nodo | Nodos |
|---|---:|
| Etapas | 4 |
| Cursos | 18 |
| Materias (por etapa) | 138 |
| Materias en un curso | 232 |
| Competencias específicas | 804 |
| Bloques competenciales | 1.318 |
| Criterios de evaluación | 3.137 |
| Bloques de saberes | 1.047 |
| Saberes básicos | 8.740 |

Infantil, Primaria, ESO, Bachillerato (con sus optativas) y los ámbitos de los Programas de
Diversificación Curricular, según los decretos 196/2022, 211/2022, 30/2023, 78/2025 y 86/2025.
No incluye el silbo gomero ni Religión. Cifras al día en [`informes/resumen.md`](informes/resumen.md).

## Qué hay en el repositorio

```
fuentes/
  manifiesto.yaml          normas y documentos oficiales (enlace, fichero local, sha256)
  proideac/exportacion-1/  exportación de ProIDEAC usada como base
  documentos/<etapa>/      ODT oficiales descargados (105)
  boletines/               texto de los decretos publicados en el BOC
config/
  corpus.yaml              identificación del corpus, su base, licencia y base de las URIs
  materias.csv             catálogo de materias: código, denominación, cursos, documento
  descriptores.csv         descriptores operativos / competencias clave por etapa
  notas_contraste.yaml     diferencias con los documentos que se justifican con una nota
  incidencias_aceptadas.yaml  errores conocidos que no bloquean la CI (hoy, ninguno)
correcciones/              una corrección por fichero, con motivo, fuente y estado
datos/                     corpus construido: un JSON por materia (+ niveles.json)
esquema/                   JSON Schema del corpus y formas SHACL del RDF
vocabulario/               vocabulario RDF del corpus (cur.ttl)
herramientas/              importación, corrección, validación, contraste, construcción y RDF
tests/                     pruebas automáticas (pytest)
informes/                  último informe de construcción y de contraste
publicaciones/             id y tipo de los nodos de cada versión publicada
docs/                      modelo de datos, cómo contribuir y pendientes
```

## Cómo se construye

```
exportación ProIDEAC ──► importar ──► aplicar correcciones aprobadas ──► validar ──► datos/
                                                                            │
                         ODT oficiales + texto del BOC ──► contrastar ◄─────┤
                                                                            ▼
                                         publicación: curriculo.json, CSV, curriculo.ttl
```

- **El documento oficial es la referencia.** El corpus refleja los ODT publicados en la web
  de currículos de la Consejería. El texto del BOC sirve para explicar y decidir las
  diferencias; donde el ODT y el BOC no coinciden, la decisión queda documentada en
  [`docs/pendientes.md`](docs/pendientes.md).
- **No se edita `datos/` a mano.** Se regenera con las herramientas y la CI comprueba que
  coincide exactamente con lo que producen.
- **No se edita la exportación de origen.** Los errores se arreglan con ficheros en
  `correcciones/`, que documentan el motivo y la fuente, y que solo se aplican cuando
  están aprobados.
- **Ninguna diferencia sin explicar.** La CI falla si el contraste con los documentos deja
  alguna diferencia sin corrección ni explicación.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt          # requirements.txt + pytest

python -m herramientas.construir             # regenera datos/ e informes/
python -m herramientas.construir --comprobar # comprueba que datos/ está al día (CI)
python -m herramientas.construir --dist      # además, los ficheros de publicación en dist/
python -m herramientas.contrastar --estricto # compara con los ODT; falla si algo queda sin explicar
python -m herramientas.exportar_rdf --ttl dist/curriculo.ttl --validar   # valida el RDF con SHACL
python -m pytest                             # pruebas automáticas
```

## Modelo de datos (resumen)

Cada nodo es un concepto (SKOS) de uno de estos tipos: `Etapa`, `Curso`, `Materia`, `MateriaCurso`,
`CompetenciaEspecifica`, `BloqueCompetencial`, `CriterioEvaluacion`, `BloqueSaberes` y
`SaberBasico`. Los identificadores conservan los códigos de ProIDEAC
(`crit:SMAT01CE1.1`, `sb:SMAT01SBI.1.1`…) y no se reutilizan: un nodo retirado queda como
obsoleto. La materia en un curso (`asig:SMAT01`, Matemáticas de 1.º ESO) es el nodo con el
que se cataloga un recurso. Detalle, incluida la versión RDF, en [`docs/modelo.md`](docs/modelo.md).

## Versiones y consumo

Cada versión se publica como *release* de GitHub con:

- `curriculo.json` y `curriculo.json.sha256`: el corpus completo; es lo que deben consumir
  otros sistemas.
- `curriculo-csv.zip`: un CSV por tipo de nodo, para revisión o herramientas de hoja de cálculo.
- `curriculo.ttl` y `curriculo.ttl.sha256`: el corpus como datos enlazados (SKOS en Turtle), y
  `cur.ttl`, el vocabulario de sus clases y propiedades (importable en Omeka S). Ver
  [`docs/modelo.md`](docs/modelo.md#datos-enlazados-rdf).

Numeración: **parche** = correcciones de texto; **menor** = nodos nuevos o retirados;
**mayor** = cambio de marco normativo o de modelo de datos.

Los consumidores deben fijar una versión concreta y comprobar el sha256, nunca descargar
«la última» automáticamente. El módulo de Omeka S (en preparación, en otro repositorio)
descargará
`https://github.com/ateeducacion/curriculo_lomloe_canarias/releases/download/vX.Y.Z/curriculo.json`,
lo verificará y aplicará los cambios tras la aprobación de una persona; ver
[`docs/modelo.md`](docs/modelo.md#integración-con-omeka-s).

## Contribuir

Ver [`docs/contribuir.md`](docs/contribuir.md): cómo registrar un documento oficial,
proponer una corrección, incorporar una exportación nueva y publicar una versión.

## Licencia

- **Datos** (`datos/`, `correcciones/`, `config/`, `vocabulario/`, `publicaciones/` y los ficheros de cada versión):
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.es).
- **Código** (`herramientas/`, `esquema/`, `tests/`, `.github/`): [GPL-3.0](LICENSE).

Los textos curriculares proceden de normas publicadas en el BOC y, según el artículo 13 de
la Ley de Propiedad Intelectual, no son objeto de propiedad intelectual: la licencia de los
datos cubre la estructura, los identificadores, las relaciones y las correcciones del corpus,
no los textos normativos. Detalle y forma de cita en [`LICENCIA-DATOS.md`](LICENCIA-DATOS.md).
