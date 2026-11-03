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
| CompetenciaEspecifica | `ce:SMATC1` | Materia | De la etapa: el mismo enunciado en todos los cursos |
| BloqueCompetencial | `bc:SMAT02BC1` | Materia | De cada curso. `agrupa` lista sus competencias (dos en Matemáticas); lleva la explicación (`scopeNote`) y los descriptores |
| CriterioEvaluacion | `crit:SMAT02CE1.1` | Su competencia (por el número del código) | `bloque` apunta a su bloque competencial |
| BloqueSaberes | `sb:SMAT02SBI` | Materia | `definition` = título del bloque |
| SaberBasico | `sb:SMAT02SBI.1`, `sb:SMAT02SBI.1.1`… | Bloque o saber superior | Los que tienen hijos son encabezados |

Todos los nodos llevan, además, los atajos `materia`, `curso` y `etapa` cuando aplican,
para poder filtrar sin recorrer la jerarquía.

## Campos

| Campo | Significado | Correspondencia RDF prevista |
|---|---|---|
| `id` | Clave estable; nunca se reutiliza | `dcterms:identifier` |
| `tipo` | Tipo de nodo | clase `cur:<Tipo>` ⊂ `skos:Concept` |
| `notation` | Código oficial | `skos:notation` |
| `prefLabel` | Etiqueta corta (código + inicio del texto) | `skos:prefLabel` |
| `definition` | Texto completo | `skos:definition` |
| `scopeNote` | Explicación del bloque competencial o texto introductorio | `skos:scopeNote` |
| `broader` | Padre inmediato | `skos:broader` |
| `agrupa` | Competencias de un bloque competencial | `cur:agrupa` |
| `bloque` | Bloque competencial de un criterio | `cur:bloqueCompetencial` |
| `descriptores` | Códigos de descriptores operativos | `cur:descriptorOperativo` |
| `materia`, `curso`, `etapa`, `cursos` | Atajos a ancestros | `cur:materia`, `cur:curso`, `cur:etapa` |

## Reglas de identidad

1. Un identificador nunca cambia de significado ni se reutiliza.
2. Corregir una errata mantiene el identificador.
3. Un cambio sustantivo de la norma crea un nodo nuevo y retira el anterior.
