import xml.etree.ElementTree as ET

from conftest import lista, p, tabla

from herramientas import odt

SECCION = 'Matemáticas 1.º ESO'


def _leer(crear_odt, *partes):
    return odt.leer(crear_odt(*partes), {SECCION: None})


def test_bloque_competencial(crear_odt):
    doc = _leer(
        crear_odt,
        p('Competencia específica 1 (C1)'), p('Explicación de la competencia.'),
        p(SECCION), p('Bloques competenciales'),
        tabla([['Competencia específica', '1. Enunciado de la competencia.'], ['Descriptores', 'CCL1, STEM1.']],
              [['Criterios de evaluación']],
              [['1.1. Texto del criterio'], ['CCL1; STEM1']],
              [['Explicación del bloque competencial'], ['Texto de la explicación.']]),
    )
    assert doc['avisos'] == []
    assert doc['explicacion_competencias'] == {1: 'Explicación de la competencia.'}
    (bloque,) = doc['secciones'][SECCION]['bloques_competenciales']
    assert bloque['competencias'] == [{'num': 1, 'enunciado': 'Enunciado de la competencia.'}]
    # El punto final de la lista de descriptores se quita.
    assert bloque['descriptores'] == ['CCL1', 'STEM1']
    assert bloque['criterios'] == [{'num': '1.1', 'competencia': 1, 'texto': 'Texto del criterio',
                                    'descriptores': ['CCL1', 'STEM1']}]
    assert bloque['explicacion'] == 'Texto de la explicación.'


def test_criterios_de_infantil_en_una_fila(crear_odt):
    doc = _leer(
        crear_odt, p(SECCION),
        tabla([['Competencia específica', '1. Enunciado.']],
              [['Criterios de evaluación', '1.1 Primer criterio', 'que sigue aquí', '1.2. Segundo criterio']]),
    )
    criterios = doc['secciones'][SECCION]['bloques_competenciales'][0]['criterios']
    assert [(c['num'], c['texto'], c['descriptores']) for c in criterios] == [
        ('1.1', 'Primer criterio que sigue aquí', None), ('1.2', 'Segundo criterio', None)]


def test_saberes(crear_odt):
    doc = _leer(
        crear_odt, p(SECCION), p('Saberes básicos'),
        p('I. Sentido numérico'), p('Descripción del bloque.'),
        lista(('Conteo', lista('3.2 Contar hasta diez', 'Contar hacia atrás')), 'Cantidad'),
        p('Bloque II Medida'),
        lista('Magnitudes'),
    )
    assert doc['avisos'] == []
    i, ii = doc['secciones'][SECCION]['saberes']
    assert (i['romano'], i['titulo'], i['descripcion']) == ('I', 'Sentido numérico', 'Descripción del bloque.')
    assert [h['texto'] for h in i['hijos']] == ['Conteo', 'Cantidad']
    # La numeración escrita a mano se quita y el espacio de no separación se normaliza.
    assert [h['texto'] for h in i['hijos'][0]['hijos']] == ['Contar hasta diez', 'Contar hacia atrás']
    assert (ii['romano'], ii['titulo'], [h['texto'] for h in ii['hijos']]) == ('II', 'Medida', ['Magnitudes'])


def test_apartados_numerados_a_mano(crear_odt):
    # Como en Historia de Canarias (Bachillerato): el apartado es un párrafo suelto y sus
    # saberes, una lista de segundo nivel.
    doc = _leer(crear_odt, p(SECCION), p('Saberes básicos'), p('I. Historia'),
                p('1. Primer apartado'), lista(('', lista('Saber del apartado'))))
    (bloque,) = doc['secciones'][SECCION]['saberes']
    (apartado,) = bloque['hijos']
    assert apartado['texto'] == 'Primer apartado'
    assert [h['texto'] for h in apartado['hijos']] == ['Saber del apartado']


def test_texto_en_nfc():
    el = ET.fromstring('<p xmlns="urn:oasis:names:tc:opendocument:xmlns:text:1.0">Educación</p>')
    assert odt._texto(el) == 'Educación'


def test_seccion_ausente(crear_odt):
    doc = _leer(crear_odt, p('Otra cosa'))
    assert doc['avisos'] == [f'Secciones del manifiesto no encontradas: {SECCION}']
