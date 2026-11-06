from herramientas.construir import _materias_curso
from herramientas.validar import validar


def _nodos():
    return {
        'etapa:ESO': {'id': 'etapa:ESO', 'tipo': 'Etapa'},
        'curso:S01': {'id': 'curso:S01', 'tipo': 'Curso', 'prefLabel': '1º ESO'},
        'curso:S02': {'id': 'curso:S02', 'tipo': 'Curso', 'prefLabel': '2º ESO'},
        'materia:SMAT': {'id': 'materia:SMAT', 'tipo': 'Materia', 'notation': 'SMAT', 'prefLabel': 'Matemáticas (ESO)',
                         'cursos': ['curso:S01', 'curso:S02'], 'etapa': 'etapa:ESO'},
        'ce:SMATC1': {'id': 'ce:SMATC1', 'tipo': 'CompetenciaEspecifica', 'broader': 'materia:SMAT',
                      'materia': 'materia:SMAT', 'etapa': 'etapa:ESO'},
        'bc:SMAT01BC1': {'id': 'bc:SMAT01BC1', 'tipo': 'BloqueCompetencial', 'broader': 'materia:SMAT',
                         'materia': 'materia:SMAT', 'curso': 'curso:S01', 'etapa': 'etapa:ESO'},
        'sb:SMAT01SBI': {'id': 'sb:SMAT01SBI', 'tipo': 'BloqueSaberes', 'broader': 'materia:SMAT',
                         'materia': 'materia:SMAT', 'curso': 'curso:S01', 'etapa': 'etapa:ESO'},
        'sb:SMAT01SBI.1': {'id': 'sb:SMAT01SBI.1', 'tipo': 'SaberBasico', 'broader': 'sb:SMAT01SBI',
                           'materia': 'materia:SMAT', 'curso': 'curso:S01', 'etapa': 'etapa:ESO'},
    }


def test_materia_en_curso():
    nodos = _nodos()
    _materias_curso(nodos)
    assert nodos['asig:SMAT01'] == {'id': 'asig:SMAT01', 'tipo': 'MateriaCurso', 'notation': 'SMAT01',
                                    'prefLabel': 'Matemáticas · 1º ESO', 'broader': 'materia:SMAT',
                                    'materia': 'materia:SMAT', 'curso': 'curso:S01', 'etapa': 'etapa:ESO'}
    # Uno por cada curso de la materia, aunque aún no tenga bloques.
    assert nodos['asig:SMAT02']['curso'] == 'curso:S02'
    # Los bloques del curso cuelgan de él; los saberes siguen colgando de su bloque.
    assert nodos['bc:SMAT01BC1']['broader'] == 'asig:SMAT01'
    assert nodos['sb:SMAT01SBI']['broader'] == 'asig:SMAT01'
    assert nodos['sb:SMAT01SBI.1']['broader'] == 'sb:SMAT01SBI'
    assert nodos['sb:SMAT01SBI.1']['materia_curso'] == 'asig:SMAT01'
    # Las competencias son de la etapa: siguen colgando de la materia y no llevan curso.
    assert nodos['ce:SMATC1']['broader'] == 'materia:SMAT' and 'materia_curso' not in nodos['ce:SMATC1']


def _reglas(nodos):
    corpus = {'corpus': {'marco': 'm', 'ambito': 'a', 'version': '0', 'base': {}, 'normas': []},
              'nodos': list(nodos.values())}
    return {a['regla'] for a in validar(corpus, {})}


def test_nodo_que_cuelga_de_uno_retirado():
    def saber(nid, **extra):
        return {'id': nid, 'tipo': 'SaberBasico', 'notation': nid[3:], 'prefLabel': nid[3:], **extra}
    nodos = {'sb:X01SBI.1': saber('sb:X01SBI.1', obsoleto=True),
             'sb:X01SBI.1.1': saber('sb:X01SBI.1.1', broader='sb:X01SBI.1'),
             'sb:X01SBI.2': saber('sb:X01SBI.2', obsoleto=True, sustituido_por='sb:X01SBI.1')}
    reglas = _reglas(nodos)
    assert {'padre_obsoleto', 'sustituto_obsoleto'} <= reglas
