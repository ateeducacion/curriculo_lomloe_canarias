from herramientas.boletin import Boletin

TEXTO = '''Boletín Oficial de Canarias núm. 58
Jueves 23 de marzo de 2023
1.1. Diseñar soluciones sencillas a problemas de la vida cotidiana con herramien-
tas digitales, aplicando estrategias de diseño CCL1, STEM1, STEM2 utilizando
los recursos disponibles en el aula.
https://sede.gobiernodecanarias.org/boc
15478
4. Conocimiento básico de la normativa relativa a la protección de datos personales; gestión consciente
de la cesión de datos.
'''


def test_quita_cabeceras_y_une_palabras_partidas():
    b = Boletin(TEXTO)
    assert b.contiene('problemas de la vida cotidiana con herramientas digitales')
    assert not b.contiene('Boletín Oficial de Canarias')
    assert not b.contiene('Jueves 23 de marzo')


def test_quita_descriptores_intercalados():
    b = Boletin(TEXTO)
    assert b.exacto('aplicando estrategias de diseño utilizando los recursos disponibles en el aula')


def test_contiene_ignora_la_puntuacion_y_literal_no():
    b = Boletin(TEXTO)
    assert b.contiene('protección de datos personales, gestión consciente de la cesión de datos')
    assert b.contiene_literal('protección de datos personales; gestión consciente de la cesión de datos.')
    assert not b.contiene_literal('protección de datos personales, gestión consciente de la cesión de datos.')


def test_exacto_no_admite_prefijos_de_palabra():
    b = Boletin(TEXTO)
    assert not b.exacto('la cesión de dat')


def test_texto_largo_tolera_un_trozo_si_no_es_exacto():
    palabras = ' '.join(f'palabra{i}' for i in range(50))
    b = Boletin(palabras)
    alterado = palabras.replace('palabra15', 'otra')
    assert b.contiene(alterado)
    assert not b.exacto(alterado)


def test_descriptores_completos_sin_otros_pegados():
    b = Boletin(TEXTO)
    assert b.contiene_descriptores(['CCL1', 'STEM1', 'STEM2'])
    assert not b.contiene_descriptores(['CCL1', 'STEM1'])
    assert not b.contiene_descriptores(['STEM1', 'STEM2'])
    assert not b.contiene_descriptores([])
