# Sitio para personas — plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir las fichas del sitio de GitHub Pages en un visor del currículo para asesores y docentes, con navegación por etapa, curso y materia, pestañas en la materia en curso y un buscador estático.

**Architecture:** `herramientas/sitio.py` pasa a ser un paquete. Una capa de lectura (`datos.py`) indexa una vez el grafo (`curriculo.ttl`) y responde a «hijos», «nodos de tipo X con cur:prop = Y» y «ruta de navegación». Las páginas (`paginas.py`) se escriben con f-strings sobre una plantilla común (`plantilla.py`) que enlaza `recursos/estilo.css` y `recursos/buscar.js`. El índice de búsqueda (`indice.py`) es un JSON que MiniSearch 7.2.0 (incluido en el sitio) carga al enfocar el buscador.

**Tech Stack:** Python 3 + rdflib (ya en el proyecto), pytest, HTML/CSS, JavaScript sin dependencias salvo MiniSearch 7.2.0 (MIT).

**Spec:** `docs/superpowers/specs/2026-11-09-sitio-para-personas-design.md`

## Global Constraints

- Las URIs, los `index.ttl`, `<link rel="alternate" type="text/turtle" href="index.ttl">` y `def/cur` no cambian.
- Interfaz pública sin cambios: `generar(g, base, destino, vocabulario=VOCABULARIO) -> int`, `ruta(base, s)`, `main(argv)`; `python -m herramientas.sitio` funciona igual.
- Ninguna página lleva `<style>`; todas enlazan `<base>recursos/estilo.css`.
- Sin dependencias Python nuevas; MiniSearch 7.2.0 copiado en `herramientas/sitio/recursos/minisearch.js` con su licencia (`minisearch.LICENSE`). La especificación lo llamaba `minisearch.min.js`; el build UMD publicado no está minificado y se nombra `minisearch.js`.
- Rótulos para personas, nunca nombres de propiedades RDF, en las páginas del currículo.
- Sin marca ni logotipos del Gobierno de Canarias.
- Commits con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; PR sin «Generated with Claude Code».

## Review Focus

- Nodos retirados: deben seguir teniendo ficha y ser alcanzables desde la portada (en el árbol de saberes, marcados como retirados), y no deben entrar en `buscar.json`. Pruebas en las tareas 3 y 4.
- Textos con `<`, `&` o comillas en definiciones y códigos: escapados en HTML y válidos en el JSON. Prueba en la tarea 3 (HTML) y en la 4 (JSON).
- Materias en curso sin criterios o sin saberes (hay materias recién incorporadas): la página se genera con la pestaña vacía y un aviso, sin fallar. Prueba en la tarea 3.
- Competencias con enunciado distinto en un curso: en la materia en curso se muestra el enunciado de ese curso, no el general. Prueba en la tarea 3.
- Base distinta para la vista previa local (`http://localhost:8000/`): recursos e índice se enlazan con la base recibida, no con la de `config/corpus.yaml`. Prueba en la tarea 1.

---

### Task 1: paquete, plantilla y recursos

**Files:**
- Delete: `herramientas/sitio.py`
- Create: `herramientas/sitio/__init__.py` (interfaz pública, `generar`, `ruta`, `main`; contenido del antiguo `sitio.py` salvo lo que pasa a `plantilla.py`)
- Create: `herramientas/sitio/__main__.py` (`from . import main; sys.exit(main())`)
- Create: `herramientas/sitio/plantilla.py`
- Create: `herramientas/sitio/recursos/estilo.css`, `herramientas/sitio/recursos/buscar.js` (vacío con cabecera, se completa en la tarea 4), `herramientas/sitio/recursos/minisearch.js`, `herramientas/sitio/recursos/minisearch.LICENSE`
- Modify: `.gitignore` (añadir `.superpowers/`)
- Test: `tests/test_sitio.py`

**Interfaces:**
- Produces: `plantilla.pagina(titulo: str, cuerpo: str, base: str, migas: list[tuple[str|None, str]] = (), cabecera: str = '', version: str|None = None) -> str` — documento completo: `<head>` con `<link rel="stylesheet" href="{base}recursos/estilo.css">` y `<script defer src="{base}recursos/buscar.js" data-base="{base}">`; cabecera con el nombre del sitio y un `<form action="{base}buscar/" role="search">` con `<input name="q" type="search">`; `<nav class="migas">` si hay migas (pares URL/rótulo, el último sin enlace); `<main>`; pie con versión, licencia y enlaces a `{base}id/curriculo`, `{base}id/descriptores`, `{base}def/cur` y el repositorio.
- Produces: `plantilla.e(x) -> str` (escape de `str(x)`).
- Produces: `generar` copia `recursos/` a `destino/recursos/`.

- [ ] **Step 1: Pruebas que fallan** (añadir a `tests/test_sitio.py`)

```python
def test_sin_css_en_linea_y_recursos(web):
    _, destino = web
    for f in destino.rglob('index.html'):
        texto = f.read_text(encoding='utf-8')
        assert '<style' not in texto, f
        assert f'href="{BASE}recursos/estilo.css"' in texto, f
    for r in ('estilo.css', 'buscar.js', 'minisearch.js', 'minisearch.LICENSE'):
        assert (destino / 'recursos' / r).is_file()


def test_base_de_vista_previa(tmp_path):
    otra = 'http://localhost:8000/'
    g = Graph()
    for s, p, o in _grafo():
        cambia = lambda x: URIRef(str(x).replace(BASE, otra)) if isinstance(x, URIRef) else x
        g.add((cambia(s), cambia(p), cambia(o)))
    sitio.generar(g, otra, tmp_path / 's')
    portada = (tmp_path / 's/index.html').read_text(encoding='utf-8')
    assert f'{otra}recursos/estilo.css' in portada and f'action="{otra}buscar/"' in portada
```

- [ ] **Step 2:** `.venv/bin/python -m pytest -q tests/test_sitio.py` → las 2 nuevas fallan.
- [ ] **Step 3:** Crear el paquete moviendo el código (`git mv herramientas/sitio.py herramientas/sitio/__init__.py`), sacar `_pagina`/`CSS` a `plantilla.pagina`, copiar los recursos (`minisearch.js` = `package/dist/umd/index.js` de `minisearch@7.2.0`, con una línea de cabecera `/*! MiniSearch 7.2.0 — MIT — https://github.com/lucaong/minisearch */`), y en `generar` copiar `Path(__file__).parent / 'recursos'` a `destino / 'recursos'`. CSS en `estilo.css`: variables de color en `:root`, ancho máximo 60rem, cabecera con buscador, migas, etiquetas de tipo (`.tipo-criterio`, `.tipo-saber`…), chips (`.chip`), pestañas (`.pestanas`, `[role=tab]`), árbol (`ul.arbol`), `details.tecnico`, `.aviso`, `.retirado` (tachado gris), sugerencias (`.sugerencias`), resultados y filtros; foco visible; legible en móvil.
- [ ] **Step 4:** `.venv/bin/python -m pytest -q` → todo pasa (las 17 del sitio siguen valiendo).
- [ ] **Step 5: Commit** — «Sitio: paquete, plantilla común y recursos (CSS y MiniSearch 7.2.0)».

### Task 2: lectura del grafo para navegar (`datos.py`)

**Files:**
- Create: `herramientas/sitio/datos.py`
- Test: `tests/test_sitio.py`

**Interfaces:**
- Produces: `class Curriculo(g, base)` con:
  - `tipo(u) -> str|None` — nombre local de su clase `cur:` (`'CriterioEvaluacion'`…).
  - `codigo(u) -> str` (`skos:notation`), `etiqueta(u) -> str` (`skos:prefLabel`), `texto(u) -> str|None` (`skos:definition`), `nota(u) -> str|None` (`skos:scopeNote`).
  - `retirado(u) -> bool`, `sustituto(u) -> URIRef|None`.
  - `padre(u) -> URIRef|None` (`skos:broader`), `hijos(u, tipo=None) -> list[URIRef]` (inversa de `skos:broader`, orden natural por código).
  - `con(prop: str, valor: URIRef, tipo: str) -> list[URIRef]` — nodos de clase `cur:tipo` cuyo `cur:prop` es `valor`, orden natural (índice construido una vez).
  - `atajo(u, prop: str) -> URIRef|None` — valor de `cur:prop` (`etapa`, `curso`, `materia`, `materiaCurso`).
  - `numero(u) -> str` — número corto para listas: criterio `SMAT01CE1.1`→`1.1`, competencia `SMATC1`→`C1`, bloque `SMAT01BC1`→`BC1`, saber `SMAT01SBI.2.1`→`2.1`, bloque de saberes `SMAT01SBI`→`I`.
  - `enunciado(ce, curso) -> str` — el de ese curso si difiere, si no `texto(ce)`.
  - `migas(u) -> list[tuple[str|None, str]]` — Inicio › etapa › curso › materia en curso › (competencia | bloque de saberes › apartados) según el tipo; la materia de la etapa y la competencia cuelgan de la etapa.
  - `descriptores(u) -> list[tuple[URIRef, str, str]]` — (URI, código, nombre de la competencia clave).
  - `ROTULOS: dict[str, str]` — tipo → rótulo para personas (`'CriterioEvaluacion': 'Criterio de evaluación'`, …).

- [ ] **Step 1: Pruebas que fallan**

```python
from herramientas.sitio.datos import Curriculo


def _u(x):
    return URIRef(BASE + x)


def test_curriculo_navegacion():
    c = Curriculo(_grafo(), BASE)
    assert c.tipo(_u('id/crit/SMAT01CE1.1')) == 'CriterioEvaluacion'
    assert c.numero(_u('id/crit/SMAT01CE1.1')) == '1.1' and c.numero(_u('id/ce/SMATC1')) == 'C1'
    assert c.numero(_u('id/sb/SMAT01SBI')) == 'I' and c.numero(_u('id/sb/SMAT01SBI.1')) == '1'
    assert c.con('materiaCurso', _u('id/asig/SMAT01'), 'CriterioEvaluacion') == [_u('id/crit/SMAT01CE1.1')]
    assert c.hijos(_u('id/sb/SMAT01SBI')) == [_u('id/sb/SMAT01SBI.1'), _u('id/sb/SMAT01SBI.2')]
    assert c.retirado(_u('id/sb/SMAT01SBI.2')) and c.sustituto(_u('id/sb/SMAT01SBI.2')) == _u('id/sb/SMAT01SBI.1')
    assert c.enunciado(_u('id/ce/SMATC1'), _u('id/curso/S01')) == 'Resolver problemas sencillos.'
    assert [u for u, _ in c.migas(_u('id/sb/SMAT01SBI.1'))] == [
        BASE, str(_u('id/etapa/ESO')), str(_u('id/curso/S01')), str(_u('id/asig/SMAT01')), str(_u('id/sb/SMAT01SBI')), None]
    assert [(str(u), cod) for u, cod, _ in c.descriptores(_u('id/crit/SMAT01CE1.1'))] == [
        (BASE + 'id/descriptor/ESO/STEM1', 'STEM1')]
```

- [ ] **Step 2:** la prueba falla (`ModuleNotFoundError`).
- [ ] **Step 3:** implementar `Curriculo` construyendo en `__init__` tres diccionarios: tipo por sujeto, hijos por padre (`skos:broader`) y `(prop, valor, tipo) → [nodos]` para `cur:etapa`, `cur:curso`, `cur:materia`, `cur:materiaCurso`, `cur:bloqueCompetencial`, `cur:agrupa` (este último indexado como `('agrupada_por', ce, 'BloqueCompetencial')`). Orden natural con la clave `_clave_natural` del paquete.
- [ ] **Step 4:** pasa toda la batería.
- [ ] **Step 5: Commit** — «Sitio: lectura del grafo para navegar».

### Task 3: páginas para personas (`paginas.py`)

**Files:**
- Create: `herramientas/sitio/paginas.py`
- Modify: `herramientas/sitio/__init__.py` (`generar` elige la página según `Curriculo.tipo`; los demás sujetos, esquemas, descriptores y competencias clave, usan la ficha genérica actual sobre la plantilla nueva; el vocabulario y la portada, también con la plantilla)
- Test: `tests/test_sitio.py`

**Interfaces:**
- Consumes: `Curriculo` (tarea 2), `plantilla.pagina`, `plantilla.e`.
- Produces: `portada(c, version)`, `etapa(c, u)`, `curso(c, u)`, `materia(c, u)`, `materia_curso(c, u)`, `ficha(c, u)` (competencia, bloque competencial, criterio, bloque de saberes, saber) → `str` (cuerpo HTML para `plantilla.pagina`), y `PAGINAS: dict[tipo, función]`.
- Contrato HTML que usan las pruebas y `buscar.js`: pestañas `<div class="pestanas" role="tablist" hidden>` con `<button role="tab" aria-controls="p-…">` y paneles `<section class="panel" id="p-competencias|p-saberes|p-bloques"><h2>…</h2>…`; árbol de saberes `<ul class="arbol">`; descriptores `<a class="chip" href="…" title="…">CCL1</a>`; retirado `<p class="aviso">` y en listas `class="retirado"`; datos técnicos `<details class="tecnico">` con la URI, el enlace `index.ttl` y el identificador.

- [ ] **Step 1: Pruebas que fallan**

```python
def _pagina(destino, ruta):
    return (destino / ruta / 'index.html').read_text(encoding='utf-8')


def test_materia_en_curso_con_pestanas(web):
    _, destino = web
    t = _pagina(destino, 'id/asig/SMAT01')
    assert 'role="tablist"' in t and 'id="p-competencias"' in t and 'id="p-saberes"' in t and 'id="p-bloques"' in t
    comp = t[t.index('id="p-competencias"'):t.index('id="p-saberes"')]
    # el criterio va bajo su competencia, con el enunciado del curso y sus descriptores
    assert comp.index('SMATC1') < comp.index('SMAT01CE1.1')
    assert 'Resolver problemas sencillos.' in comp and 'class="chip"' in comp
    saberes = t[t.index('id="p-saberes"'):t.index('id="p-bloques"')]
    assert 'class="arbol"' in saberes and 'Sentido numérico' in saberes and 'Conteo.' in saberes
    assert 'class="retirado"' in saberes   # el retirado sigue enlazado, marcado


def test_ficha_criterio_para_personas(web):
    _, destino = web
    t = _pagina(destino, 'id/crit/SMAT01CE1.1')
    assert 'Criterio de evaluación' in t and 'Interpretar problemas.' in t
    for rotulo in ('Competencia específica', 'Bloque competencial', 'Descriptores operativos'):
        assert rotulo in t
    for tecnico in ('Superior', 'Esquema', 'bloque competencial</dt>'):
        assert tecnico not in t
    assert '<details class="tecnico">' in t and 'href="index.ttl"' in t
    assert '<nav class="migas"' in t and f'href="{BASE}id/asig/SMAT01"' in t


def test_portada_etapa_y_curso(web):
    _, destino = web
    portada = (destino / 'index.html').read_text(encoding='utf-8')
    assert 'role="search"' in portada and f'href="{BASE}id/etapa/ESO"' in portada
    assert f'href="{BASE}id/curso/S01"' in _pagina(destino, 'id/etapa/ESO')
    curso = _pagina(destino, 'id/curso/S01')
    assert f'href="{BASE}id/asig/SMAT01"' in curso and '1 criterio' in curso


def test_materia_en_curso_vacia(tmp_path):
    g = _grafo()
    asig = URIRef(BASE + 'id/asig/SMAT02')
    cur = exportar_rdf.espacio_cur()
    g.add((asig, RDF.type, cur.MateriaCurso))
    g.add((asig, SKOS.notation, Literal('SMAT02')))
    g.add((asig, SKOS.prefLabel, Literal('Matemáticas · 2º ESO', lang='es')))
    g.add((asig, cur.materia, URIRef(BASE + 'id/materia/SMAT')))
    g.add((asig, cur.curso, URIRef(BASE + 'id/curso/S01')))
    g.add((asig, cur.etapa, URIRef(BASE + 'id/etapa/ESO')))
    sitio.generar(g, BASE, tmp_path / 's')
    t = (tmp_path / 's/id/asig/SMAT02/index.html').read_text(encoding='utf-8')
    assert 'Sin criterios en este curso' in t and 'Sin saberes en este curso' in t


def test_ficha_retirado_con_sustituto(web):
    _, destino = web
    t = _pagina(destino, 'id/sb/SMAT01SBI.2')
    assert 'class="aviso"' in t and f'href="{BASE}id/sb/SMAT01SBI.1"' in t
```

Las pruebas existentes `test_ficha_retirado`, `test_ficha_enlaza_turtle_y_escapa`, `test_nombre_sin_notacion_repetida`, `test_orden_natural`, `test_desde_la_portada_se_llega_a_todo` y `test_etapa_y_curso_enlazan_el_nivel_siguiente` deben seguir pasando; si alguna comprueba un detalle de la ficha antigua que la nueva expresa de otra forma (p. ej. el `<h1>` exacto), se adapta a la ficha nueva manteniendo lo que protege (notación no repetida, orden natural, escapado).

- [ ] **Step 2:** fallan las nuevas.
- [ ] **Step 3:** implementar `paginas.py` según la especificación (tabla «Páginas» y párrafo de lo relacionado). Las listas se ordenan con orden natural; los textos pasan siempre por `e()`; las pestañas sin contenido muestran «Sin criterios en este curso» / «Sin saberes en este curso» / «Sin bloques competenciales en este curso». La portada lleva el buscador grande (`<form class="buscador-portada" action="{base}buscar/" role="search">`), ejemplos que enlazan a `buscar/?q=…` y las etapas con sus cursos.
- [ ] **Step 4:** pasa toda la batería; generar el sitio real y medir: `time .venv/bin/python -m herramientas.sitio --ttl dist/curriculo.ttl --destino dist/sitio`.
- [ ] **Step 5: Commit** — «Sitio: páginas para personas (portada, etapa, curso, materia, materia en curso con pestañas y fichas)».

### Task 4: buscador (`indice.py`, `buscar/`, `buscar.js`)

**Files:**
- Create: `herramientas/sitio/indice.py`
- Modify: `herramientas/sitio/__init__.py` (escribe `buscar.json` y `buscar/index.html`)
- Modify: `herramientas/sitio/paginas.py` (página `buscar`)
- Modify: `herramientas/sitio/recursos/buscar.js`
- Test: `tests/test_sitio.py`

**Interfaces:**
- Consumes: `Curriculo` (`tipo`, `retirado`, `codigo`, `texto`, `etiqueta`, `migas`, `atajo`, `ROTULOS`).
- Produces: `indice.entradas(c) -> list[dict]` con claves `u, c, t, k, r, e, m` (todas `str`); `TIPOS_INDEXADOS = ('Materia', 'MateriaCurso', 'CompetenciaEspecifica', 'BloqueCompetencial', 'CriterioEvaluacion', 'BloqueSaberes', 'SaberBasico')`. `e` es el código de la etapa (`ESO`), `m` la etiqueta de la materia de la etapa, `r` las migas sin «Inicio» unidas con « · ».
- Contrato de `buscar/index.html`: `<form id="filtros">` con `<select name="e">`, `<select name="k">`, `<select name="m">` (opciones generadas desde el índice) y `<ol id="resultados">`, `<button id="mas" hidden>`.

- [ ] **Step 1: Pruebas que fallan**

```python
def test_indice_de_busqueda(web):
    g, destino = web
    datos = json.loads((destino / 'buscar.json').read_text(encoding='utf-8'))
    por_url = {d['u']: d for d in datos}
    crit = por_url[BASE + 'id/crit/SMAT01CE1.1']
    assert crit == {'u': BASE + 'id/crit/SMAT01CE1.1', 'c': 'SMAT01CE1.1', 't': 'Interpretar problemas.',
                    'k': 'Criterio de evaluación', 'r': crit['r'], 'e': 'ESO', 'm': crit['m']}
    assert 'Matemáticas' in crit['r'] or 'SMAT' in crit['r']
    assert BASE + 'id/sb/SMAT01SBI.2' not in por_url          # retirado fuera
    assert BASE + 'id/etapa/ESO' not in por_url               # etapas y cursos fuera
    assert {d['k'] for d in datos} <= set(sitio.datos.ROTULOS.values())
    assert (destino / 'buscar' / 'index.html').is_file()


def test_indice_admite_texto_raro(tmp_path):
    g = _grafo()
    g.set((URIRef(BASE + 'id/crit/SMAT01CE1.1'), SKOS.definition, Literal('a < b & "c" \\ ñ', lang='es')))
    sitio.generar(g, BASE, tmp_path / 's')
    datos = json.loads((tmp_path / 's/buscar.json').read_text(encoding='utf-8'))
    assert any(d['t'] == 'a < b & "c" \\ ñ' for d in datos)
```

(Añadir `import json` al principio de `tests/test_sitio.py`.)

- [ ] **Step 2:** fallan.
- [ ] **Step 3:** implementar `indice.entradas` y escribir `buscar.json` con `json.dumps(..., ensure_ascii=False, separators=(',', ':'))`. `buscar.js` (sin dependencias salvo MiniSearch, cargado bajo demanda):
  - `cargar()`: la primera vez inyecta `<script src="{base}recursos/minisearch.js">`, descarga `{base}buscar.json` y crea `new MiniSearch({idField: 'u', fields: ['c', 't', 'r'], storeFields: ['u','c','t','k','r','e','m'], processTerm: normalizar, searchOptions: {prefix: true, fuzzy: 0.2, boost: {c: 3}, combineWith: 'AND'}})`; `normalizar` quita tildes (`normalize('NFD')` y diacríticos) y pasa a minúsculas.
  - Sugerencias: en el `input[name=q]` de la cabecera (y el de la portada), `role="combobox"`, `aria-expanded`, lista `role="listbox"` con 8 resultados (tipo, código, texto recortado, ruta) y «Ver los N resultados →» a `buscar/?q=…`; flechas, Intro (abre el seleccionado o la página de resultados) y Esc.
  - Página de resultados: lee `q`, `e`, `k`, `m` de la URL; rellena los `<select>` con los valores presentes en los resultados; al cambiar un filtro actualiza la URL con `history.replaceState`; pinta de 50 en 50 con «Ver más».
  - Pestañas: si existe `.pestanas`, la muestra, activa la primera, oculta los demás paneles y gestiona clic y flechas izquierda/derecha (`aria-selected`, `tabindex`).
  - Sin JavaScript: el `<noscript>` de `buscar/` dice que el buscador necesita JavaScript.
- [ ] **Step 4:** pasa la batería. **Comprobación manual en el navegador** con la vista previa local (`--base http://localhost:8000/` y `python -m http.server -d dist/sitio 8000`): sugerencias con «fracciones» y «SMAT01CE1.1», teclado, filtros y URL compartible, pestañas con teclado, página sin JavaScript.
- [ ] **Step 5: Commit** — «Sitio: buscador con sugerencias y página de resultados».

### Task 5: publicación y documentación

**Files:**
- Modify: `.github/workflows/publicar.yml` (rutas comprobadas con `curl`: añadir `buscar/`, `buscar.json`, `recursos/estilo.css`)
- Modify: `docs/modelo.md` («Resolución»), `docs/contribuir.md` (vista previa local), `docs/backlog.md` (fase 7, tarea 7.1, hecha), `CHANGELOG.md` («Sin publicar» → «Añadido»), `docs/superpowers/specs/2026-11-09-sitio-para-personas-design.md` (estado y nombre `minisearch.js`)

- [ ] **Step 1:** editar los ficheros. En `modelo.md`, la viñeta «Resolución» añade: «Las fichas HTML son también un visor para personas (navegación por etapa, curso y materia, y buscador estático con `buscar.json`); revisa la decisión de la 6.2 de dejar la consulta para personas a Omeka.»
- [ ] **Step 2:** `.venv/bin/python -m pytest -q`, `construir --comprobar --dist`, `exportar_rdf --validar`, `sitio` sobre `dist/curriculo.ttl` y `contrastar --estricto`: todo en verde. Tamaño del sitio (`du -sh dist/sitio`) anotado en el PR.
- [ ] **Step 3: Commit** — «Sitio para personas: publicación y documentación».
- [ ] **Step 4:** subir la rama `sitio-personas` y abrir PR (base `main` cuando #15 esté fusionado; si no, indicarlo en el PR).
