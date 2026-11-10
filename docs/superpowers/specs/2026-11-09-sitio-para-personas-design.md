# Sitio para personas: navegación y buscador

Fecha: 09-11-2026. Estado: aprobado; implementado el 10-11-2026 (plan en
`docs/superpowers/plans/2026-11-09-sitio-para-personas.md`). MiniSearch se incluye como
`recursos/minisearch.js` (el build UMD publicado no está minificado).

## Objetivo

Que el sitio de GitHub Pages sirva para enseñar el currículo a asesores y docentes: navegación
amigable de la etapa a los criterios y saberes, y un buscador. Hoy cada URI devuelve una ficha
HTML mínima pensada para máquinas (lista de propiedades RDF con rótulos técnicos).

Revisa una decisión de la 6.2 («la consulta para personas es cosa de Omeka; sin índices,
búsqueda ni diseño propio»): Omeka aún no tiene el currículo cargado, y el sitio ya publica cada
versión, de modo que un visor de solo lectura generado de los mismos datos es la forma natural
de enseñar el resultado.

Cierre: desde la portada se llega navegando a cualquier criterio o saber con rótulos para
personas, y el buscador encuentra por texto y por código, con sugerencias y con una página de
resultados filtrable.

## Decisiones

- **Público: asesores y docentes**, que conocen el currículo pero no RDF. Lo técnico (URI,
  Turtle) queda plegado al final de cada ficha.
- **Las máquinas reciben lo mismo:** URIs, `index.ttl`, `<link rel="alternate">` y vocabulario
  `def/cur` no cambian. La página HTML de cada URI pasa a ser la ficha amigable.
- **No sustituye a Omeka:** sin edición, catalogación de REA ni cuentas.
- **Materia en un curso con pestañas** (elegida frente a una columna con secciones plegables y a
  navegación lateral).
- **Portada con el buscador como protagonista** y las cuatro etapas debajo.
- **Búsqueda con sugerencias en la cabecera y página de resultados con filtros.**
- **Ficha en una columna**, con lo relacionado debajo del texto.
- **Buscador estático con índice propio (`buscar.json`) y MiniSearch 7.2.0** (MIT, incluido en el
  sitio), frente a Pagefind: todo se genera en Python y se prueba con pytest, sin binarios en la
  CI.
- **Identidad sobria y neutra**, con el nombre del proyecto; sin logotipos ni marca del Gobierno
  de Canarias, para que no parezca una web oficial.

## Páginas

| Página | Contenido |
|---|---|
| Portada | Título, buscador protagonista con ejemplos («fracciones», «SMAT01CE1.1», «contaminación lumínica») y las cuatro etapas; al pie, versión, número de elementos y enlaces al repositorio, al release y a las descargas |
| Etapa | Sus cursos y sus materias |
| Curso | Sus materias en curso, cada una con cuántas competencias, criterios y saberes tiene |
| Materia en un curso | Pestañas: «Competencias y criterios» (criterios agrupados bajo su competencia, con los descriptores como etiquetas), «Saberes básicos» (árbol por bloque y apartado) y «Bloques competenciales» (con las competencias que agrupan y su explicación) |
| Materia de la etapa | Sus competencias específicas (con los enunciados que cambian por curso) y enlaces a cada curso |
| Fichas (competencia, bloque competencial, criterio, bloque de saberes, saber) | Ruta de navegación; tipo y código; el texto como protagonista; debajo, lo relacionado; al final, «Datos técnicos» plegado (URI, Turtle, identificador) |
| Nodo retirado | Aviso destacado y enlace al sustituto, si lo hay |
| Buscar (`buscar/`) | Resultados con filtros por etapa, tipo y materia |
| Esquemas, descriptores, competencias clave, vocabulario | La misma plantilla, en versión sencilla |

Lo relacionado en la ficha de un criterio: competencia específica, bloque competencial,
descriptores operativos (con el nombre de su competencia clave al pasar el ratón) y los otros
criterios de la misma competencia en el mismo curso. En la de un saber: su bloque y su apartado
superior, y sus subsaberes. En la de una competencia: sus criterios por curso y sus enunciados
por curso.

**En todas las páginas:** cabecera con el nombre del sitio y el buscador con sugerencias, ruta
de navegación (Inicio › Etapa › Curso › Materia › …) y pie con versión y licencia. Rótulos para
personas («Competencia específica», «Criterios», «Saberes», «Pertenece a»), nunca los nombres de
las propiedades RDF.

**Sin JavaScript:** las pestañas se ven como secciones seguidas y el buscador avisa de que lo
necesita.

## Buscador

- **Índice (`buscar.json`).** Solo nodos vigentes de tipo materia, materia en curso, competencia
  específica, bloque competencial, criterio, bloque de saberes y saber. Cada entrada: `u` (URL de
  la ficha), `c` (código), `t` (texto completo: definición, o etiqueta si no la tiene), `k`
  (tipo, rótulo para personas), `r` (ruta legible, «ESO · 1.º ESO · Matemáticas · I. Sentido
  numérico»), `e` (etapa), `m` (materia). Unos 6 MB; Pages lo sirve comprimido (≈1,2 MB).
- **Búsqueda.** Sin tildes ni mayúsculas, por prefijo y con tolerancia a erratas; el código pesa
  más que el texto («SMAT01CE1.1» lleva al criterio); con varias palabras, deben aparecer todas.
- **Sugerencias** en la cabecera de cada página: desde 2 caracteres, 8 resultados con tipo y
  ruta, y «Ver los N resultados →». Teclado: flechas, Intro y Esc.
- **Página de resultados** (`buscar/?q=…&e=…&k=…&m=…`): filtros combinables por etapa, tipo y
  materia, reflejados en la URL para poder compartirla; de 50 en 50 con «Ver más».
- **Carga.** El índice y MiniSearch se descargan solo cuando alguien enfoca el buscador.

## Código

`herramientas/sitio.py` pasa a ser el paquete `herramientas/sitio/`:

| Fichero | Responsabilidad |
|---|---|
| `__init__.py` | Interfaz pública sin cambios: `generar(g, base, destino, vocabulario=VOCABULARIO) -> int`, `ruta(base, s)`, `main(argv)`; `python -m herramientas.sitio` sigue funcionando |
| `plantilla.py` | Página base (cabecera con buscador, ruta, pie), escapado |
| `paginas.py` | Una función por tipo de página |
| `indice.py` | `buscar.json` |
| `recursos/` | `estilo.css`, `buscar.js` (sugerencias, resultados, pestañas), `minisearch.min.js` 7.2.0 con su licencia |

Plantillas con f-strings y `escape()`, como ahora (sin dependencias nuevas). Los datos salen de
`curriculo.ttl`, el mismo Turtle validado que se publica. Los recursos se enlazan con la base
(`<base>recursos/estilo.css`); ninguna página lleva CSS en línea.

**Vista previa local:** `python -m herramientas.sitio --ttl dist/curriculo.ttl --destino
dist/sitio --base http://localhost:8000/` y `python -m http.server -d dist/sitio`.

**Accesibilidad:** `lang="es"`, pestañas con roles ARIA y teclado, sugerencias como
`combobox`/`listbox`, contraste suficiente, todo usable sin ratón.

## Publicación

Sin cambios en el flujo: Pages se despliega con cada etiqueta de versión. La comprobación con
`curl` del job `pages` añade `buscar/`, `buscar.json` y `recursos/estilo.css`. Para que el
equipo lo vea hace falta publicar una versión (parche, 1.1.2: los datos no cambian).

## Pruebas

Siguen valiendo las del sitio actual (cada URI con ficha y Turtle, ningún enlace roto, todo
alcanzable desde la portada). Nuevas:

- La materia en curso agrupa cada criterio bajo su competencia y los saberes en árbol por bloque.
- La ficha de un criterio muestra competencia, bloque, descriptores y criterios hermanos, con
  rótulos para personas y sin nombres de propiedades RDF.
- La ruta de navegación de un saber va de la etapa a su apartado superior.
- `buscar.json`: sin retirados, con los campos descritos, y una entrada por nodo de los tipos
  indexados.
- Ninguna página lleva `<style>`; todas enlazan `recursos/estilo.css` y existe.
- El texto sigue escapado.

El JavaScript se comprueba a mano en el navegador (sugerencias, filtros, pestañas, teclado).

## Documentación

- `docs/modelo.md` («Resolución»): el sitio es también para personas (revisa la decisión de la
  6.2).
- `docs/contribuir.md`: vista previa local.
- `docs/backlog.md`: tarea nueva (7.1) y su cierre; CHANGELOG.
- `.gitignore`: `.superpowers/`.

## Fuera de alcance

- Edición, cuentas o catalogación de REA.
- Comparar versiones, exportar selecciones o imprimir.
- Cambiar las URIs o pasar a w3id.org.
