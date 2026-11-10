import json
import re

import pytest
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import RDF, SKOS

from herramientas import exportar_rdf, sitio
from tests.test_exportar_rdf import BASE, CORPUS, DESCRIPTORES


def _grafo():
    return exportar_rdf.grafo(CORPUS, DESCRIPTORES, BASE)


@pytest.fixture
def web(tmp_path):
    g = _grafo()
    destino = tmp_path / 'sitio'
    sitio.generar(g, BASE, destino)
    return g, destino


def _sujetos(g):
    return {s for s in g.subjects() if isinstance(s, URIRef) and str(s).startswith(BASE + 'id/')}


def test_cada_sujeto_tiene_ficha_y_turtle(web):
    g, destino = web
    for s in _sujetos(g):
        carpeta = destino / str(s)[len(BASE):]
        assert (carpeta / 'index.html').is_file() and (carpeta / 'index.ttl').is_file()


def test_turtle_es_la_descripcion_del_sujeto(web):
    g, destino = web
    ce = URIRef(BASE + 'id/ce/SMATC1')
    d = Graph().parse(destino / 'id/ce/SMATC1/index.ttl')
    sin_blancos = lambda pares: {(p, o) for p, o in pares if not isinstance(o, BNode)}
    assert sin_blancos(d.predicate_objects(ce)) == sin_blancos(g.predicate_objects(ce))
    assert set(d.subjects()) - {ce}   # el enunciado por curso (nodo en blanco) va incluido
    assert Literal('Resolver problemas sencillos.', lang='es') in set(d.objects(None, SKOS.definition))


def test_enlaces_internos_existen(web):
    _, destino = web
    for f in destino.rglob('index.html'):
        for href in re.findall(r'href="([^"]+)"', f.read_text(encoding='utf-8')):
            if href.startswith(BASE + 'id/'):
                assert (destino / href[len(BASE):] / 'index.html').is_file(), (f, href)


def test_ficha_retirado(web):
    _, destino = web
    texto = (destino / 'id/sb/SMAT01SBI.2/index.html').read_text(encoding='utf-8')
    assert 'retirado' in texto.lower()
    assert f'href="{BASE}id/sb/SMAT01SBI.1"' in texto


def test_ficha_enlaza_turtle_y_escapa(tmp_path):
    g = _grafo()
    crit = URIRef(BASE + 'id/crit/SMAT01CE1.1')
    g.set((crit, SKOS.definition, Literal('a < b & "c"', lang='es')))
    sitio.generar(g, BASE, tmp_path / 's')
    texto = (tmp_path / 's/id/crit/SMAT01CE1.1/index.html').read_text(encoding='utf-8')
    assert '<link rel="alternate" type="text/turtle" href="index.ttl">' in texto
    assert 'a &lt; b &amp; &quot;c&quot;' in texto and 'a < b' not in texto


def test_nombre_sin_notacion_repetida(tmp_path):
    g = _grafo()
    crit = URIRef(BASE + 'id/crit/SMAT01CE1.1')
    g.set((crit, SKOS.prefLabel, Literal('SMAT01CE1.1 · Interpretar', lang='es')))
    sitio.generar(g, BASE, tmp_path / 's')
    texto = (tmp_path / 's/id/crit/SMAT01CE1.1/index.html').read_text(encoding='utf-8')
    assert 'SMAT01CE1.1 · SMAT01CE1.1' not in texto and '<title>Criterio de evaluación 1.1 · SMAT01CE1.1' in texto


def test_orden_natural(tmp_path):
    g = _grafo()
    sb = URIRef(BASE + 'id/sb/SMAT01SBI')
    for n in (10, 3):
        h = URIRef(f'{BASE}id/sb/SMAT01SBI.{n}')
        g.add((sb, SKOS.narrower, h))
        g.add((h, SKOS.notation, Literal(f'SMAT01SBI.{n}')))
    sitio.generar(g, BASE, tmp_path / 's')
    texto = (tmp_path / 's/id/sb/SMAT01SBI/index.html').read_text(encoding='utf-8')
    assert texto.index('SBI.2"') < texto.index('SBI.3"') < texto.index('SBI.10"')


def test_enlace_roto(tmp_path):
    g = _grafo()
    g.add((URIRef(BASE + 'id/crit/SMAT01CE1.1'), SKOS.related, URIRef(BASE + 'id/crit/NOEXISTE')))
    with pytest.raises(ValueError, match='NOEXISTE'):
        sitio.generar(g, BASE, tmp_path / 's')


def test_base_sin_sujetos(tmp_path):
    with pytest.raises(ValueError, match='base'):
        sitio.generar(_grafo(), 'https://otra.org/', tmp_path / 's')


@pytest.mark.parametrize('cola', ['id/crit/../../x', 'id/crit//x', 'id/crit/x/', 'id/crit/x?y'])
def test_ruta_insegura(cola):
    with pytest.raises(ValueError):
        sitio.ruta(BASE, URIRef(BASE + cola))


def test_vocabulario_y_portada(web):
    _, destino = web
    voc = Graph().parse(exportar_rdf.VOCABULARIO)
    cur = str(exportar_rdf.espacio_cur())
    texto = (destino / 'def/cur/index.html').read_text(encoding='utf-8')
    terminos = {t for t in voc.subjects(RDF.type, None) if str(t).startswith(cur)}
    assert terminos and all(f'id="{str(t)[len(cur):]}"' in texto for t in terminos)
    assert (destino / 'def/cur.ttl').read_bytes() == exportar_rdf.VOCABULARIO.read_bytes()
    portada = (destino / 'index.html').read_text(encoding='utf-8')
    assert f'{BASE}id/curriculo' in portada and 'releases/tag/v1.0.0' in portada
    assert (destino / '.nojekyll').exists()


def test_main_no_borra_carpetas_ajenas(tmp_path):
    ttl = tmp_path / 'c.ttl'
    _grafo().serialize(ttl, format='turtle')
    ajena = tmp_path / 'ajena'
    ajena.mkdir()
    (ajena / 'dato.txt').write_text('x')
    with pytest.raises(SystemExit):
        sitio.main(['--ttl', str(ttl), '--destino', str(ajena), '--base', BASE])
    assert (ajena / 'dato.txt').exists()
    destino = tmp_path / 'sitio'
    assert sitio.main(['--ttl', str(ttl), '--destino', str(destino), '--base', BASE]) == 0
    assert sitio.main(['--ttl', str(ttl), '--destino', str(destino), '--base', BASE]) == 0  # regenera
    assert (destino / 'id/crit/SMAT01CE1.1/index.html').is_file()


def _alcanzables(destino, base):
    """Rutas id/... a las que se llega navegando desde la portada."""
    vistas, pendientes = set(), [destino / 'index.html']
    while pendientes:
        texto = pendientes.pop().read_text(encoding='utf-8')
        for href in re.findall(r'href="([^"#]+)"', texto):
            if href.startswith(base + 'id/') and href not in vistas:
                vistas.add(href)
                pendientes.append(destino / href[len(base):] / 'index.html')
    return {h[len(base):] for h in vistas}


def test_desde_la_portada_se_llega_a_todo(web):
    g, destino = web
    assert _alcanzables(destino, BASE) == {str(s)[len(BASE):] for s in _sujetos(g)}


def test_etapa_y_curso_enlazan_el_nivel_siguiente(web):
    _, destino = web
    assert f'href="{BASE}id/materia/SMAT"' in (destino / 'id/etapa/ESO/index.html').read_text(encoding='utf-8')
    assert f'href="{BASE}id/asig/SMAT01"' in (destino / 'id/curso/S01/index.html').read_text(encoding='utf-8')


def test_sin_css_en_linea_y_recursos(web):
    _, destino = web
    for f in destino.rglob('index.html'):
        texto = f.read_text(encoding='utf-8')
        assert '<style' not in texto, f
        assert f'href="{BASE}recursos/estilo.css"' in texto, f
    for r in ('estilo.css', 'buscar.js', 'minisearch.js', 'minisearch.LICENSE'):
        assert (destino / 'recursos' / r).is_file()


def test_base_de_vista_previa(tmp_path):
    otra = 'http://localhost:8000/'
    g = Graph()
    for s, p, o in _grafo():
        cambia = lambda x: URIRef(str(x).replace(BASE, otra)) if isinstance(x, URIRef) else x
        g.add((cambia(s), cambia(p), cambia(o)))
    sitio.generar(g, otra, tmp_path / 's')
    portada = (tmp_path / 's/index.html').read_text(encoding='utf-8')
    assert f'{otra}recursos/estilo.css' in portada and f'action="{otra}buscar/"' in portada


def _u(x):
    return URIRef(BASE + x)


def test_curriculo_navegacion():
    from herramientas.sitio.datos import Curriculo
    c = Curriculo(_grafo(), BASE)
    assert c.tipo(_u('id/crit/SMAT01CE1.1')) == 'CriterioEvaluacion'
    assert c.numero(_u('id/crit/SMAT01CE1.1')) == '1.1' and c.numero(_u('id/ce/SMATC1')) == 'C1'
    assert c.numero(_u('id/sb/SMAT01SBI')) == 'I' and c.numero(_u('id/sb/SMAT01SBI.1')) == '1'
    assert c.con('materiaCurso', _u('id/asig/SMAT01'), 'CriterioEvaluacion') == [_u('id/crit/SMAT01CE1.1')]
    assert c.hijos(_u('id/sb/SMAT01SBI')) == [_u('id/sb/SMAT01SBI.1'), _u('id/sb/SMAT01SBI.2')]
    assert c.retirado(_u('id/sb/SMAT01SBI.2')) and c.sustituto(_u('id/sb/SMAT01SBI.2')) == _u('id/sb/SMAT01SBI.1')
    assert c.enunciado(_u('id/ce/SMATC1'), _u('id/curso/S01')) == 'Resolver problemas sencillos.'
    assert [u for u, _ in c.migas(_u('id/sb/SMAT01SBI.1'))] == [
        BASE, str(_u('id/etapa/ESO')), str(_u('id/curso/S01')), str(_u('id/asig/SMAT01')), str(_u('id/sb/SMAT01SBI')), None]
    assert [(str(u), cod) for u, cod, _ in c.descriptores(_u('id/crit/SMAT01CE1.1'))] == [
        (BASE + 'id/descriptor/ESO/STEM1', 'STEM1')]


def _pagina(destino, ruta):
    return (destino / ruta / 'index.html').read_text(encoding='utf-8')


def test_materia_en_curso_con_pestanas(web):
    _, destino = web
    t = _pagina(destino, 'id/asig/SMAT01')
    assert 'role="tablist"' in t and 'id="p-competencias"' in t and 'id="p-saberes"' in t and 'id="p-bloques"' in t
    comp = t[t.index('id="p-competencias"'):t.index('id="p-saberes"')]
    # el criterio va bajo su competencia, con el enunciado del curso y sus descriptores
    assert comp.index('SMATC1') < comp.index('SMAT01CE1.1')
    assert 'Resolver problemas sencillos.' in comp and 'class="chip"' in comp
    saberes = t[t.index('id="p-saberes"'):t.index('id="p-bloques"')]
    assert 'class="arbol"' in saberes and 'Sentido numérico' in saberes and 'Conteo.' in saberes
    assert 'class="retirado"' in saberes   # el retirado sigue enlazado, marcado


def test_ficha_criterio_para_personas(web):
    _, destino = web
    t = _pagina(destino, 'id/crit/SMAT01CE1.1')
    assert 'Criterio de evaluación' in t and 'Interpretar problemas.' in t
    for rotulo in ('Competencia específica', 'Bloque competencial', 'Descriptores operativos'):
        assert rotulo in t
    for tecnico in ('Superior', 'Esquema', 'bloque competencial</dt>'):
        assert tecnico not in t
    assert '<details class="tecnico">' in t and 'href="index.ttl"' in t
    assert '<nav class="migas"' in t and f'href="{BASE}id/asig/SMAT01"' in t


def test_portada_etapa_y_curso(web):
    _, destino = web
    portada = (destino / 'index.html').read_text(encoding='utf-8')
    assert 'role="search"' in portada and f'href="{BASE}id/etapa/ESO"' in portada
    assert f'href="{BASE}id/curso/S01"' in _pagina(destino, 'id/etapa/ESO')
    curso = _pagina(destino, 'id/curso/S01')
    assert f'href="{BASE}id/asig/SMAT01"' in curso and '1 criterio' in curso


def test_materia_en_curso_vacia(tmp_path):
    g = _grafo()
    asig = URIRef(BASE + 'id/asig/SMAT02')
    cur = exportar_rdf.espacio_cur()
    g.add((asig, RDF.type, cur.MateriaCurso))
    g.add((asig, SKOS.notation, Literal('SMAT02')))
    g.add((asig, SKOS.prefLabel, Literal('Matemáticas · 2º ESO', lang='es')))
    g.add((asig, cur.materia, URIRef(BASE + 'id/materia/SMAT')))
    g.add((asig, cur.curso, URIRef(BASE + 'id/curso/S01')))
    g.add((asig, cur.etapa, URIRef(BASE + 'id/etapa/ESO')))
    sitio.generar(g, BASE, tmp_path / 's')
    t = (tmp_path / 's/id/asig/SMAT02/index.html').read_text(encoding='utf-8')
    assert 'Sin criterios en este curso' in t and 'Sin saberes en este curso' in t


def test_ficha_retirado_con_sustituto(web):
    _, destino = web
    t = _pagina(destino, 'id/sb/SMAT01SBI.2')
    assert 'class="aviso"' in t and f'href="{BASE}id/sb/SMAT01SBI.1"' in t


def test_main_vista_previa_con_otra_base(tmp_path, monkeypatch):
    ttl = tmp_path / 'c.ttl'
    _grafo().serialize(ttl, format='turtle')
    monkeypatch.setattr(sitio, 'base_uri', lambda: BASE)
    otra = 'http://localhost:8000/'
    assert sitio.main(['--ttl', str(ttl), '--destino', str(tmp_path / 's'), '--base', otra]) == 0
    t = (tmp_path / 's/id/crit/SMAT01CE1.1/index.html').read_text(encoding='utf-8')
    assert f'href="{otra}id/ce/SMATC1"' in t and BASE not in t


def test_indice_de_busqueda(web):
    _, destino = web
    datos = json.loads((destino / 'buscar.json').read_text(encoding='utf-8'))
    por_url = {d['u']: d for d in datos}
    crit = por_url[BASE + 'id/crit/SMAT01CE1.1']
    assert crit == {'u': BASE + 'id/crit/SMAT01CE1.1', 'c': 'SMAT01CE1.1', 't': 'Interpretar problemas.',
                    'k': 'Criterio de evaluación', 'r': crit['r'], 'e': 'ESO', 'm': crit['m']}
    assert 'Matemáticas' in crit['r'] or 'SMAT' in crit['r']
    assert BASE + 'id/sb/SMAT01SBI.2' not in por_url          # retirado fuera
    assert BASE + 'id/etapa/ESO' not in por_url               # etapas y cursos fuera
    from herramientas.sitio.datos import ROTULOS
    assert {d['k'] for d in datos} <= set(ROTULOS.values())
    buscar = (destino / 'buscar' / 'index.html').read_text(encoding='utf-8')
    assert 'id="resultados"' in buscar and '<noscript>' in buscar


def test_indice_admite_texto_raro(tmp_path):
    g = _grafo()
    g.set((URIRef(BASE + 'id/crit/SMAT01CE1.1'), SKOS.definition, Literal('a < b & "c" \\ ñ', lang='es')))
    sitio.generar(g, BASE, tmp_path / 's')
    datos = json.loads((tmp_path / 's/buscar.json').read_text(encoding='utf-8'))
    assert any(d['t'] == 'a < b & "c" \\ ñ' for d in datos)
