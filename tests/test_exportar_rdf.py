import copy

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, SKOS

from herramientas import exportar_rdf
from herramientas.comun import CONFIG, leer_yaml

BASE = 'https://ejemplo.org/cur/'
CUR = exportar_rdf.espacio_cur()
DESCRIPTORES = [{'etapa': 'etapa:ESO', 'codigo': 'CCL1', 'competencia': 'Competencia en comunicación lingüística'},
                {'etapa': 'etapa:ESO', 'codigo': 'STEM1', 'competencia': 'Competencia STEM'}]


def _n(nid, tipo, **campos):
    return {'id': nid, 'tipo': tipo, 'notation': nid.split(':')[1], 'prefLabel': nid, **campos}


ATAJOS = {'materia': 'materia:SMAT', 'materia_curso': 'asig:SMAT01', 'curso': 'curso:S01', 'etapa': 'etapa:ESO'}
CORPUS = {'corpus': {'marco': 'LOMLOE', 'ambito': 'Canarias', 'version': '1.0.0',
                     'licencia': {'url': 'https://creativecommons.org/licenses/by/4.0/'}},
          'nodos': [
              _n('etapa:ESO', 'Etapa'),
              _n('curso:S01', 'Curso', broader='etapa:ESO', etapa='etapa:ESO'),
              _n('materia:SMAT', 'Materia', cursos=['curso:S01'], etapa='etapa:ESO'),
              _n('asig:SMAT01', 'MateriaCurso', broader='materia:SMAT', materia='materia:SMAT', curso='curso:S01',
                 etapa='etapa:ESO'),
              _n('ce:SMATC1', 'CompetenciaEspecifica', definition='Resolver problemas.', broader='materia:SMAT',
                 materia='materia:SMAT', etapa='etapa:ESO', enunciados_curso={'curso:S01': 'Resolver problemas sencillos.'}),
              _n('bc:SMAT01BC1', 'BloqueCompetencial', broader='asig:SMAT01', agrupa=['ce:SMATC1'],
                 descriptores=['CCL1', 'STEM1'], **ATAJOS),
              _n('crit:SMAT01CE1.1', 'CriterioEvaluacion', definition='Interpretar problemas.', broader='ce:SMATC1',
                 bloque='bc:SMAT01BC1', descriptores=['STEM1'], **ATAJOS),
              _n('sb:SMAT01SBI', 'BloqueSaberes', definition='Sentido numérico', broader='asig:SMAT01', **ATAJOS),
              _n('sb:SMAT01SBI.1', 'SaberBasico', definition='Conteo.', broader='sb:SMAT01SBI', **ATAJOS),
              _n('sb:SMAT01SBI.2', 'SaberBasico', definition='Texto retirado.', broader='sb:SMAT01SBI', obsoleto=True,
                 sustituido_por='sb:SMAT01SBI.1', **ATAJOS),
          ]}


def _u(nid):
    return exportar_rdf.uri(BASE, nid)


def _grafo(corpus=CORPUS):
    return exportar_rdf.grafo(corpus, DESCRIPTORES, BASE)


def test_uris_y_tipos():
    g = _grafo()
    crit = URIRef(BASE + 'id/crit/SMAT01CE1.1')
    assert {SKOS.Concept, CUR.CriterioEvaluacion, exportar_rdf.SCHEMA.DefinedTerm} <= set(g.objects(crit, RDF.type))
    assert g.value(crit, DCTERMS.identifier) == Literal('crit:SMAT01CE1.1')
    assert g.value(crit, SKOS.definition) == Literal('Interpretar problemas.', lang='es')
    assert g.value(crit, SKOS.inScheme) == URIRef(BASE + 'id/curriculo')


def test_jerarquia_y_enlaces():
    g = _grafo()
    assert (_u('crit:SMAT01CE1.1'), SKOS.broader, _u('ce:SMATC1')) in g
    assert (_u('ce:SMATC1'), SKOS.narrower, _u('crit:SMAT01CE1.1')) in g
    assert (_u('crit:SMAT01CE1.1'), CUR.bloqueCompetencial, _u('bc:SMAT01BC1')) in g
    assert (_u('crit:SMAT01CE1.1'), CUR.materiaCurso, _u('asig:SMAT01')) in g
    assert (_u('bc:SMAT01BC1'), CUR.agrupa, _u('ce:SMATC1')) in g
    assert (_u('materia:SMAT'), CUR.curso, _u('curso:S01')) in g
    assert (_u('etapa:ESO'), SKOS.topConceptOf, URIRef(BASE + 'id/curriculo')) in g


def test_descriptores_operativos():
    g = _grafo()
    stem1 = URIRef(BASE + 'id/descriptor/ESO/STEM1')
    assert (_u('crit:SMAT01CE1.1'), CUR.descriptorOperativo, stem1) in g
    assert g.value(stem1, SKOS.broader) == URIRef(BASE + 'id/competencia-clave/STEM')
    assert (URIRef(BASE + 'id/competencia-clave/STEM'), RDF.type, CUR.CompetenciaClave) in g


def test_enunciado_por_curso_y_obsoletos():
    g = _grafo()
    (e,) = g.objects(_u('ce:SMATC1'), CUR.enunciadoEnCurso)
    assert g.value(e, CUR.curso) == _u('curso:S01')
    assert g.value(e, SKOS.definition) == Literal('Resolver problemas sencillos.', lang='es')
    assert g.value(_u('sb:SMAT01SBI.2'), OWL.deprecated) == Literal(True)
    assert g.value(_u('sb:SMAT01SBI.2'), DCTERMS.isReplacedBy) == _u('sb:SMAT01SBI.1')


def test_formas_shacl():
    assert exportar_rdf.validar_grafo(_grafo())[0]
    # Un criterio sin bloque competencial y un saber que cuelga de la materia no las cumplen.
    roto = copy.deepcopy(CORPUS)
    nodos = {n['id']: n for n in roto['nodos']}
    del nodos['crit:SMAT01CE1.1']['bloque']
    nodos['sb:SMAT01SBI.1']['broader'] = 'materia:SMAT'
    conforme, informe = exportar_rdf.validar_grafo(_grafo(roto))
    assert not conforme
    assert 'bloqueCompetencial' in informe and 'SMAT01SBI.1' in informe


def test_vocabulario_declara_lo_que_se_usa():
    vocabulario = Graph().parse(exportar_rdf.VOCABULARIO)
    usados = {t for tripleta in _grafo() for t in tripleta if isinstance(t, URIRef) and str(t).startswith(str(CUR))}
    assert usados and all((t, RDF.type, None) in vocabulario for t in usados)


def test_base_de_config_y_vocabulario_coinciden():
    base = leer_yaml(CONFIG / 'corpus.yaml')['rdf']['base']
    assert str(CUR) == base + 'def/cur#'
