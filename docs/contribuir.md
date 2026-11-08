# Cómo contribuir

Todo cambio entra por *pull request*. La CI pasa las pruebas (`python -m pytest`), construye
el corpus, lo valida, genera el RDF y lo valida con SHACL, lo contrasta con los documentos
oficiales y publica el resumen en la pestaña de la ejecución. Falla si `datos/` no está al
día, si hay errores de validación no aceptados, si el RDF no cumple las formas SHACL o si
queda alguna diferencia con los documentos sin explicar (`contrastar --estricto`).

Si cambias algo en `herramientas/`, añade o ajusta su prueba en `tests/` (el lector de ODT
se prueba con documentos mínimos construidos en memoria, ver `tests/conftest.py`).

## Registrar un documento oficial

1. Descarga el ODT desde la página oficial con el navegador (el portal no admite
   descargas automatizadas) y guárdalo en `fuentes/documentos/<etapa>/` con el mismo
   nombre que tiene en la URL.
2. Ejecuta `python -m herramientas.registrar_fuentes`: anota ruta, sha256 y fecha en el manifiesto.
3. Revisa en el manifiesto las `materias` propuestas para ese documento.
4. Ejecuta `python -m herramientas.contrastar` y revisa `informes/contraste.md`.

Las secciones del documento (qué rótulo corresponde a qué materia y curso) se deducen de
los cursos de cada materia en `config/materias.csv`: «1.º ESO», «2.º Bachillerato»,
«Tercer ciclo Educación Primaria» (que se contrasta con 5.º y 6.º)… Si varias materias del
documento comparten curso (Matemáticas A y B en 4.º ESO), la sección se busca por su
denominación. Solo si un documento usa otros rótulos hay que escribir `secciones` en el
manifiesto; sustituyen a las deducidas:

```yaml
secciones:
  1.º ESO: {materia: SMAT, curso: '01'}
  Tercer ciclo Educación Primaria: [{materia: PMAT, curso: '05'}, {materia: PMAT, curso: '06'}]
```

El lector de ODT está probado con los formatos de Infantil, Primaria, ESO, Bachillerato y
los ámbitos de diversificación (estos con `secciones` en el manifiesto, porque sus rótulos
—«Curso 1.º. Ámbito…»— no siguen el curso de la ESO).

## Textos del BOC

`fuentes/boletines/` guarda el texto de cada decreto tal como lo extrae `pdftotext` (poppler,
sin opciones) del PDF del BOC. El enlace y el sha256 del PDF están en el manifiesto
(`boletin_pdf`, `boletin_pdf_sha256`). Sirven para decidir qué versión de un texto es la
publicada cuando el documento y la exportación no coinciden.

## Crear una materia que no está en la exportación

Añádela a `config/materias.csv` (código, código en identificadores, denominación, cursos y
documento), pon su código en las `materias` del documento en el manifiesto y ejecuta:

```bash
python -m herramientas.materia_desde_odt <id-del-documento>
```

Escribe una corrección `propuesta` que crea todos sus nodos desde el ODT, pasándolo por el
importador para que tengan la misma forma que los importados.

## Proponer una corrección

**Criterio:** el corpus refleja el documento oficial (el ODT de la web de currículos). Ante
una diferencia, lo normal es corregir el corpus con el documento. Hay dos excepciones, que se
deciden caso a caso y se documentan:

- El documento tiene una errata que el BOC desmiente (p. ej. un código de descriptor que no
  existe): el corpus conserva el valor correcto y la diferencia se explica con una nota en
  `config/notas_contraste.yaml` (`nodo`, `tipo` y `motivo`), salvo que el contraste ya la
  explique solo.
- El documento y el BOC no coinciden: se valida cuál prevalece y se anota en
  [`pendientes.md`](pendientes.md) («Diferencias con el BOC»).

Los huecos del corpus que un documento permite rellenar (enunciados de competencia y textos
de saber que faltan) no hace falta escribirlos a mano:

```bash
python -m herramientas.contrastar --proponer
```

escribe una corrección `propuesta` por documento y tipo de error, con la fuente y su sha256.
Tipos: textos de la versión publicada en el BOC (el del documento está en `fuentes/boletines/`
y el del corpus no), textos que solo difieren en espacios, textos ausentes en la exportación, explicaciones de bloque copiadas de otro curso,
textos de saber de otra materia y bloques de saberes con título y descripción juntos (ver
`CATEGORIAS` en `herramientas/contrastar.py`). Los saberes sin texto se emparejan por
contenido, no por número; los tramos que no casan uno a uno aparecen en el informe como
«revisar a mano». No toca las correcciones existentes ni repite cambios que ya cubren.

Para el resto, crea `correcciones/NNNN-descripcion-breve.yaml` (ver el formato en
`herramientas/correcciones.py` y los ejemplos 0001 y 0002) con `estado: propuesta`.
Para quitar un nodo ya publicado usa `accion: retirar` (con `sustituido_por` si otro lo
reemplaza): queda en el corpus como obsoleto y no se rompen los enlaces de quien lo use.
`accion: eliminar` es solo para nodos que nunca se publicaron.
La persona responsable del currículo la revisa y cambia el estado a `aprobada`, indicando
`aprobada_por`. Después:

```bash
python -m herramientas.construir
```

y sube también los cambios de `datos/` e `informes/`. Si la corrección resuelve
incidencias de `config/incidencias_aceptadas.yaml`, el informe lo indica: retíralas.

## Incorporar una exportación nueva de ProIDEAC

Sigue `fuentes/proideac/exportacion-1/LEEME.md`. El informe mostrará qué cambia y qué
correcciones ya no son necesarias.

## Publicar una versión

1. Actualiza `CHANGELOG.md` y la `version` de `config/corpus.yaml`, y registra los nodos de la
   versión: `python -m herramientas.identidad --registrar X.Y.Z` (escribe
   `publicaciones/X.Y.Z.csv`; súbelo en el mismo PR).
2. Fusiona en `main` con la CI en verde.
3. Crea la etiqueta: `git tag v1.0.0 && git push origin v1.0.0`. El flujo «Publicar versión»
   vuelve a comprobarlo todo, crea la *release* con `curriculo.json`, los CSV,
   `curriculo.ttl` (con sus sha256) y el vocabulario `cur.ttl`, y despliega en GitHub Pages el
   sitio que hace resolubles las URIs (`herramientas/sitio.py`); al final comprueba que
   responden. Requiere tener Pages configurado con *Source: GitHub Actions* (Settings → Pages).

Desde la 1.0, un nodo publicado no se borra: se retira (`accion: retirar`). La construcción
lo comprueba con la lista de nodos de la última versión publicada (`publicaciones/`): si
falta uno o cambia de tipo, da error. La numeración
de versiones está en el [README](../README.md#versiones-y-consumo).
