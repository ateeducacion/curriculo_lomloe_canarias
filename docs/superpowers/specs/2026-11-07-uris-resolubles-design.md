# URIs resolubles en GitHub Pages (tarea 6.2)

Fecha: 07-11-2026. Estado: aprobado; implementado el 08-11-2026 (plan en `docs/superpowers/plans/2026-11-08-uris-resolubles.md`).

## Objetivo

Que las URIs del Turtle de la 1.1.0 respondan. Hoy `curriculo.ttl` nombra cada nodo con
`<base>id/<prefijo>/<código>` y el vocabulario con `<base>def/cur#`, con la base de GitHub
Pages (`config/corpus.yaml`, `rdf.base`), pero Pages no está activado y ninguna responde.

Cierre (backlog): las URIs del Turtle de la 1.1.0 responden.

## Decisiones

- **Público: máquinas, con HTML mínimo.** Cada URI devuelve una ficha HTML sobria que enlaza a
  su Turtle. La consulta para personas es cosa de Omeka S; el sitio no tiene índices de
  navegación, búsqueda ni diseño propio.
- **Base: la actual de GitHub Pages.** No cambia ninguna URI. w3id.org u otro dominio quedan
  fuera de esta tarea.
- **Sitio generado en la CI y desplegado con GitHub Actions**, sin guardar nada generado en git
  (descartadas una rama `gh-pages`, por el tamaño del historial, y una página única con
  `404.html`, que responde con estado 404).

## Qué se publica

GitHub Pages no negocia el tipo de contenido y los códigos llevan puntos (`SMAT01CE1.1`), así
que cada URI es una carpeta con su `index.html`; Pages redirige `…/SMAT01CE1.1` a
`…/SMAT01CE1.1/` (301).

| Ruta en el sitio | Contenido |
|---|---|
| `id/<ruta>/index.html` | Ficha de cada sujeto URI del grafo bajo `<base>id/` |
| `id/<ruta>/index.ttl` | Descripción RDF de ese sujeto |
| `def/cur/index.html` | Ficha del vocabulario: sus clases y propiedades, con ancla por término (`#Criterio`) |
| `def/cur.ttl` | Copia de `vocabulario/cur.ttl` |
| `index.html` | Portada: qué es, versión (`owl:versionInfo`), enlaces a los dos esquemas, al vocabulario y al release `v<versión>` |
| `.nojekyll` | Que Pages no procese el sitio con Jekyll |

`<ruta>` es lo que sigue a `<base>id/` en la URI, sea de un nivel (`crit/SMAT01CE1.1`,
`curriculo`, `descriptores`) o de dos (`descriptor/ESO/CCL1`). Hoy son unos 15.560 sujetos
(nodos del corpus, descriptores, competencias clave y los esquemas `curriculo` y
`descriptores`), unos 31.000 ficheros.

### Ficha HTML de un sujeto

- `<title>` y `<h1>` con la notación y la etiqueta (`skos:notation`, `skos:prefLabel`).
- Tipo (la clase `cur:` o `skos:ConceptScheme`) enlazado a su ancla en `def/cur/`.
- Definición, nota de alcance y enunciados por curso, si los tiene.
- Enlaces a los sujetos relacionados, con su notación y etiqueta: `skos:broader`,
  `skos:narrower`, `skos:inScheme`, `skos:hasTopConcept`, las propiedades `cur:` que apuntan a
  otros nodos (materia, curso, etapa, bloque, agrupa, descriptor operativo…).
- Si está retirado (`owl:deprecated`), un aviso visible y el enlace a `dcterms:isReplacedBy`.
- `<link rel="alternate" type="text/turtle" href="index.ttl">` y un enlace visible al Turtle.
- Unas líneas de CSS en línea; HTML en español (`lang="es"`), escapado.

### Turtle de un sujeto

Las tripletas cuyo sujeto es la URI, más las de los nodos en blanco que cuelgan de ella (los
enunciados por curso), es decir, su descripción acotada (CBD). Con los prefijos del grafo.

## Componentes

- **`herramientas/sitio.py`** (nuevo). `generar(g, base, destino, vocabulario=VOCABULARIO)` recibe
  el grafo ya construido, la base y la ruta del vocabulario, y escribe el sitio en `destino`.
  Recorre los sujetos URI que empiezan por `<base>id/`; para cada uno escribe la ficha y su
  Turtle. La línea de órdenes toma la base de `exportar_rdf.base_uri()`, sin duplicar la
  configuración:
  `python -m herramientas.sitio --ttl dist/curriculo.ttl --destino dist/sitio`.
- **`herramientas/exportar_rdf.py`**: sin cambios de comportamiento; `sitio.py` reutiliza
  `base_uri()` y `VOCABULARIO`.
- **`.github/workflows/publicar.yml`**:
  1. El job actual genera el sitio desde `dist/curriculo.ttl` (el mismo Turtle validado con
     SHACL) **antes** de crear la *release*, para no publicar nada si falla, y lo sube con
     `actions/upload-pages-artifact`.
  2. Un job nuevo, `pages`, lo despliega con `actions/deploy-pages`, con `permissions: pages:
     write, id-token: write` y el entorno `github-pages`.
  3. Comprobación final con `curl`: responden con 200, siguiendo redirecciones, una URI de cada
     tipo (criterio, saber, descriptor, competencia clave, esquema) y `def/cur`. Si alguna
     falla, el job falla.
- **Documentación**: `docs/modelo.md` («Datos enlazados»: las URIs ya resuelven y cómo),
  `docs/contribuir.md` (procedimiento de publicación), `pendientes.md` (quitar la entrada de
  URIs resolubles), `backlog.md` (6.2 hecha) y CHANGELOG.

Paso manual, fuera del código: activar Pages en el repositorio (*Settings → Pages → Source:
GitHub Actions*) antes de publicar la 1.1.0.

## Errores

- Si un enlace de una ficha apunta a una URI bajo `<base>id/` que no es sujeto del grafo, la
  generación falla con la lista de enlaces rotos (no debería pasar: lo impiden la validación
  SHACL y la identidad entre versiones).
- Si el grafo no tiene ningún sujeto bajo la base (base mal configurada), falla.
- El despliegue solo ocurre si han pasado las pruebas, la validación SHACL y el contraste
  estricto, como el release.

## Pruebas

En `tests/test_sitio.py`, con el corpus mínimo de `tests/test_exportar_rdf.py`:

- Todo sujeto URI bajo la base tiene `index.html` e `index.ttl` en su carpeta.
- Cada `index.ttl` se puede leer y contiene exactamente la descripción de su sujeto, incluidos
  los enunciados por curso.
- Los enlaces internos de las fichas apuntan a carpetas que existen.
- Un nodo retirado muestra el aviso y enlaza a su sustituto.
- Los textos con caracteres especiales (`<`, `&`, comillas) salen escapados.
- `def/cur/index.html` tiene un ancla por cada clase y propiedad de `cur.ttl`.

Lo que no se puede probar en local (la redirección 301 de Pages y que las URIs respondan) lo
cubre la comprobación con `curl` del job `pages`.

## Fuera de alcance

JSON-LD, negociación de contenido, índices por etapa o materia, búsqueda, páginas de versiones
anteriores (las URIs no llevan versión) y el cambio de base a w3id.org.
