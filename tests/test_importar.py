import copy

from herramientas.importar_proideac import importar

EXPORTACION = {
    'ESO': {
        '1.º ESO': {
            'MAT': {
                'denominacion': 'Matemáticas',
                'competencias_especificas': {
                    'SMATC1': {
                        'descripcion': 'Enunciado de la competencia.',
                        'explicacion_bloque_competencial': 'Explicación del bloque.',
                        'criterios_evaluacion': [
                            {'codigo': 'SMAT01CE1.1', 'descripcion': 'Primer criterio.', 'competencias_clave': ['CCL1', ' STEM1']},
                            {'codigo': 'SMAT01CE1.2', 'descripcion': 'Segundo criterio.', 'competencias_clave': ['STEM1', 'CD1']},
                        ],
                    },
                },
                'saberes_basicos': {'bloques': {'I. Sentido numérico': [
                    {'nombre': 'SMAT01SBI.1.1', 'subtitulo_nivel_1': '1. Conteo', 'subtitulo_nivel_2': '1.1. Contar hasta diez.'},
                    {'nombre': 'SMAT01SBI.1.2', 'subtitulo_nivel_1': '1. Conteo', 'subtitulo_nivel_2': '1.2. Contar hacia atrás.'},
                ]}},
            },
        },
    },
}


def _reglas(imp):
    return [a['regla'] for a in imp.avisos]


def test_estructura():
    imp = importar(copy.deepcopy(EXPORTACION))
    n = imp.nodos
    assert n['etapa:ESO']['tipo'] == 'Etapa'
    assert n['curso:S01']['broader'] == 'etapa:ESO'
    assert n['materia:SMAT']['prefLabel'] == 'Matemáticas (ESO)'
    assert n['ce:SMATC1']['definition'] == 'Enunciado de la competencia.'
    bc = n['bc:SMAT01BC1']
    assert bc['scopeNote'] == 'Explicación del bloque.'
    # Los descriptores del bloque son la unión de los de sus criterios, sin repetir.
    assert bc['descriptores'] == ['CCL1', 'STEM1', 'CD1']
    assert n['crit:SMAT01CE1.1']['descriptores'] == ['CCL1', 'STEM1']
    assert n['crit:SMAT01CE1.1']['bloque'] == 'bc:SMAT01BC1'
    assert n['sb:SMAT01SBI']['definition'] == 'Sentido numérico'
    assert n['sb:SMAT01SBI.1']['definition'] == 'Conteo'
    assert n['sb:SMAT01SBI.1.2']['definition'] == 'Contar hacia atrás.'
    assert n['sb:SMAT01SBI.1.2']['broader'] == 'sb:SMAT01SBI.1'
    assert 'error' not in {a['nivel'] for a in imp.avisos}


def test_textos_en_nfc():
    exp = copy.deepcopy(EXPORTACION)
    exp['ESO']['1.º ESO']['MAT']['competencias_especificas']['SMATC1']['descripcion'] = 'Educación'
    assert importar(exp).nodos['ce:SMATC1']['definition'] == 'Educación'


def test_registro_repetido_de_forma_identica():
    exp = copy.deepcopy(EXPORTACION)
    items = exp['ESO']['1.º ESO']['MAT']['saberes_basicos']['bloques']['I. Sentido numérico']
    items.append(dict(items[0]))
    assert 'registro_repetido' in _reglas(importar(exp))


def test_codigo_con_punto_final():
    exp = copy.deepcopy(EXPORTACION)
    items = exp['ESO']['1.º ESO']['MAT']['saberes_basicos']['bloques']['I. Sentido numérico']
    items.append({'nombre': 'SMAT01SBI.1.3.', 'subtitulo_nivel_1': '1. Conteo', 'subtitulo_nivel_2': '1.3. Estimar.'})
    imp = importar(exp)
    assert imp.nodos['sb:SMAT01SBI.1.3']['definition'] == 'Estimar.'
    assert 'codigo_saber_reconstruido' in _reglas(imp)


def test_criterio_de_otro_curso():
    exp = copy.deepcopy(EXPORTACION)
    exp['ESO']['1.º ESO']['MAT']['competencias_especificas']['SMATC1']['criterios_evaluacion'][0]['codigo'] = 'SMAT02CE1.1'
    assert 'criterio_curso_inconsistente' in _reglas(importar(exp))


def test_posible_secreto_en_clave_de_bloque():
    exp = copy.deepcopy(EXPORTACION)
    clave = 'ghp_' + 'x' * 24   # se compone en ejecución para que el escaneo de secretos no lo detecte aquí
    exp['ESO']['1.º ESO']['MAT']['saberes_basicos']['bloques'][clave] = []
    assert 'posible_secreto' in _reglas(importar(exp))


def test_etapa_desconocida():
    assert 'etapa_desconocida' in _reglas(importar({'FP': {}}))
