# Contrato del currículo en Omeka S

Fecha: 09-11-2026. Estado: aprobado; implementado el 09-11-2026 (plan en
`docs/superpowers/plans/2026-11-09-contrato-omeka.md`).

## Objetivo

Fijar cómo se representa en Omeka S cada nodo de `curriculo.json`, de modo que el módulo de
sincronización (que lo escribe) y OERManager (que lo lee) dependan de un contrato escrito y no
uno del otro. Omeka adopta el modelo del repositorio (clases `cur:` y SKOS) y OERManager se
adapta: la ADR-0009 de OERManager queda sustituida.

Cierre: el contrato está escrito en este repositorio, `curriculo.json` lleva la base de las
URIs y OERManager tiene la ADR-0022 aprobada. El código del módulo de sincronización y la
adaptación del código de OERManager tendrán su propia especificación y su propio plan.

## Decisiones

- **El modelo del repositorio en Omeka** (opción 2): clases `cur:<Tipo>` y propiedades SKOS y
  `cur:`, como en el Turtle. Descartadas: escribir con la forma de la ADR-0009 (dos modelos que
  traducir) y añadir también las aristas de schema.org (cada enlace duplicado).
- **Carga de cero.** No hay REA en producción: no se migran los ítems de la instancia de
  desarrollo.
- **Un módulo de sincronización aparte**, no dentro de OERManager: OERManager consume el
  currículo, no lo mantiene (como ya decía su ADR-0009), y los dos tienen ritmos de versión
  distintos.
- **Un REA apunta a la materia en un curso** (`schema:about` → `cur:MateriaCurso`), como la
  «Asignatura» de hoy.
- **Sin vocabularios nuevos** salvo `cur`. La instancia tiene `dcterms`, `dctype`, `bibo`,
  `foaf`, `skos`, `schema`, `lrmi` y `curation`; no tiene `owl`, así que lo que el Turtle dice
  con `owl:` se dice aquí con `dcterms:` y `skos:`.
- **Descriptores operativos como valores URI**, no como ítems: `curriculo.json` solo trae sus
  códigos y ni los REA ni OERManager los usan como nodos.

## Estructura

| Elemento | En Omeka |
|---|---|
| Vocabularios | `dcterms`, `skos` y `cur` (este, importado del `cur.ttl` de la misma versión, espacio de nombres `<base>def/cur#`); `schema` y `lrmi` siguen haciendo falta para los REA |
| Ítems | Uno por nodo de `curriculo.json` (15.438 en la 1.1.1), con clase de recurso `cur:<Tipo>`: `Etapa`, `Curso`, `Materia`, `MateriaCurso`, `CompetenciaEspecifica`, `BloqueCompetencial`, `CriterioEvaluacion`, `BloqueSaberes`, `SaberBasico` |
| Conjunto «Currículo LOMLOE de Canarias» | Clase `skos:ConceptScheme`. Contiene todos los ítems. Lleva `skos:prefLabel`, `dcterms:hasVersion` (versión cargada, p. ej. `1.1.1`), `dcterms:license` (`corpus.licencia.url`) y `dcterms:identifier` (URI `<base>id/curriculo`) |
| Conjunto «Currículo · Retirados» | Contiene, además, los ítems retirados |
| Plantillas de recurso | Una por clase, «Currículo · <rótulo de la clase>», con `skos:prefLabel` como título y `skos:definition` como descripción |
| Visibilidad | Todo público, también los retirados (los REA que los enlazaban deben poder seguir resolviéndolos) |

Los ítems no llevan `schema:DefinedTerm`: en Omeka un ítem tiene una sola clase. El doble
tipado sigue en el Turtle publicado.

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

URIs: un `id` `<prefijo>:<código>` corresponde a `<base>id/<prefijo>/<código>`, como en el
Turtle. `<base>` es `corpus.uri_base` de `curriculo.json`.

Diferencias deliberadas con el Turtle:

1. **Sin `skos:narrower`.** Omeka muestra los hijos como recursos enlazados y se obtienen
   consultando `skos:broader`; escribirlo duplicaría unas 15.000 aristas.
2. **Enunciados por curso como literales anotados**, no como nodos (en el Turtle son nodos en
   blanco, que Omeka no tiene). `skos:definition` conserva un único valor: el general.
3. **Sin `skos:inScheme` ni `skos:topConceptOf`.** Lo dicen la pertenencia al conjunto y la
   clase `cur:Etapa`.
4. **`skos:changeNote` solo marca la retirada.** Ninguna otra cosa escribe esa propiedad en los
   ítems del currículo, de modo que «sin `skos:changeNote`» (operador `nex` de la búsqueda de
   Omeka) equivale a «vigente». La búsqueda de Omeka, sin módulos añadidos, no puede excluir
   los ítems de un conjunto; esta regla lo permite en una sola consulta.

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

## Cambios en este repositorio

1. **`corpus.uri_base` en `curriculo.json`**, tomado de `config/corpus.yaml` (`rdf.base`).
   Requerido en `esquema/curriculo.schema.json`, con su prueba. Entra en la próxima versión
   publicada; el CHANGELOG lo anota como añadido.
2. **`docs/omeka.md`**: el contrato (estructura, correspondencia, diferencias con el Turtle y
   reglas de sincronización) para quien implemente el módulo o lea los datos en Omeka. La
   sección «Integración con Omeka S» de `docs/modelo.md` lo resume y enlaza; `pendientes.md`
   recoge las decisiones (opción 2, carga de cero).

## ADR-0022 en OERManager

Se escribe en `docs/decisions/0022-curriculo-modelo-cur.md` del repositorio de OERManager.
Sustituye a la ADR-0009 y al punto 2 de la ADR-0006; precisa la ADR-0004. Contenido:

- **Rangos de las propiedades del REA** (se mantienen las propiedades de la ADR-0004):
  `lrmi:educationalLevel` → `cur:Curso`; `schema:about` → `cur:MateriaCurso`; `lrmi:teaches` →
  `cur:SaberBasico` de cualquier nivel; `lrmi:assesses` → `cur:CriterioEvaluacion`. Etapa,
  materia y competencias son nodos de navegación: no se escriben en el REA.
- **Configuración.** Desaparecen `oermanager_type_*` (literal de `dcterms:type` por dimensión)
  y `oermanager_educational_framework`: la dimensión la fija el contrato con la clase. Queda un
  ajuste, el conjunto de ítems del currículo (referencia fija, como pide la ADR-0006). El punto
  1 de la ADR-0006 (ejes temáticos) no cambia.
- **Cascada del re-catalogador.** Todas las consultas, dentro del conjunto del currículo y con
  `skos:changeNote` `nex`: etapas (clase `cur:Etapa`); cursos (`cur:Curso` con `cur:etapa`);
  materias en curso (`cur:MateriaCurso` con `cur:curso`); saberes y criterios (`cur:SaberBasico`
  y `cur:CriterioEvaluacion` con `cur:materiaCurso`), los saberes en árbol por `skos:broader`.
  Las familias de asignaturas, que hoy se agrupan por nombre, son `cur:Materia` (sus cursos,
  por `cur:materia`).
- **Estadísticas.** Cursos por clase `cur:Curso`, materias por `cur:MateriaCurso`, etapa por
  `cur:etapa`.
- **Integridad.** Regla nueva: aviso para los REA que enlazan un término retirado, con el
  sustituto de `dcterms:isReplacedBy` si lo hay.
- **Instancia de desarrollo.** Se carga de cero: se eliminan los ítems de la ADR-0009 y se
  rehace la configuración.

## Fuera de alcance

- El código del módulo de sincronización (repositorio nuevo) y la adaptación del código de
  OERManager.
- Cambiar la base de las URIs (w3id.org).
- Crear ítems para los descriptores operativos y las competencias clave.

## Pruebas

- `corpus.uri_base`: la construcción lo escribe con el valor de `rdf.base` y el esquema JSON
  rechaza un `curriculo.json` sin él.
- El contrato se comprueba con el módulo, en su propia especificación: una carga de la 1.1.1 en
  una instancia limpia debe dar 15.438 ítems y, para una muestra de cada clase, los valores de
  la tabla de correspondencia.
