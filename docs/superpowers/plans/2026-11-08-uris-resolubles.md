# URIs resolubles en GitHub Pages: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generar un sitio estático con una carpeta por URI del corpus (ficha HTML y Turtle) y
desplegarlo en GitHub Pages con cada versión, para que las URIs del Turtle de la 1.1.0 respondan.

**Architecture:** `herramientas/sitio.py` lee el grafo (el `curriculo.ttl` ya validado) y escribe
`id/<ruta>/index.html` e `index.ttl` por sujeto, la ficha del vocabulario en `def/cur/`, una
portada y `.nojekyll`. Los enlaces de las fichas son las propias URIs (absolutas). El flujo
«Publicar versión» genera el sitio antes de crear la *release* y un segundo job lo despliega y
comprueba con `curl`.

**Tech Stack:** Python 3.12, rdflib 7, pytest, GitHub Actions (`upload-pages-artifact@v3`,
`deploy-pages@v4`).

**Spec:** `docs/superpowers/specs/2026-11-07-uris-resolubles-design.md`

## Global Constraints

- La base de las URIs sale de `config/corpus.yaml` (`rdf.base`) vía `exportar_rdf.base_uri()`; no se duplica.
- No cambia ninguna URI ni el comportamiento de `exportar_rdf.py`.
- HTML en español (`lang="es"`), todo texto escapado con `html.escape`.
- Nada generado se guarda en git (`dist/` ya está en `.gitignore`).
- Fuera de alcance: JSON-LD, negociación de contenido, índices, búsqueda, w3id.org.
- Estilo del repositorio: módulos con docstring de uso, nombres en español, comentarios escasos.

## Review Focus

1. Ruta de un sujeto con `..`, segmentos vacíos o barra final → la generación falla en lugar de escribir fuera de `destino`.
2. `--destino` apunta a una carpeta existente que no es un sitio generado → error, nunca se borra.
3. Enlace a una URI bajo `<base>id/` que no es sujeto del grafo → error con la lista de enlaces rotos.
4. Grafo sin ningún sujeto bajo la base (base mal configurada) → error.
5. Hijos numerados (`SBI.2`, `SBI.10`) → salen en orden natural, no alfabético.

Cada uno tiene su prueba en la tarea 1 o 2.

## Cambio respecto a la especificación

El sitio se genera en el job de publicación **antes** de crear la *release* (si la generación
falla, no se publica nada) y se sube con `upload-pages-artifact`; el job `pages` solo despliega
y comprueba. Así no hace falta pasar el Turtle entre jobs. La especificación se actualiza.

---

### Task 1: Fichas y Turtle por sujeto (`herramientas/sitio.py`)

**Files:**
- Create: `herramientas/sitio.py`
- Test: `tests/test_sitio.py`

**Interfaces:**
- Consumes: `exportar_rdf.grafo(corpus, descriptores, base)`, `exportar_rdf.VOCABULARIO`,
  `exportar_rdf.base_uri()`; el corpus mínimo `CORPUS`, `DESCRIPTORES`, `BASE` de
  `tests/test_exportar_rdf.py`.
- Produces: `sitio.generar(g, base, destino, vocabulario=VOCABULARIO) -> int` (número de
  sujetos escritos); `sitio.ruta(base, s) -> str` (ruta relativa `id/...`, valida segmentos).

- [ ] **Step 1: Pruebas que fallan** en `tests/test_sitio.py`:

```python
import pytest
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import SKOS

from herramientas import exportar_rdf, sitio
from tests.test_exportar_rdf import BASE, CORPUS, DESCRIPTORES

def _grafo():
    return exportar_rdf.grafo(CORPUS, DESCRIPTORES, BASE)

@pytest.fixture
def web(tmp_path):
    g = _grafo()
    destino = tmp_path / 'sitio'
    sitio.generar(g, BASE, destino)
    return g, destino

def _sujetos(g):
    return {s for s in g.subjects() if isinstance(s, URIRef) and str(s).startswith(BASE + 'id/')}

def test_cada_sujeto_tiene_ficha_y_turtle(web):
    g, destino = web
    for s in _sujetos(g):
        carpeta = destino / str(s)[len(BASE):]
        assert (carpeta / 'index.html').is_file() and (carpeta / 'index.ttl').is_file()

def test_turtle_es_la_descripcion_del_sujeto(web):
    g, destino = web
    ce = URIRef(BASE + 'id/ce/SMATC1')
    d = Graph().parse(destino / 'id/ce/SMATC1/index.ttl')
    assert set(d.predicate_objects(ce)) == set(g.predicate_objects(ce))
    assert set(d.subjects()) - {ce}   # el enunciado por curso (nodo en blanco) va incluido
    assert Literal('Resolver problemas sencillos.', lang='es') in set(d.objects(None, SKOS.definition))

def test_enlaces_internos_existen(web):
    g, destino = web
    import re
    for f in destino.rglob('index.html'):
        for href in re.findall(r'href="([^"]+)"', f.read_text(encoding='utf-8')):
            if href.startswith(BASE + 'id/'):
                assert (destino / href[len(BASE):] / 'index.html').is_file(), (f, href)

def test_ficha_retirado(web):
    _, destino = web
    texto = (destino / 'id/sb/SMAT01SBI.2/index.html').read_text(encoding='utf-8')
    assert 'retirado' in texto.lower()
    assert f'href="{BASE}id/sb/SMAT01SBI.1"' in texto

def test_ficha_enlaza_turtle_y_escapa(tmp_path):
    g = _grafo()
    crit = URIRef(BASE + 'id/crit/SMAT01CE1.1')
    g.set((crit, SKOS.prefLabel, Literal('a < b & "c"', lang='es')))
    sitio.generar(g, BASE, tmp_path / 's')
    texto = (tmp_path / 's/id/crit/SMAT01CE1.1/index.html').read_text(encoding='utf-8')
    assert '<link rel="alternate" type="text/turtle" href="index.ttl">' in texto
    assert 'a &lt; b &amp; &quot;c&quot;' in texto and 'a < b' not in texto

def test_orden_natural(tmp_path):
    g = _grafo()
    sb = URIRef(BASE + 'id/sb/SMAT01SBI')
    for n in (10, 3):
        h = URIRef(f'{BASE}id/sb/SMAT01SBI.{n}')
        g.add((sb, SKOS.narrower, h)); g.add((h, SKOS.notation, Literal(f'SMAT01SBI.{n}')))
    sitio.generar(g, BASE, tmp_path / 's')
    texto = (tmp_path / 's/id/sb/SMAT01SBI/index.html').read_text(encoding='utf-8')
    assert texto.index('SBI.2"') < texto.index('SBI.3"') < texto.index('SBI.10"')

def test_enlace_roto(tmp_path):
    g = _grafo()
    g.add((URIRef(BASE + 'id/crit/SMAT01CE1.1'), SKOS.related, URIRef(BASE + 'id/crit/NOEXISTE')))
    with pytest.raises(ValueError, match='NOEXISTE'):
        sitio.generar(g, BASE, tmp_path / 's')

def test_base_sin_sujetos(tmp_path):
    with pytest.raises(ValueError, match='base'):
        sitio.generar(_grafo(), 'https://otra.org/', tmp_path / 's')

@pytest.mark.parametrize('cola', ['id/crit/../../x', 'id/crit//x', 'id/crit/x/'])
def test_ruta_insegura(cola):
    with pytest.raises(ValueError):
        sitio.ruta(BASE, URIRef(BASE + cola))
```

- [ ] **Step 2:** `.venv/bin/python -m pytest tests/test_sitio.py -q` → falla (`sitio` no existe).
- [ ] **Step 3: Implementación** de `generar`, `ruta`, la ficha y el Turtle (CBD con
  `Graph.cbd`, prefijos copiados del grafo). Orden natural con
  `re.split(r'(\d+)', texto)`. Etiqueta de cada propiedad: `rdfs:label` del vocabulario, si no
  un diccionario para SKOS/dcterms/owl, si no su forma corta. Se omiten en la lista `rdf:type`
  (va aparte), `prefLabel`, `notation`, `definition`, `scopeNote`, `enunciadoEnCurso`,
  `owl:deprecated` (aviso aparte) y las de schema.org (duplican SKOS).
- [ ] **Step 4:** las pruebas pasan.
- [ ] **Step 5: Commit** «Sitio de las URIs: ficha y Turtle por nodo (tarea 6.2)».

### Task 2: Vocabulario, portada, `.nojekyll` y línea de órdenes

**Files:**
- Modify: `herramientas/sitio.py`
- Test: `tests/test_sitio.py`

**Interfaces:**
- Consumes: `generar` de la tarea 1.
- Produces: `python -m herramientas.sitio [--ttl dist/curriculo.ttl] [--destino dist/sitio] [--base URL]`;
  `sitio.main(argv) -> int`.

- [ ] **Step 1: Pruebas que fallan:**

```python
from rdflib.namespace import RDF

def test_vocabulario_y_portada(web):
    _, destino = web
    voc = Graph().parse(exportar_rdf.VOCABULARIO)
    cur = str(exportar_rdf.espacio_cur())
    texto = (destino / 'def/cur/index.html').read_text(encoding='utf-8')
    terminos = {t for t in voc.subjects(RDF.type, None) if str(t).startswith(cur)}
    assert terminos and all(f'id="{str(t)[len(cur):]}"' in texto for t in terminos)
    assert (destino / 'def/cur.ttl').read_bytes() == exportar_rdf.VOCABULARIO.read_bytes()
    portada = (destino / 'index.html').read_text(encoding='utf-8')
    assert f'{BASE}id/curriculo' in portada and 'releases/tag/v1.0.0' in portada
    assert (destino / '.nojekyll').exists()

def test_main_no_borra_carpetas_ajenas(tmp_path):
    ttl = tmp_path / 'c.ttl'
    _grafo().serialize(ttl, format='turtle')
    ajena = tmp_path / 'ajena'; ajena.mkdir(); (ajena / 'dato.txt').write_text('x')
    with pytest.raises(SystemExit):
        sitio.main(['--ttl', str(ttl), '--destino', str(ajena), '--base', BASE])
    assert (ajena / 'dato.txt').exists()
    destino = tmp_path / 'sitio'
    assert sitio.main(['--ttl', str(ttl), '--destino', str(destino), '--base', BASE]) == 0
    assert sitio.main(['--ttl', str(ttl), '--destino', str(destino), '--base', BASE]) == 0  # regenera
```

- [ ] **Step 2:** fallan.
- [ ] **Step 3:** `_vocabulario(vocabulario, destino)`: ancla por término `cur:` con etiqueta,
  comentario, `subClassOf`, `domain`, `range`; copia `cur.ttl` a `def/cur.ttl`. `_portada(g, base,
  destino)`: versión de `owl:versionInfo` del esquema `<base>id/curriculo`, enlaces a los dos
  esquemas, al vocabulario y a `REPOSITORIO/releases/tag/v<versión>`. `main`: `--ttl`,
  `--destino`, `--base` (por defecto `base_uri()`); si `destino` existe y no tiene `.nojekyll`,
  `SystemExit` con mensaje; si lo tiene, lo borra y regenera.
- [ ] **Step 4:** pasan; además, con el corpus real:
  `.venv/bin/python -m herramientas.sitio --ttl dist/curriculo.ttl --destino dist/sitio`
  (medir tiempo y tamaño) y abrir `dist/sitio/id/crit/SMAT01CE1.1/index.html`.
- [ ] **Step 5: Commit** «Sitio de las URIs: vocabulario, portada y línea de órdenes».

### Task 3: Despliegue en `publicar.yml` y comprobación en `validar.yml`

**Files:**
- Modify: `.github/workflows/publicar.yml`, `.github/workflows/validar.yml`

- [ ] **Step 1:** en `publicar.yml`, job `publicar`: `outputs: base`, paso que escribe la base en
  `$GITHUB_OUTPUT`, paso «Generar el sitio de las URIs» (`python -m herramientas.sitio --ttl
  dist/curriculo.ttl --destino dist/sitio`) y `actions/upload-pages-artifact@v3` con
  `path: dist/sitio`, todo antes de «Crear la versión en GitHub».
- [ ] **Step 2:** job `pages` (`needs: publicar`, `permissions: pages: write, id-token: write`,
  `environment: github-pages`): `actions/deploy-pages@v4` y la comprobación:

```bash
base='${{ needs.publicar.outputs.base }}'
falla=0
for ruta in id/curriculo id/descriptores id/etapa/ESO id/crit/SMAT01CE1.1 id/crit/SMAT01CE1.1/index.ttl \
            id/sb/SMAT01SBI.1 id/descriptor/ESO/CCL1 id/competencia-clave/CCL def/cur def/cur.ttl; do
  ok=
  for intento in 1 2 3 4 5 6; do
    if curl -fsSL -o /dev/null "$base$ruta"; then ok=1; break; fi
    sleep 10
  done
  if [ -n "$ok" ]; then echo "responde: $base$ruta"; else echo "::error::No responde $base$ruta"; falla=1; fi
done
exit $falla
```

- [ ] **Step 3:** en `validar.yml`, paso «Generar el sitio de las URIs» tras la validación SHACL
  (detecta enlaces rotos en los PR).
- [ ] **Step 4:** comprobar que las rutas de la lista existen en `dist/sitio` local y que los
  YAML se leen (`python -c "import yaml,sys; [yaml.safe_load(open(f)) for f in sys.argv[1:]]" …`).
- [ ] **Step 5: Commit** «CI: despliegue del sitio de las URIs en GitHub Pages».

### Task 4: Documentación

**Files:**
- Modify: `docs/modelo.md`, `docs/contribuir.md`, `docs/pendientes.md`, `docs/backlog.md`,
  `CHANGELOG.md`, `docs/superpowers/specs/2026-11-07-uris-resolubles-design.md`

- [ ] `modelo.md`, «Datos enlazados»: cómo resuelven las URIs (carpeta con `index.html` e
  `index.ttl`, `def/cur`) y que se publican con cada versión.
- [ ] `contribuir.md`, «Publicar una versión»: el flujo despliega el sitio y comprueba las URIs;
  requisito de tener Pages con *Source: GitHub Actions*.
- [ ] `pendientes.md`: quitar «URIs resolubles» (o dejar solo el paso manual pendiente).
- [ ] `backlog.md`: 6.2 hecha, con el cierre pendiente de la 1.1.0.
- [ ] `CHANGELOG.md` [Sin publicar]: entrada del sitio.
- [ ] Especificación: el sitio se genera en el job de publicación y el job `pages` despliega.
- [ ] `pytest -q` completo en verde; commit «Documentación de las URIs resolubles (tarea 6.2)».
