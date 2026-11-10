# Módulo de Omeka S EducationalCurriculum: sincronización del currículo

Fecha: 10-11-2026. Estado: pendiente de revisión. El módulo se desarrolla en el repositorio
`ateeducacion/omeka-s-educationalcurriculum`; esta especificación vive aquí, junto al contrato,
hasta que exista ese repositorio.

## Objetivo

Un módulo de Omeka S que carga en una instancia una versión publicada del currículo cumpliendo
el contrato [`docs/omeka.md`](../../omeka.md). Primer uso: poblar la instancia de desarrollo para
desbloquear la adaptación de OERManager (su TASK-064, ADR-0022). Después, cargar cada versión
nueva, que llega pocas veces al año.

Cierre: la release 1.1.2 cargada en la instancia de desarrollo con el modelo `cur:`; aplicar la
misma versión otra vez no cambia nada; las consultas del contrato (vigentes con `nex`, cursos y
materias por los atajos) devuelven lo esperado.

## Decisiones

- **Módulo aparte**, no dentro de OERManager: OERManager consume el currículo, no lo mantiene
  (ADR-0022, alternativas). Nombre `EducationalCurriculum`, repositorio
  `omeka-s-educationalcurriculum`, a partir de `omeka-s-ModuleTemplate` (Docker con
  `erseco/alpine-omeka-s`, Makefile, PHPUnit, empaquetado). Omeka S ≥ 4.2, como OERManager.
- **Operación desde la administración subiendo los ficheros** de la release
  (`curriculo.json`, `curriculo.json.sha256`, `cur.ttl`): el servidor no necesita salida a
  Internet. Solo `global_admin`.
- **Escritura con la API de Omeka dentro de jobs** (frente a Doctrine/SQL directo, que se salta
  eventos, validación y reindexado y depende del esquema interno, y frente a generar un CSV para
  CSVImport, que no sabe de identidad por conjunto, retirada, errores bloqueantes ni anotaciones
  de valor). Es lento (estimación: 10-30 min la carga inicial), pero corre en segundo plano y
  pocas veces.
- **Lectura del estado actual con consultas Doctrine de solo lectura**: leer 15.000 ítems con sus
  valores por la API es demasiado lento, y leer no tiene los riesgos de escribir.
- **Vocabularios:** `skos` va empaquetado en el módulo y se instala al activarlo; `cur` se crea o
  actualiza en cada aplicación desde el `cur.ttl` subido, con `Omeka\Stdlib\RdfImporter`.
- **Textos de la interfaz en inglés con traducción al español** (`language/es.po`), como
  OERManager.

## Flujo

**Página «Currículo»** (menú lateral de administración): versión cargada (`dcterms:hasVersion`
del conjunto «Currículo LOMLOE de Canarias») y fecha, número de ítems vigentes y retirados,
historial de cargas y botón «Cargar versión».

1. **Subir.** Formulario con los tres ficheros. Comprobaciones inmediatas, sin recorrer Omeka:
   el sha256 coincide con `curriculo.json` (el `.sha256` tiene el formato de `sha256sum`: `<hash>  curriculo.json`); el JSON tiene `corpus.version`, `corpus.uri_base`,
   `corpus.licencia.url` y `nodos`; `cur.ttl` se puede leer; la versión no es anterior a la cargada;
   no hay otra carga analizándose o aplicándose. Si algo falla, se avisa en el formulario y no
   se guarda nada. Si no, los ficheros se guardan en `files/educationalcurriculum/<id>/`, se crea
   la carga y se lanza el análisis.
2. **Analizar (job).** Lee los ítems del conjunto, planifica (nuevos, modificados con las
   propiedades que cambian, retirados, cambios del vocabulario `cur`) y detecta los errores
   bloqueantes. Guarda `informe.json` junto a los ficheros y su huella en la carga. La página de
   la carga muestra «Analizando…» con enlace al job; al terminar, el informe: resumen por tipo
   de nodo y detalle paginado y filtrable (nuevos, modificados, retirados); si hay errores, su
   lista, y «Aplicar» desactivado.
3. **Aplicar (job).** Lo lanza la persona desde el informe. Vuelve a planificar y, si la huella
   no coincide con la del informe aprobado, se detiene sin escribir y la carga vuelve a
   necesitar análisis. Si coincide: vocabulario `cur`, plantillas de recurso, los dos conjuntos,
   primera pasada (ítems con sus literales), segunda pasada (enlaces `resource:item`) y, al
   final, `dcterms:hasVersion`. El progreso queda en el registro del job.
4. **Descartar.** Una carga no aplicada se puede borrar (fila y ficheros). Las aplicadas se
   conservan como historial.

Estados de una carga: `analyzing`, `ready`, `blocked` (con errores), `stale` (necesita análisis),
`applying`, `interrupted`, `applied`, `discarded`.

## Componentes

| Pieza | Responsabilidad |
|---|---|
| `Release\Reader` | Lee y valida los tres ficheros; devuelve `Release` (`version`, `uriBase`, `licencia`, nodos en el orden del corpus) |
| `Mapping\NodeMapper` | Nodo → clase y valores deseados según la tabla de `docs/omeka.md`: por propiedad, lista ordenada de valores normalizados (tipo, literal o URI, etiqueta, idioma `es`, anotación `cur:curso`); los enlaces llevan el **identificador** del destino, no su id interno |
| `Sync\CurrentState` | Lee de Omeka (Doctrine, solo lectura) los ítems del conjunto y los normaliza a la misma forma: identificador → id interno, clase, valores de las propiedades del módulo, pertenencia a «Retirados»; enlaces traducidos a identificadores |
| `Sync\Planner` | Valores deseados + estado actual → `Plan`: nuevos, modificados (propiedad, antes, después), retirados, errores. El `Plan` serializado es el informe; su sha256, la huella |
| `Sync\Writer` | Aplica un `Plan` con la API en lotes de ~100, vaciando el entity manager entre lotes |
| `Job\Analyze`, `Job\Apply` | Orquestan lo anterior; `Apply` comprueba la huella |
| `Entity\CurriculumImport` | Una fila por carga: versión, estado, carpeta, huella, ids de los jobs, persona, fechas |
| Controlador, formulario, vistas | Las páginas del flujo |

`Reader`, `NodeMapper` y `Planner` son PHP puro: se prueban sin Omeka.

**Comparación.** Dos valores son iguales si lo es su forma normalizada. Una propiedad cambia si
cambia su lista de valores, orden incluido (el contrato pide el orden del corpus); entonces se
sustituye entera. Las propiedades que no son del módulo no se leen ni se tocan. Comparar enlaces
por identificador permite planificar la segunda pasada antes de que existan los ítems nuevos.

**Instalar y desinstalar.** Instalar crea la tabla de cargas e instala `skos`. Desinstalar
borra la tabla y la carpeta de ficheros, no los ítems, los conjuntos, las plantillas ni los
vocabularios: son datos que usan otros (los REA).

## Errores

**Al subir** (en el formulario, sin guardar nada): sha256 que no coincide; JSON inválido o sin
los campos de `corpus` o `nodos`; `cur.ttl` ilegible; versión anterior a la cargada; otra carga
en curso.

**Bloqueantes del análisis** (desactivan «Aplicar»; cada uno con el identificador y enlace al
ítem):

- un ítem del conjunto cuyo id no está en el JSON;
- un ítem cuya clase no coincide con el `tipo` del nodo;
- un ítem retirado en Omeka que vuelve a estar vigente en el JSON;
- dos ítems del conjunto con el mismo literal de `dcterms:identifier`;
- un ítem del conjunto sin literal de `dcterms:identifier`;
- un enlace a un id que no está en el JSON;
- un cambio de `cur.ttl` que quita una clase o propiedad usada por los ítems.

**Al aplicar:**

- Huella distinta: se detiene antes de escribir; la carga pasa a `stale`.
- Corte a medias (excepción, reinicio): la carga queda `interrupted` y se puede relanzar; al
  volver a planificar sobre lo ya escrito, termina sin duplicar. `dcterms:hasVersion` sigue en la
  versión anterior hasta el final, como pide el contrato.
- Misma versión ya aplicada: plan vacío; el informe dice «Sin cambios».

## Pruebas

- **Unitarias (PHPUnit, sin Omeka).** `Reader`: sha256, estructura, versión. `NodeMapper`: el
  ejemplo `crit:SMAT01CE1.1` de `docs/omeka.md` como referencia exacta, más un saber anidado,
  una competencia con enunciados por curso, un retirado con sustituto y una materia con varios
  cursos. `Planner`: nuevo, modificado, cambio solo de orden, retirado, sin cambios y cada error
  bloqueante.
- **Fixture.** `curriculo.json` reducido a una materia en un curso con su cadena etapa → curso →
  materia y sus competencias, bloques, criterios y saberes, extraído de la release 1.1.2, con su
  sha256 y `cur.ttl`. Variantes para retirada y errores.
- **Integración (Omeka en Docker).** Carga inicial del fixture; aplicar dos veces sin cambios;
  retirada con sustituto; propiedad añadida a mano que se conserva; aplicación interrumpida y
  relanzada; huella que no coincide.
- **CI.** Lint y PHPUnit en GitHub Actions, como OERManager.
- **A mano.** Carga completa de la 1.1.2 en la instancia de desarrollo, después de quitar el
  grafo de ADR-0009 (ADR-0022 §7); medir el tiempo y anotarlo en el README; comprobar las
  consultas del contrato.

## Fuera de alcance

- Descargar las versiones desde GitHub.
- Sincronizar por línea de comandos.
- Adaptar OERManager (TASK-064).
- Editar el currículo desde Omeka.
- Volver a una versión anterior.
