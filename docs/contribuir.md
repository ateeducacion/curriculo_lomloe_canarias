# Cómo contribuir

Todo cambio entra por *pull request*. La CI construye el corpus, lo valida, lo contrasta con
los documentos oficiales y publica el resumen en la pestaña de la ejecución.

## Registrar un documento oficial

1. Descarga el ODT desde la página oficial con el navegador (el portal no admite
   descargas automatizadas) y guárdalo en `fuentes/documentos/<etapa>/` con el mismo
   nombre que tiene en la URL.
2. Ejecuta `python -m herramientas.registrar_fuentes`: anota ruta, sha256 y fecha en el manifiesto.
3. Revisa en el manifiesto las `materias` propuestas para ese documento.
4. Para que se contraste, añade `secciones`: qué rótulo del documento corresponde a qué
   materia y curso. Ejemplo (Matemáticas de ESO):

   ```yaml
   secciones:
     1.º ESO: {materia: SMAT, curso: '01'}
     Matemáticas A: {materia: SMMA, curso: '04'}
   ```
5. Ejecuta `python -m herramientas.contrastar` y revisa `informes/contraste.md`.

El lector de ODT está probado con el formato de las materias de ESO. Otros formatos
(Infantil, Primaria, ámbitos) pueden necesitar ajustes en `herramientas/odt.py`.

## Proponer una corrección

Crea `correcciones/NNNN-descripcion-breve.yaml` (ver el formato en
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
