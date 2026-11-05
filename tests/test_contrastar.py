from herramientas import contrastar
from herramientas.boletin import Boletin


def _saber(nid, texto):
    return {'id': nid, 'tipo': 'SaberBasico', 'definition': texto}


def _diferencias(nodos, base, hijos):
    dif, vistos = [], set()

    def d(tipo, nodo, detalle='', campo=None, esperado=None, **extra):
        dif.append({'tipo': tipo, 'nodo': nodo, 'campo': campo, 'esperado': esperado})
    contrastar._saberes(d, nodos, base, hijos, vistos)
    return dif, vistos


def _hijos(*textos):
    return [{'texto': t, 'hijos': []} for t in textos]


def test_saberes_se_emparejan_por_contenido_y_no_por_numero():
    nodos = {k: _saber(k, t) for k, t in [('sb:X01SBI.1', 'Conteo de objetos.'), ('sb:X01SBI.2', 'Medida de longitudes.')]}
    dif, vistos = _diferencias(nodos, 'sb:X01SBI', _hijos('Conteo de objetos.', 'Saber nuevo del documento.',
                                                          'Medida de longitudes.'))
    # Solo falta el saber nuevo; «Medida» no se compara con el que ocupa su número en el documento.
    assert dif == [{'tipo': 'falta en el corpus: texto de saber', 'nodo': 'sb:X01SBI.2',
                    'campo': 'definition', 'esperado': 'Saber nuevo del documento.'}]
    assert vistos == {'sb:X01SBI.1', 'sb:X01SBI.2'}


def test_saber_con_texto_distinto():
    nodos = {'sb:X01SBI.1': _saber('sb:X01SBI.1', 'Conteo de objetos')}
    dif, _ = _diferencias(nodos, 'sb:X01SBI', _hijos('Conteo de objetos.'))
    assert [(x['tipo'], x['esperado']) for x in dif] == [('texto de saber distinto', 'Conteo de objetos.')]


def test_saber_sobrante_queda_fuera_de_vistos():
    nodos = {k: _saber(k, t) for k, t in [('sb:X01SBI.1', 'Conteo de objetos.'), ('sb:X01SBI.2', 'Texto antiguo.')]}
    dif, vistos = _diferencias(nodos, 'sb:X01SBI', _hijos('Conteo de objetos.'))
    assert dif == [] and vistos == {'sb:X01SBI.1'}


BOC = Boletin('Uso de estrategias de cálculo mental con números naturales hasta el millar en contextos cotidianos.')


def _explicar(nodo, campo, actual, esperado, tipo='texto de saber distinto'):
    nodos = {nodo: {'id': nodo, campo: actual}}
    x = {'tipo': tipo, 'nodo': nodo, 'campo': campo, 'esperado': esperado}
    return contrastar._explicacion_automatica(x, nodos, BOC, conocidos={'CCL1', 'STEM1'})


def test_explicacion_corpus_publicado_en_el_boc():
    publicado = 'Uso de estrategias de cálculo mental con números naturales hasta el millar en contextos cotidianos.'
    assert _explicar('sb:X', 'definition', publicado, 'Uso de estrategias de cálculo escrito.') == \
        'el texto del corpus es el publicado en el BOC; el del documento no'


def test_sin_explicacion_si_el_boc_no_decide():
    assert _explicar('sb:X', 'definition', 'Texto A distinto.', 'Texto B distinto.') is None


def test_descriptores_con_codigo_inexistente_son_errata():
    assert _explicar('crit:X', 'descriptores', ['CCL1'], ['CCL1', 'CCE3'],
                     tipo='descriptores de criterio distinto') == \
        'el documento trae códigos de descriptor que no existen en la etapa (errata)'


def test_informe_cuenta_las_diferencias_sin_explicar():
    resultados = [{'documento': 'doc', 'estado': 'contrastado', 'diferencias': [
        {'tipo': 't', 'nodo': 'n1', 'explicacion': 'motivo'}, {'tipo': 't', 'nodo': 'n2', 'explicacion': None}]}]
    assert '**sin explicar: 1**' in contrastar.informe_md(resultados)


def test_numeracion_distinta_en_el_boc():
    boc = Boletin('Otra materia. 5.1. Valorar la diversidad lingüística y cultural de Canarias con respeto. '
                  + 'relleno ' * 3000
                  + '5.1. Valorar la diversidad lingüística y cultural de Canarias con respeto. '
                  '6.1. Registrar los progresos de aprendizaje de la lengua extranjera con apoyo. '
                  '7.1. Producir textos orales breves y sencillos sobre temas cotidianos.')
    nodos = {'crit:X01CE5.1': {'definition': 'Registrar los progresos de aprendizaje de la lengua extranjera con apoyo.'},
             'crit:X01CE6.1': {'definition': 'Valorar la diversidad lingüística y cultural de Canarias con respeto.'},
             'crit:X01CE7.1': {'definition': 'Producir textos orales breves y sencillos sobre temas cotidianos.'}}
    avisos = contrastar._numeracion_boc(nodos, boc, list(nodos))
    # El texto de 6.1 aparece también lejos, en otra materia, con el mismo número 5.1: se toma
    # la aparición de la zona de la materia, y la del 7.1 coincide.
    assert avisos == [{'nodo': 'crit:X01CE5.1', 'numero': '5.1', 'boc': '6.1'},
                      {'nodo': 'crit:X01CE6.1', 'numero': '6.1', 'boc': '5.1'}]
