# Contrato del currículo en Omeka S — plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dejar escrito y publicado el contrato entre `curriculo.json` y los ítems de Omeka S: la base de las URIs dentro de `curriculo.json`, el contrato en `docs/omeka.md` y la ADR-0022 en OERManager.

**Architecture:** Un campo nuevo en los metadatos del corpus (`corpus.uri_base`), exigido por el esquema JSON; un documento de contrato en este repositorio; y una ADR en el repositorio de OERManager que sustituye a su ADR-0009, con sus documentos de gobierno al día. Dos PR, uno por repositorio.

**Tech Stack:** Python 3 (`herramientas/`, pytest, jsonschema), Markdown, `gh`.

**Spec:** `docs/superpowers/specs/2026-11-09-contrato-omeka-design.md`

## Global Constraints

- `corpus.uri_base` toma el valor de `config/corpus.yaml` → `rdf.base` (hoy `https://ateeducacion.github.io/curriculo_lomloe_canarias/`).
- El contrato de `docs/omeka.md` copia sin cambios la estructura, la tabla de correspondencia, las cuatro diferencias con el Turtle y las reglas de sincronización de la especificación.
- OERManager: los ADR son append-only; al sustituir uno se cambia solo su «Estado» a «Reemplazado por ADR-0022». Al registrar una decisión se actualizan juntos backlog, trazabilidad y memoria del proyecto (`AGENTS.md`). IDs `TASK-NNN` correlativos (el último es TASK-063).
- Commits con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; los PR **sin** la línea «Generated with Claude Code».
- `main` está protegida en este repositorio (solo por PR, con `validar` en verde); en OERManager se trabaja en una rama desde `origin/main`.

## Review Focus

- `curriculo.json` de la próxima versión sin `uri_base` porque la construcción no lo escribe: el esquema debe rechazarlo (lo cubre la prueba de la tarea 1).
- Base de `config/corpus.yaml` cambiada en el futuro (w3id.org): `uri_base` debe seguirla sin tocar código (la prueba compara con `rdf.base`, no con un literal).
- Un lector del contrato que no conoce el Turtle: `docs/omeka.md` debe poder leerse solo, con ejemplos de URI y de valores.
- OERManager con la rama de trabajo actual (`hotfix/task-047-…`) sin terminar: la ADR no debe mezclarse con ella (rama nueva desde `origin/main`).
- Documentos de OERManager que citan la ADR-0009 como vigente (RF-014, trazabilidad, memoria): deben remitir a la ADR-0022.

---

### Task 1: `corpus.uri_base` en `curriculo.json`

**Files:**
- Modify: `herramientas/construir.py:102-111` (diccionario `corpus`)
- Modify: `esquema/curriculo.schema.json:11` (`required` y `properties` de `corpus`)
- Test: `tests/test_construir.py`
- Modify: `CHANGELOG.md` (sección «Sin publicar»)

**Interfaces:**
- Produces: `corpus['corpus']['uri_base']: str`, igual a `exportar_rdf.base_uri()`.

- [ ] **Step 1: Escribir las pruebas que fallan** (al final de `tests/test_construir.py`)

```python
def test_uri_base_en_los_metadatos():
    from herramientas.construir import construir
    from herramientas.exportar_rdf import base_uri
    corpus, avisos, _ = construir()
    assert corpus['corpus']['uri_base'] == base_uri()
    assert not [a for a in avisos if a['regla'] == 'esquema']


def test_esquema_exige_uri_base():
    corpus = {'corpus': {'marco': 'm', 'ambito': 'a', 'version': '0', 'base': {}, 'normas': []}, 'nodos': []}
    assert any(a['regla'] == 'esquema' and 'uri_base' in a['detalle'] for a in validar(corpus, {}))
```

- [ ] **Step 2: Comprobar que fallan**

Run: `.venv/bin/python -m pytest -q tests/test_construir.py -k uri_base`
Expected: 2 failed (`KeyError: 'uri_base'` y la aserción del esquema).

- [ ] **Step 3: Implementar**

En `herramientas/construir.py`, dentro de `'corpus': {...}`, tras `'licencia': conf.get('licencia'),`:

```python
            'uri_base': conf['rdf']['base'],
```

En `esquema/curriculo.schema.json`:

```json
      "required": ["marco", "ambito", "version", "base", "normas", "uri_base"],
```

y en `properties` de `corpus`, tras `"licencia"`:

```json
        "uri_base": {"type": "string", "pattern": "^https?://.+/$"},
```

En `CHANGELOG.md`, bajo `## [Sin publicar]`, una sección `### Añadido` (antes de `### Cambiado`):

```markdown
### Añadido
- `curriculo.json` lleva la base de las URIs (`corpus.uri_base`), para que quien lo cargue en Omeka S u otro sistema construya las mismas URIs que el Turtle (contrato en `docs/omeka.md`).
```

- [ ] **Step 4: Comprobar que pasan, y toda la batería y la construcción**

Run: `.venv/bin/python -m pytest -q && .venv/bin/python -m herramientas.construir --comprobar --dist >/dev/null && .venv/bin/python -c "import json; print(json.load(open('dist/curriculo.json'))['corpus']['uri_base'])"`
Expected: todas pasan; imprime `https://ateeducacion.github.io/curriculo_lomloe_canarias/`.

- [ ] **Step 5: Commit**

```bash
git add herramientas/construir.py esquema/curriculo.schema.json tests/test_construir.py CHANGELOG.md
git commit -m "curriculo.json lleva la base de las URIs (corpus.uri_base)"
```

### Task 2: el contrato en `docs/omeka.md`

**Files:**
- Create: `docs/omeka.md`
- Modify: `docs/modelo.md` (sección «Integración con Omeka S»)
- Modify: `docs/pendientes.md` (sección «Integración con Omeka S»)
- Modify: `docs/backlog.md` (línea «Fuera de este repositorio…»)
- Modify: `docs/superpowers/specs/2026-11-09-contrato-omeka-design.md` (línea de estado)

**Interfaces:**
- Consumes: `corpus.uri_base` (tarea 1).

- [ ] **Step 1: Escribir `docs/omeka.md`** con estas secciones, tomando el texto de la especificación:
  1. Introducción: para qué sirve, quién lo cumple (módulo de sincronización) y quién lo lee (OERManager), y que la referencia es la versión publicada de `curriculo.json`.
  2. «Estructura» (tabla de la especificación).
  3. «Correspondencia de campos» (tabla, regla de URIs con `corpus.uri_base` y un ejemplo completo de ítem: el criterio `crit:SMAT01CE1.1` con sus valores, sacados de `dist/curriculo.json`).
  4. «Diferencias con el Turtle» (las cuatro).
  5. «Sincronización» (las reglas).
  6. «Consumidores»: OERManager, con los rangos de las propiedades del REA (`lrmi:educationalLevel` → `cur:Curso`, `schema:about` → `cur:MateriaCurso`, `lrmi:teaches` → `cur:SaberBasico`, `lrmi:assesses` → `cur:CriterioEvaluacion`), la consulta de vigentes (`skos:changeNote` `nex`) y el enlace a su ADR-0022.

- [ ] **Step 2: Resumir y enlazar en `docs/modelo.md`.** Sustituir el párrafo de «Integración con Omeka S» por:

```markdown
Omeka S importa vocabularios (clases y propiedades) desde Turtle, pero no ítems: el Turtle es
para publicar los datos enlazados y `cur.ttl` para importar el vocabulario. Los nodos se cargan
como ítems con un módulo de sincronización que sigue el contrato de [`omeka.md`](omeka.md):
cada nodo es un ítem de clase `cur:<Tipo>` con las mismas propiedades SKOS y `cur:` que el
Turtle, localizado por `dcterms:identifier` y actualizado sin cambiar su id interno; los
retirados no se borran (decisiones del 05-11-2026 y del 09-11-2026).
```

- [ ] **Step 3: Actualizar `docs/pendientes.md`** («Integración con Omeka S»): el módulo de sincronización sigue pendiente, ahora con contrato (`omeka.md`); la instancia de desarrollo se carga de cero (decisión del 09-11-2026: no hay REA en producción); OERManager se adapta según su ADR-0022.

- [ ] **Step 4: Actualizar `docs/backlog.md`**: la línea «Fuera de este repositorio: …» añade que el contrato está fijado en `omeka.md` (09-11-2026) y que la adaptación de OERManager sigue su ADR-0022.

- [ ] **Step 5: Marcar la especificación** como «Estado: aprobado; implementado el 09-11-2026 (plan en `docs/superpowers/plans/2026-11-09-contrato-omeka.md`)».

- [ ] **Step 6: Comprobar enlaces**

Run: `grep -o '](\([^)]*\.md\)[^)]*)' docs/omeka.md docs/modelo.md | sort -u` y comprobar que cada fichero existe.
Expected: todos existen.

- [ ] **Step 7: Commit**

```bash
git add docs/omeka.md docs/modelo.md docs/pendientes.md docs/backlog.md docs/superpowers
git commit -m "Contrato del currículo en Omeka S (docs/omeka.md)"
```

### Task 3: ADR-0022 en OERManager

**Files** (repositorio `../omeka-s-OERManager`, rama `adr-0022-curriculo-cur` desde `origin/main`):
- Create: `docs/decisions/0022-curriculo-modelo-cur.md`
- Modify: `docs/decisions/0009-grafo-curricular-lomloe.md` (solo «Estado»)
- Modify: `docs/decisions/0006-raiz-arboles-rdf-config.md` (solo «Estado»: punto 2 reemplazado)
- Modify: `docs/backlog.md` (TASK-064 nueva, pendiente)
- Modify: `docs/traceability.md` (fila de RF-014 / re-catalogación curricular)
- Modify: `docs/project-memory.md` («Decisiones ya tomadas»)

- [ ] **Step 1: Rama limpia**

Run: `git -C ../omeka-s-OERManager fetch -q && git -C ../omeka-s-OERManager switch -c adr-0022-curriculo-cur origin/main`
Expected: rama nueva sin cambios.

- [ ] **Step 2: Escribir la ADR-0022** con la plantilla `0000-template.md`: Estado «Aceptado (2026-11-09)»; Contexto (el currículo pasa a publicarse desde `curriculo_lomloe_canarias` con modelo SKOS/`cur:`; la ADR-0009 describía la primera carga; no hay REA en producción); Alternativas (escribir con la forma de la ADR-0009; añadir aristas schema.org; adoptar el modelo `cur:`); Decisión (los puntos de la sección «ADR-0022 en OERManager» de la especificación, con el contrato enlazado por URL de GitHub a `docs/omeka.md`); Consecuencias (cambia `CurriculumSearch`, `CurriculumOutline`, `RecatalogService`, `CurricularPairs`, `ConfigForm` y el clasificador de la ADR-0010: las familias son `cur:Materia` y la descripción de las hojas es `skos:definition`; se elimina la configuración por `dcterms:type`; adaptación en TASK-064); Fuentes (especificación y contrato).

- [ ] **Step 3: Estados de las ADR sustituidas.** En la 0009, «## Estado» pasa a `Reemplazado por ADR-0022 (2026-11-09)`. En la 0006, se añade bajo «## Estado»: `Punto 2 (raíces curriculares por lrmi:educationalFramework) reemplazado por ADR-0022 (2026-11-09); el punto 1 sigue vigente.`

- [ ] **Step 4: Gobierno.** Backlog: TASK-064 «Adaptar OERManager al modelo `cur:` del currículo (ADR-0022)», estado `pendiente`, enlazada a RF-014, ADR-0022, ADR-0004, ADR-0010, bloqueada por «módulo de sincronización del currículo (carga en la instancia)». Trazabilidad: en la fila de re-catalogación curricular, añadir ADR-0022 (sustituye a la ADR-0009) y TASK-064. Memoria: entrada «ADR-0022 (2026-11-09)» en «Decisiones ya tomadas», y nota en la de la ADR-0009 de que está reemplazada.

- [ ] **Step 5: Comprobar** que ningún documento de gobierno sigue presentando la ADR-0009 como vigente sin la nota.

Run: `grep -n "ADR-0009" ../omeka-s-OERManager/docs/project-memory.md ../omeka-s-OERManager/docs/traceability.md | head`
Expected: cada mención está acompañada de la ADR-0022 o es histórica (tareas hechas).

- [ ] **Step 6: Commit, push y PR en OERManager**

```bash
git -C ../omeka-s-OERManager add docs
git -C ../omeka-s-OERManager commit -m "docs: ADR-0022, el currículo en Omeka con el modelo cur: (sustituye a ADR-0009)"
git -C ../omeka-s-OERManager push -u origin adr-0022-curriculo-cur
gh pr create -R ateeducacion/omeka-s-OERManager --base main --head adr-0022-curriculo-cur --title "ADR-0022: currículo con el modelo cur: (sustituye a ADR-0009)" --body "<resumen>"
```

### Task 4: PR en este repositorio

- [ ] **Step 1:** `.venv/bin/python -m pytest -q` y `.venv/bin/python -m herramientas.contrastar --estricto >/dev/null` en verde.
- [ ] **Step 2:** `git push -u origin contrato-omeka` y `gh pr create` con resumen y enlace al PR de OERManager; sin la línea «Generated with Claude Code».
