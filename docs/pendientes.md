# Pendientes y decisiones abiertas

Estado del corpus antes de la versión 1.0.0: lo que queda abierto, las decisiones que se han
tomado donde las fuentes no coinciden y las erratas detectadas en ellas. Las cifras exactas,
en `informes/resumen.md` y `informes/contraste.md`; el historial de tareas, en
[`backlog.md`](backlog.md).

## Para comunicar a la Consejería

Erratas o dudas de las fuentes oficiales que el corpus resuelve, pero que conviene corregir
en origen:

- **BOC, Segunda Lengua Extranjera (ESO): criterios 5.1 y 6.1 intercambiados** en los cuatro
  cursos y los tres idiomas (detalle en «Erratas del BOC»).
- **BOC y ODT, Lengua Castellana y Literatura (Primaria, 1.º y 2.º):** el criterio 7.2 trae el
  descriptor «CCE3», que no existe en la etapa. El corpus conserva la lista válida; son las 4
  diferencias que quedan en el contraste.
- **ODT, Cultura Científica (Bachillerato):** repite «Contaminación lumínica» en los saberes
  II.2.4.1 y II.2.4.3 (corrección 0012, aprobada con el texto del documento). ¿Errata?
- **ODT, Filosofía (Bachillerato):** el documento anida tres saberes de III.1.8 bajo
  III.1.8.4; el corpus los mantiene al mismo nivel, con los códigos de ProIDEAC (corrección
  0015). Respetar la jerarquía del documento cambiaría identificadores.
- **Exportación de ProIDEAC:** una clave de bloque de saberes (Primaria, Educación Física, 1.º)
  contenía una credencial, ya revocada (03-11-2026); se eliminó de la copia del repositorio y
  la CI bloquea cualquier cadena con formato de credencial. Conviene que el proceso de
  exportación no vuelva a introducir valores de este tipo.

## Diferencias con el BOC

El corpus refleja el ODT oficial de la web de currículos (criterio aprobado el 05-11-2026). En 24
casos el ODT no coincide con el texto publicado en el BOC; se validaron uno a uno el 05-11-2026 y
en todos prevalece el ODT (correcciones 0255–0262). Quien necesite el texto literal del BOC debe
tenerlo en cuenta:

- Texto distinto (9): explicaciones de bloque `bc:SEC304BC6`, `bc:BEC101BC2`, `bc:BAAP01BC1`;
  enunciados `ce:BDBTC2`, `ce:BDBCC2`, `ce:BEFIC3`, `ce:BAAPC2`; criterios `crit:BDBT01CE2.3`,
  `crit:BDBT01CE4.1`.
- Puntuación (8): títulos de los bloques II y III de Educación Emocional y para la Creatividad
  (Primaria, 1.º, 2.º, 5.º y 6.º).
- Descriptores (4): el ODT añade CCL1 al criterio 8.2 de Lengua Castellana y Literatura (Primaria,
  5.º y 6.º) y, por tanto, a su bloque competencial.
- Saberes que el ODT omite (3): `sb:PLCL05SBIV.4`, `sb:PLCL06SBIV.4` y `sb:BPSI02SBVI.9` están en el
  BOC y no en el ODT; se retiran del corpus.

Quedan 4 diferencias con el ODT, explicadas en `informes/contraste.md`: erratas de descriptores
del ODT de Lengua Castellana y Literatura (Primaria, 1.º y 2.º, criterio 7.2 y su bloque), con
códigos que no existen en la etapa; el corpus conserva la lista válida. Las competencias cuyo
enunciado cambia según el curso guardan el de cada curso en `enunciados_curso` (correcciones
0263–0266); al hacerlo aparecieron cuatro enunciados que la explicación «limitación del modelo»
ocultaba y se corrigieron con el ODT (0267–0269; en Cultura Científica la competencia 2 repetía
el enunciado de la 1).

## Erratas del BOC

El contraste comprueba también con qué número imprime el BOC cada criterio de evaluación
(informe `informes/contraste.md`, «numeración distinta en el BOC»). Estas erratas no son
diferencias del corpus: el corpus sigue el documento oficial.

- **Segunda Lengua Extranjera (ESO), criterios 5.1 y 6.1 intercambiados** en los cuatro cursos
  y los tres idiomas (Alemán `SSGA`, Italiano `SSGD`, Francés `SSGN`): 24 criterios. En el Decreto
  30/2023 (BOC n.º 58, de 23-03-2023), la tabla de la competencia 5 («Ampliar y usar los
  repertorios lingüísticos…», plurilingüismo) contiene «5.1. Valorar de forma empática y
  respetuosa la diversidad lingüística, cultural y artística…» y la de la competencia 6
  («Valorar críticamente y adecuarse a la diversidad lingüística, cultural…», interculturalidad)
  contiene «6.1. Registrar, analizar y compartir los progresos y dificultades de aprendizaje…» (en
  1.º y 3.º, «Identificar y registrar…» / «Identificar, registrar, y compartir…»). Comprobado en
  el PDF en 2.º ESO, págs. 16133–16134. El contenido de cada criterio no corresponde a la
  competencia bajo la que aparece: el ODT oficial, las rúbricas de la Consejería, Primera Lengua
  Extranjera y la exportación de ProIDEAC usada como base dan 5.1 = «Registrar…» (autoevaluación,
  Portfolio) y 6.1 = «Valorar…», y así queda el corpus. Lo señaló un usuario de ProIDEAC
  (05-11-2026), que lo ve intercambiado en el catálogo actual de ProIDEAC para Alemán de 2.º ESO;
  el origen probable es esta errata del BOC. Conviene comunicarlo al servicio responsable del
  currículo por si procede una corrección de errores en el BOC.

## Cobertura

- Las optativas *Juegos y Deportes Tradicionales de Canarias* y *Música, Expresión y
  Espectáculos* (Decreto 78/2025) no estaban en la exportación: se crearon desde su ODT con los
  códigos `JUI` y `MUW`, que no proceden de ProIDEAC (correcciones 0042 y 0043).
- Los ámbitos de diversificación (`SMBS`, `SAMB`, `SAM3`) corresponden al Decreto 86/2025.
- No entran las concreciones del silbo gomero ni los currículos de Religión (`excluidos` en el
  manifiesto).

## Avisos del importador

Los produce el importador al leer la exportación de ProIDEAC (`informes/resumen.md`). Son
informativos: el contraste con los 105 documentos confirma que, con las correcciones, el
corpus coincide con ellos.

- **Encabezados de otra materia** (`encabezado_no_corresponde`, `texto_en_conflicto`): textos
  mezclados entre materias en la exportación (sobre todo 3.º ESO), corregidos desde los ODT.
- **Explicaciones de bloque idénticas entre cursos** (`explicacion_repetida_entre_cursos`): las
  que el documento distingue ya están corregidas; las dos que quedan (Matemáticas BC7 de 1.º a
  3.º ESO y Matemáticas B BC2 de 3.º y 4.º) las repite el propio documento. El aviso no cuenta
  los cursos de un mismo ciclo de Infantil o Primaria, que comparten la explicación oficial.
- **Códigos de materia inconsistentes**: en tres materias el código del catálogo no coincide con
  el de sus identificadores (`TSA`/`TA7`, `PLW`/`LNT`, `VAL`/`EDK`). Se mantienen ambos en
  `config/materias.csv` y los identificadores no cambian (decisión del 04-11-2026).
- **Códigos de saber reconstruidos** (43): venían truncados, con punto final o repetidos; se
  reparan a partir del número del texto.

## Después de la 1.0

- **Códigos incoherentes con la numeración del texto** (tarea 3.5): unos 88 registros de la
  exportación tienen un código cuyo apartado no coincide con el número de su encabezado. Los
  textos ya coinciden con los documentos; cambiar esos códigos rompería identificadores
  publicados, así que solo se haría retirando los nodos y creando otros. Aplazado a después de la
  1.0 (confirmado el 06-11-2026).
- **CODEOWNERS** con los equipos reales y protección de la rama `main` (aplazado el 04-11-2026).

## Integración con Omeka S

Modelo y decisiones en [`modelo.md`](modelo.md#integración-con-omeka-s). Pendiente:

- **Módulo de sincronización** (repositorio aparte): lee `curriculo.json`, localiza los ítems por
  `dcterms:identifier` y aplica los cambios tras la aprobación de una persona.
- **Instancia de desarrollo.** Es una primera aproximación (12.474 ítems `schema:DefinedTerm`,
  cargados de la misma exportación de ProIDEAC). Comparada el 05-11-2026: coinciden los códigos
  de los 3.026 criterios, 7.805 saberes y 759 competencias, así que una tabla de correspondencias
  es directa. Falta decidir si se migran sus recursos o se carga de cero.
- **URIs resolubles.** Resuelven desde la 1.1.0 (tarea 6.2). Pasar a w3id.org sigue abierto:
  cambiaría todas las URIs.
