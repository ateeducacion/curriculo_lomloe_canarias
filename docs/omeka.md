# El currículo en Omeka S

Contrato entre `curriculo.json` y los ítems de Omeka S. Lo cumple el módulo de sincronización,
que carga cada versión publicada, y lo leen los módulos que usan el currículo, como OERManager.
Ninguno depende del otro: los dos dependen de este documento.

La referencia es el `curriculo.json` de una versión publicada (release `v<versión>`). Omeka
adopta el modelo del repositorio ([`modelo.md`](modelo.md)): las mismas clases `cur:` y
propiedades SKOS que el Turtle, con las diferencias que se explican abajo. Decisiones del
09-11-2026 (especificación en
[`superpowers/specs/2026-11-09-contrato-omeka-design.md`](superpowers/specs/2026-11-09-contrato-omeka-design.md)).

## Estructura

| Elemento | En Omeka |
|---|---|
| Vocabularios | `dcterms`, `skos` y `cur` (este, importado del `cur.ttl` de la misma versión, espacio de nombres `<base>def/cur#`); `schema` y `lrmi` siguen haciendo falta para los REA. No se usa `owl`: Omeka no lo trae |
| Ítems | Uno por nodo de `curriculo.json` (15.438 en la 1.1.1), con clase de recurso `cur:<Tipo>`: `Etapa`, `Curso`, `Materia`, `MateriaCurso`, `CompetenciaEspecifica`, `BloqueCompetencial`, `CriterioEvaluacion`, `BloqueSaberes`, `SaberBasico` |
| Conjunto «Currículo LOMLOE de Canarias» | Clase `skos:ConceptScheme`. Contiene todos los ítems. Lleva `skos:prefLabel`, `dcterms:hasVersion` (versión cargada, p. ej. `1.1.1`), `dcterms:license` (`corpus.licencia.url`) y `dcterms:identifier` (URI `<base>id/curriculo`) |
| Conjunto «Currículo · Retirados» | Contiene, además, los ítems retirados |
| Plantillas de recurso | Una por clase, «Currículo · <rótulo de la clase>», con `skos:prefLabel` como título y `skos:definition` como descripción |
| Visibilidad | Todo público, también los retirados (los REA que los enlazaban deben poder seguir resolviéndolos) |

Los ítems no llevan `schema:DefinedTerm`: en Omeka un ítem tiene una sola clase. El doble
tipado sigue en el Turtle publicado. Los descriptores operativos y las competencias clave no
son ítems: se enlazan por su URI publicada.

## Correspondencia de campos

Los literales llevan idioma `es`. Los valores repetidos siguen el orden del corpus.

| Campo de `curriculo.json` | Propiedad | Tipo de valor |
|---|---|---|
| `id` | `dcterms:identifier` | dos valores: literal (`crit:SMAT01CE1.1`) y `uri` (`<base>id/crit/SMAT01CE1.1`, con el `id` como etiqueta) |
| `tipo` | clase de recurso `cur:<tipo>` y su plantilla | — |
| `notation` | `skos:notation` | literal |
| `prefLabel` | `skos:prefLabel` | literal |
| `definition` | `skos:definition` | literal |
| `scopeNote` | `skos:scopeNote` | literal |
| `enunciados_curso` | `cur:enunciadoEnCurso`, un valor por curso | literal con anotación de valor `cur:curso` de tipo `uri` (URI del curso, con el `prefLabel` del curso como etiqueta) |
| `broader` | `skos:broader` | `resource:item` |
| `agrupa` | `cur:agrupa` | `resource:item` |
| `bloque` | `cur:bloqueCompetencial` | `resource:item` |
| `descriptores` | `cur:descriptorOperativo` | `uri`: `<base>id/descriptor/<notation de la etapa del nodo>/<código>`, con el código como etiqueta |
| `etapa` | `cur:etapa` | `resource:item` |
| `curso` | `cur:curso` | `resource:item` |
| `cursos` (materias) | `cur:curso`, un valor por curso | `resource:item` |
| `materia` | `cur:materia` | `resource:item` |
| `materia_curso` | `cur:materiaCurso` | `resource:item` |
| `obsoleto` | pertenencia a «Currículo · Retirados» y `skos:changeNote` «Retirado en la versión X» | literal |
| `sustituido_por` | `dcterms:isReplacedBy` | `resource:item` |

**URIs.** `<base>` es `corpus.uri_base` de `curriculo.json` (hoy
`https://ateeducacion.github.io/curriculo_lomloe_canarias/`). Un `id` `<prefijo>:<código>`
corresponde a `<base>id/<prefijo>/<código>`, como en el Turtle: `crit:SMAT01CE1.1` →
`<base>id/crit/SMAT01CE1.1`.

### Ejemplo: el criterio `crit:SMAT01CE1.1` (versión 1.1.1)

Clase `cur:CriterioEvaluacion`, plantilla «Currículo · Criterio de evaluación», en el conjunto
«Currículo LOMLOE de Canarias»:

| Propiedad | Valor |
|---|---|
| `dcterms:identifier` | `crit:SMAT01CE1.1` (literal) |
| `dcterms:identifier` | `<base>id/crit/SMAT01CE1.1` (uri, etiqueta `crit:SMAT01CE1.1`) |
| `skos:notation` | `SMAT01CE1.1` |
| `skos:prefLabel` | `SMAT01CE1.1 · Interpretar problemas matemáticos, identificando los datos y el objetivo, definiendo la…` |
| `skos:definition` | `Interpretar problemas matemáticos, identificando los datos y el objetivo, […] con el fin de comprender el enunciado y explorar distintas maneras de proceder.` |
| `skos:broader` | ítem `ce:SMATC1` |
| `cur:bloqueCompetencial` | ítem `bc:SMAT01BC1` |
| `cur:descriptorOperativo` | `<base>id/descriptor/ESO/CCL1` (uri, etiqueta `CCL1`), y lo mismo para `CCL2`, `STEM1`, `CD2`, `CC2` y `CE3` |
| `cur:materia` | ítem `materia:SMAT` |
| `cur:materiaCurso` | ítem `asig:SMAT01` |
| `cur:curso` | ítem `curso:S01` |
| `cur:etapa` | ítem `etapa:ESO` |

## Diferencias con el Turtle

1. **Sin `skos:narrower`.** Omeka muestra los hijos como recursos enlazados y se obtienen
   consultando `skos:broader`; escribirlo duplicaría unas 15.000 aristas.
2. **Enunciados por curso como literales anotados**, no como nodos (en el Turtle son nodos en
   blanco, que Omeka no tiene). `skos:definition` conserva un único valor: el general.
3. **Sin `skos:inScheme` ni `skos:topConceptOf`.** Lo dicen la pertenencia al conjunto y la
   clase `cur:Etapa`.
4. **`skos:changeNote` solo marca la retirada** (en el Turtle, `owl:deprecated`). Ninguna otra
   cosa escribe esa propiedad en los ítems del currículo, de modo que «sin `skos:changeNote`»
   (operador `nex` de la búsqueda de Omeka) equivale a «vigente». La búsqueda de Omeka, sin
   módulos añadidos, no puede excluir los ítems de un conjunto; esta regla lo permite en una
   sola consulta.

## Sincronización

Lo que el módulo garantiza, sea cual sea su implementación:

- **Origen.** `curriculo.json` y `cur.ttl` de una versión publicada concreta (assets del
  release `v<versión>`), con el `sha256` comprobado antes de usar nada.
- **Identidad.** Cada ítem se localiza por el literal de `dcterms:identifier` dentro del
  conjunto «Currículo LOMLOE de Canarias». Dos ítems con el mismo literal son un error.
- **Propiedad del módulo.** Son del módulo las propiedades de la tabla de correspondencia, la
  clase de recurso, la plantilla y la pertenencia a los dos conjuntos. Al actualizar, los
  valores de esas propiedades se sustituyen enteros; cualquier otra propiedad del ítem (añadida
  a mano o por otro módulo) se conserva. Una edición manual de una propiedad del módulo se
  pierde en la siguiente sincronización; el informe previo la muestra como cambio.
- **Dos pasadas.** Primero se crean o actualizan todos los ítems con sus literales; después se
  escriben los enlaces `resource:item`, que necesitan los ids internos.
- **Retirada.** Ningún ítem se borra. Un nodo con `obsoleto` entra en «Currículo · Retirados» y
  lleva `skos:changeNote` y, si lo hay, `dcterms:isReplacedBy`.
- **Errores que detienen la sincronización antes de aplicar nada:** un ítem del conjunto cuyo
  id no está en el JSON; un ítem cuya clase no coincide con el `tipo` del nodo; un nodo retirado
  en Omeka que vuelve a estar vigente en el JSON; una versión anterior a la cargada
  (`dcterms:hasVersion`).
- **Aprobación.** Antes de aplicar, un informe de cambios (ítems nuevos, modificados con las
  propiedades que cambian, retirados) que aprueba una persona.
- **Idempotencia y cortes.** Aplicar dos veces la misma versión no cambia nada.
  `dcterms:hasVersion` del conjunto se actualiza al final: si la aplicación se corta, sigue
  figurando la versión anterior y basta con relanzarla.

## Consumidores

**Recursos educativos (REA).** Un REA (`lrmi:LearningResource`) se enlaza al currículo con
valores `resource:item`:

| Propiedad del REA | Apunta a |
|---|---|
| `lrmi:educationalLevel` | `cur:Curso` |
| `schema:about` | `cur:MateriaCurso` (la materia en un curso) |
| `lrmi:teaches` | `cur:SaberBasico`, de cualquier nivel |
| `lrmi:assesses` | `cur:CriterioEvaluacion` |

Etapa, materia y competencias son nodos de navegación: no se escriben en el REA.

**Consultas.** Para trabajar solo con los términos vigentes, se filtra por el conjunto
«Currículo LOMLOE de Canarias» y por `skos:changeNote` sin valor (`nex`). La jerarquía se
recorre con los atajos: los cursos de una etapa son los `cur:Curso` con `cur:etapa`; las
materias de un curso, los `cur:MateriaCurso` con `cur:curso`; sus saberes y criterios, los
`cur:SaberBasico` y `cur:CriterioEvaluacion` con `cur:materiaCurso`.

**OERManager** sigue este contrato desde su ADR-0022, que sustituye a su ADR-0009.
