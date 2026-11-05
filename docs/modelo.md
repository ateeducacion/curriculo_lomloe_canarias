# Modelo de datos

El corpus es un sistema de organización del conocimiento: cada nodo es un `skos:Concept`
de una subclase propia que indica su tipo. El JSON usa nombres de campo cercanos a SKOS
para que la conversión a RDF sea directa.

## Tipos de nodo

| Tipo | Identificador | Padre (`broader`) | Notas |
|---|---|---|---|
| Etapa | `etapa:INF`, `etapa:PRI`, `etapa:ESO`, `etapa:BAC` | — | |
| Curso | `curso:S01` (letra de etapa + n.º) | Etapa | |
| Materia | `materia:SMAT` (letra + código) | — | Una por etapa, común a todos sus cursos; `cursos` lista dónde se imparte |
| MateriaCurso | `asig:SMAT01` (materia + n.º de curso) | Materia | La materia en un curso (Matemáticas de 1.º ESO): es el nodo con el que se cataloga un recurso. Se genera para cada curso de la materia |
| CompetenciaEspecifica | `ce:SMATC1` | Materia | De la etapa. Si el enunciado cambia en algún curso, `enunciados_curso` guarda el de ese curso |
| BloqueCompetencial | `bc:SMAT02BC1` | MateriaCurso | De cada curso. `agrupa` lista sus competencias (dos en Matemáticas); lleva la explicación (`scopeNote`) y los descriptores |
| CriterioEvaluacion | `crit:SMAT02CE1.1` | Su competencia (por el número del código) | `bloque` apunta a su bloque competencial |
| BloqueSaberes | `sb:SMAT02SBI` | MateriaCurso | `definition` = título del bloque |
| SaberBasico | `sb:SMAT02SBI.1`, `sb:SMAT02SBI.1.1`… | Bloque o saber superior | Los que tienen hijos son encabezados |

Todos los nodos llevan, además, los atajos `materia`, `materia_curso`, `curso` y `etapa`
cuando aplican, para poder filtrar sin recorrer la jerarquía (p. ej., todos los saberes de
Matemáticas de 1.º ESO son los que tienen `materia_curso: asig:SMAT01`).

## Campos

| Campo | Significado | Correspondencia RDF prevista |
|---|---|---|
| `id` | Clave estable; nunca se reutiliza | `dcterms:identifier` |
| `tipo` | Tipo de nodo | clase `cur:<Tipo>` ⊂ `skos:Concept` |
| `notation` | Código oficial | `skos:notation` |
| `prefLabel` | Etiqueta corta (código + inicio del texto) | `skos:prefLabel` |
| `definition` | Texto completo | `skos:definition` |
| `enunciados_curso` | Competencias: enunciado de los cursos en que difiere de `definition` (`{curso:P05: '…'}`) | `cur:enunciadoEnCurso` |
| `scopeNote` | Explicación del bloque competencial o texto introductorio | `skos:scopeNote` |
| `broader` | Padre inmediato | `skos:broader` |
| `agrupa` | Competencias de un bloque competencial | `cur:agrupa` |
| `bloque` | Bloque competencial de un criterio | `cur:bloqueCompetencial` |
| `descriptores` | Códigos de descriptores operativos | `cur:descriptorOperativo` |
| `materia`, `materia_curso`, `curso`, `etapa`, `cursos` | Atajos a ancestros | `cur:materia`, `cur:materiaCurso`, `cur:curso`, `cur:etapa` |
| `obsoleto`, `sustituido_por` | Nodo retirado y, si lo hay, el que lo sustituye | `owl:deprecated`, `dcterms:isReplacedBy` |

## Reglas de identidad

1. Un identificador nunca cambia de significado ni se reutiliza.
2. Corregir una errata mantiene el identificador.
3. Un cambio sustantivo de la norma crea un nodo nuevo y retira el anterior.
4. Un nodo retirado no se borra: queda con `obsoleto: true` (corrección con `accion: retirar`
   y, si procede, `sustituido_por`). Así no se rompen los enlaces de quien lo usaba. Ningún
   nodo vigente puede colgar de uno retirado. `accion: eliminar` solo se usa antes de la 1.0,
   para limpiar nodos que nunca se publicaron.

## Datos enlazados (RDF)

`python -m herramientas.exportar_rdf` (y `construir --dist`) genera `curriculo.ttl`: el corpus
en SKOS, en Turtle. Las clases y propiedades propias están en [`vocabulario/cur.ttl`](../vocabulario/cur.ttl),
que se puede importar en Omeka S como vocabulario (prefijo `cur`).

- **URIs**: `<base>id/<prefijo>/<código>`, p. ej.
  `https://ateeducacion.github.io/curriculo_lomloe_canarias/id/crit/SMAT01CE1.1`. La base está en
  `config/corpus.yaml` (`rdf.base`); es provisional en GitHub Pages y se valorará w3id.org. Las
  URIs no llevan versión: la versión es del esquema de conceptos (`owl:versionInfo`).
- **Cada nodo** es `skos:Concept`, de su clase `cur:<Tipo>` (subclase de `skos:Concept`) y
  `schema:DefinedTerm`, en el esquema `<base>id/curriculo` (`skos:inScheme` y
  `schema:inDefinedTermSet`). El doble tipado con schema.org permite enlazarlo desde recursos
  descritos con LRMI (`lrmi:teaches`, `lrmi:assesses`).
- **Campos**: los de la tabla de arriba. `broader` y `narrower` se escriben los dos (los
  consumidores no suelen inferir). Los enunciados por curso son nodos `cur:EnunciadoEnCurso`
  con `cur:curso` y `skos:definition`.
- **Descriptores operativos**: esquema `<base>id/descriptores`, generado desde
  `config/descriptores.csv`. Cada descriptor (`<base>id/descriptor/ESO/CCL1`) cuelga de su
  competencia clave (`<base>id/competencia-clave/CCL`) y los criterios y bloques los enlazan con
  `cur:descriptorOperativo`.
- **Validación**: [`esquema/curriculo.shacl.ttl`](../esquema/curriculo.shacl.ttl) comprueba lo que
  el esquema JSON no puede, que cada enlace apunta a un nodo de la clase correcta. La CI valida
  el Turtle que se publica (`exportar_rdf --ttl dist/curriculo.ttl --validar`).

### Integración con Omeka S

Omeka S importa vocabularios (clases y propiedades) desde Turtle, pero no ítems: el Turtle es
para publicar los datos enlazados y `cur.ttl` para importar el vocabulario. La carga de los
nodos como ítems la hará un módulo que lee `curriculo.json` de una versión fijada, comprueba su
sha256, localiza cada ítem por `dcterms:identifier` (el `id` del corpus) y lo actualiza sin
cambiar su identificador interno, para no romper los enlaces de los recursos; crea los nuevos y
marca los retirados (decisiones del 05-11-2026).
