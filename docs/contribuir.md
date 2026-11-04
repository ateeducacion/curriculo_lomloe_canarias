# Cómo contribuir

Todo cambio entra por *pull request*. La CI construye el corpus, lo valida, lo contrasta con
los documentos oficiales y publica el resumen en la pestaña de la ejecución.

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

## Crear una materia que no está en la exportación

Añádela a `config/materias.csv` (código, código en identificadores, denominación, cursos y
documento), pon su código en las `materias` del documento en el manifiesto y ejecuta:

```bash
python -m herramientas.materia_desde_odt <id-del-documento>
```

Escribe una corrección `propuesta` que crea todos sus nodos desde el ODT, pasándolo por el
importador para que tengan la misma forma que los importados.

## Proponer una corrección

Los huecos del corpus que un documento permite rellenar (enunciados de competencia y textos
de saber que faltan) no hace falta escribirlos a mano:

```bash
python -m herramientas.contrastar --proponer
```

escribe una corrección `propuesta` por documento y tipo de error, con la fuente y su sha256.
Tipos: textos ausentes en la exportación, explicaciones de bloque copiadas de otro curso,
textos de saber de otra materia y bloques de saberes con título y descripción juntos (ver
`CATEGORIAS` en `herramientas/contrastar.py`). Los saberes sin texto se emparejan por
contenido, no por número; los tramos que no casan uno a uno aparecen en el informe como
«revisar a mano». No toca las correcciones existentes ni repite cambios que ya cubren.

Para el resto, crea `correcciones/NNNN-descripcion-breve.yaml` (ver el formato en
`herramientas/correcciones.py` y los ejemplos 0001 y 0002) con `estado: propuesta`.
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

1. Actualiza `CHANGELOG.md` y la `version` de `config/corpus.yaml`.
2. Fusiona en `main` con la CI en verde.
3. Crea la etiqueta: `git tag v1.0.0 && git push origin v1.0.0`. El flujo «Publicar versión»
   crea la *release* con `curriculo.json`, su sha256 y los CSV.
