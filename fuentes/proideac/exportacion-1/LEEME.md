# Exportación de ProIDEAC n.º 1

- **Fichero:** `curriculo_unificado_ordenado.json`
- **Origen:** exportación de la aplicación ProIDEAC aportada al proyecto.
- **Fecha de exportación:** pendiente de confirmar.
- **sha256 del fichero original:** `fa6c88121960bd3c153164912e276aff830c392cd957b4dd9a4d59b1a23737b8`

## Única modificación respecto al original

En Educación Primaria, 1.º, materia `EFI` (Educación Física), una de las claves de
bloque de saberes contenía una **credencial** (una cadena con formato de clave de API)
en lugar del título del bloque. Se ha sustituido por el texto
`[ELIMINADO] clave sustituida: contenía una credencial`. El saber afectado
(`PEFI01SBV.2`) se sigue importando en su bloque (V) gracias a su código.

La credencial era antigua y ya estaba revocada (confirmado el 03-11-2026). Aun así no se
conserva en el repositorio, y conviene revisar el proceso de exportación de ProIDEAC para
que no vuelva a introducir valores de este tipo.

## Cómo añadir una exportación nueva

1. Crear `fuentes/proideac/exportacion-2/` con el fichero y un LEEME como este.
2. Cambiar `base.fichero` en `config/corpus.yaml`.
3. Abrir una pull request: la CI mostrará qué cambia en el corpus y qué correcciones
   dejan de ser necesarias.
