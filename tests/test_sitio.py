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
    g.set((crit, SKOS.prefLabel, Literal('a < b & "c"', lang='es')))
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
    assert '<h1>SMAT01CE1.1 · Interpretar</h1>' in texto


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
