# Currículo LOMLOE de Canarias

Fuente única y versionada del currículo LOMLOE de Canarias (Infantil, Primaria, ESO y
Bachillerato) en un formato estructurado y validado, pensada para que otros sistemas
—empezando por el repositorio de REA en Omeka S— la consuman sin tener que mantener su
propia copia.

> **Estado:** versión 0.x, en preparación. Hay incidencias heredadas de la exportación
> de origen y decisiones pendientes: ver [`docs/pendientes.md`](docs/pendientes.md).
> Plan de trabajo hasta la 1.0.0: [`docs/backlog.md`](docs/backlog.md).

## Qué hay en el repositorio

```
fuentes/
  manifiesto.yaml          normas y documentos oficiales (enlace, fichero local, sha256)
  proideac/exportacion-1/  exportación de ProIDEAC usada como base
  documentos/<etapa>/      ODT oficiales descargados
config/
  corpus.yaml              identificación del corpus y de su base
  materias.csv             catálogo de materias: código, denominación, cursos, documento
  descriptores.csv         descriptores operativos / competencias clave por etapa
  incidencias_aceptadas.yaml  errores conocidos que de momento no bloquean la CI
correcciones/              una corrección por fichero, con motivo, fuente y estado
datos/                     corpus construido: un JSON por materia (+ niveles.json)
esquema/                   JSON Schema del corpus
herramientas/              importación, corrección, validación, contraste y construcción
informes/                  último informe de construcción y de contraste
docs/                      modelo de datos, cómo contribuir y pendientes
```

## Cómo se construye

```
exportación ProIDEAC ──► importar ──► aplicar correcciones aprobadas ──► validar ──► datos/
                                                                            │
                                         ODT oficiales ──► contrastar ◄─────┘
```

- **No se edita `datos/` a mano.** Se regenera con las herramientas y la CI comprueba que
  coincide exactamente con lo que producen.
- **No se edita la exportación de origen.** Los errores se arreglan con ficheros en
  `correcciones/`, que documentan el motivo y la fuente, y que solo se aplican cuando
  están aprobados.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt          # requirements.txt + pytest

python -m herramientas.construir             # regenera datos/ e informes/
python -m herramientas.construir --comprobar # lo que ejecuta la CI
python -m herramientas.contrastar            # compara con los ODT descargados
python -m pytest                             # pruebas automáticas
```

## Modelo de datos (resumen)

Cada nodo es un concepto (SKOS) de uno de estos tipos: `Etapa`, `Curso`, `Materia`, `MateriaCurso`,
`CompetenciaEspecifica`, `BloqueCompetencial`, `CriterioEvaluacion`, `BloqueSaberes` y
`SaberBasico`. Los identificadores conservan los códigos de ProIDEAC
(`crit:SMAT01CE1.1`, `sb:SMAT01SBI.1.1`…). Detalle en [`docs/modelo.md`](docs/modelo.md).

## Versiones y consumo

Cada versión se publica como *release* de GitHub con:

- `curriculo.json` y `curriculo.json.sha256`: el corpus completo; es lo que deben consumir
  otros sistemas.
- `curriculo-csv.zip`: un CSV por tipo de nodo, para revisión o herramientas de hoja de cálculo.

Numeración: **parche** = correcciones de texto; **menor** = nodos nuevos o retirados;
**mayor** = cambio de marco normativo o de modelo de datos.

Los consumidores deben fijar una versión concreta y comprobar el sha256, nunca descargar
«la última» automáticamente. El módulo de Omeka S descarga
`https://github.com/ateeducacion/curriculo_lomloe_canarias/releases/download/vX.Y.Z/curriculo.json`,
lo verifica y aplica los cambios tras la aprobación de una persona.

## Contribuir

Ver [`docs/contribuir.md`](docs/contribuir.md): cómo registrar un documento oficial,
proponer una corrección, incorporar una exportación nueva y publicar una versión.

## Licencia

- **Datos** (`datos/`, `correcciones/`, `config/` y los ficheros de cada versión):
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.es).
- **Código** (`herramientas/`, `esquema/`, `.github/`): [GPL-3.0](LICENSE).

Los textos curriculares proceden de normas publicadas en el BOC y, según el artículo 13 de
la Ley de Propiedad Intelectual, no son objeto de propiedad intelectual: la licencia de los
datos cubre la estructura, los identificadores, las relaciones y las correcciones del corpus,
no los textos normativos. Detalle y forma de cita en [`LICENCIA-DATOS.md`](LICENCIA-DATOS.md).
