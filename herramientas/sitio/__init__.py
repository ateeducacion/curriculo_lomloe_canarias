"""Genera el sitio estático que hace resolubles las URIs del corpus en GitHub Pages.

Uso:
    python -m herramientas.sitio                                   # dist/curriculo.ttl → dist/sitio
    python -m herramientas.sitio --ttl dist/curriculo.ttl --destino dist/sitio

Cada sujeto del grafo con URI <base>id/<ruta> tiene una carpeta id/<ruta>/ con una ficha HTML
mínima (index.html) y su descripción en Turtle (index.ttl); Pages sirve <base>id/<ruta>
redirigiendo a la carpeta. Los enlaces de las fichas son las propias URIs. Además: el
vocabulario en def/cur/ (con un ancla por término) y def/cur.ttl, una portada y .nojekyll.

Falla si algún enlace apunta a una URI bajo <base>id/ que no está en el grafo, o si no hay
ningún sujeto bajo la base. Solo borra el destino si es un sitio generado (tiene .nojekyll).
"""
import argparse
import re
import shutil
import sys
from html import escape
from pathlib import Path

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS

from ..comun import DIST
from ..exportar_rdf import SCHEMA, VOCABULARIO, base_uri, espacio_cur
from .plantilla import REPOSITORIO, pagina

RECURSOS = Path(__file__).parent / 'recursos'

RE_SEGMENTO = re.compile(r'^[A-Za-z0-9._-]+$')
ETIQUETAS = {
    SKOS.broader: 'Superior', SKOS.narrower: 'Inferiores', SKOS.related: 'Relacionados',
    SKOS.inScheme: 'Esquema', SKOS.topConceptOf: 'Concepto de primer nivel de',
    SKOS.hasTopConcept: 'Conceptos de primer nivel', DCTERMS.identifier: 'Identificador',
    DCTERMS.isReplacedBy: 'Sustituido por', DCTERMS.modified: 'Modificado',
    DCTERMS.license: 'Licencia', DCTERMS.source: 'Fuente', OWL.versionInfo: 'Versión',
}
ORDEN = [SKOS.broader, DCTERMS.isReplacedBy]
# (tipo del nodo, propiedad, tipo de los nodos que apuntan a él, rótulo en su ficha)
INVERSOS = [('Etapa', 'etapa', 'Materia', 'Materias'), ('Curso', 'curso', 'MateriaCurso', 'Materias en curso')]
APARTE = {RDF.type, SKOS.prefLabel, SKOS.notation, SKOS.definition, SKOS.scopeNote, OWL.deprecated}


def ruta(base, s):
    """Ruta relativa al sitio (id/...) de una URI bajo <base>id/. Rechaza segmentos raros."""
    cola = str(s)[len(base):]
    if not str(s).startswith(base + 'id/') or not all(RE_SEGMENTO.match(x) and x not in ('.', '..')
                                                      for x in cola.split('/')):
        raise ValueError(f'URI sin ruta válida en el sitio: {s}')
    return cola


def _clave_natural(texto):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', texto)]


class _Fichas:
    def __init__(self, g, base, vocabulario):
        self.g, self.base = g, base
        self.voc = Graph().parse(vocabulario)
        self.sujetos = {s for s in g.subjects() if isinstance(s, URIRef) and str(s).startswith(base + 'id/')}
        if not self.sujetos:
            raise ValueError(f'Ningún sujeto del grafo empieza por la base {base}id/')
        # Enlaces inversos del nivel siguiente, para poder bajar navegando: el grafo no los tiene
        # (la materia apunta a su etapa y la materia en curso a su curso, no al revés).
        cur = espacio_cur()
        self.inversos = {}
        for destino, prop, origen, rotulo in INVERSOS:
            hijos = {}
            for o in g.subjects(RDF.type, cur[origen]):
                for d in g.objects(o, cur[prop]):
                    if (d, RDF.type, cur[destino]) in g:
                        hijos.setdefault(d, []).append(o)
            for d, nodos in hijos.items():
                self.inversos.setdefault(d, []).append((rotulo, nodos))

    def nombre(self, u):
        notacion, etiqueta = self.g.value(u, SKOS.notation), self.g.value(u, SKOS.prefLabel)
        if notacion is not None and etiqueta is not None and str(etiqueta).startswith(str(notacion)):
            notacion = None   # muchas etiquetas ya empiezan por su notación
        return ' · '.join(str(x) for x in (notacion, etiqueta) if x is not None) or str(u)

    def enlace(self, u):
        return f'<a href="{escape(str(u))}">{escape(self.nombre(u) if u in self.sujetos else str(u))}</a>'

    def etiqueta(self, p):
        e = self.voc.value(p, RDFS.label)
        return str(e) if e is not None else ETIQUETAS.get(p) or self.g.namespace_manager.normalizeUri(p)

    def valor(self, o):
        return self.enlace(o) if isinstance(o, URIRef) else escape(str(o))

    def html(self, s):
        g, cur = self.g, str(espacio_cur())
        nombre = self.nombre(s)
        tipos = sorted((t for t in g.objects(s, RDF.type) if str(t).startswith(cur) or t == SKOS.ConceptScheme),
                       key=str)
        partes = [f'<h1>{escape(nombre)}</h1>',
                  '<p class="tipo">' + ', '.join(f'<a href="{escape(str(t))}">{escape(str(t).split("#")[-1].split("/")[-1])}</a>'
                                                 for t in tipos) + '</p>']
        if g.value(s, OWL.deprecated) == Literal(True):
            partes.append('<p class="aviso">Nodo retirado: se conserva para no romper los enlaces.</p>')
        for p, rotulo in ((SKOS.definition, 'Definición'), (SKOS.scopeNote, 'Nota')):
            for o in g.objects(s, p):
                partes.append(f'<h2>{rotulo}</h2>\n<p>{escape(str(o))}</p>')
        enunciados = []
        datos = {}
        for p, o in g.predicate_objects(s):
            if p in APARTE or str(p).startswith(str(SCHEMA)):
                continue
            if isinstance(o, BNode):
                if (o, RDF.type, URIRef(cur + 'EnunciadoEnCurso')) in g:
                    enunciados.append((g.value(o, URIRef(cur + 'curso')), g.value(o, SKOS.definition)))
                continue
            datos.setdefault(p, []).append(o)
        if enunciados:
            partes.append('<h2>Enunciados por curso</h2>\n<dl>' + ''.join(
                f'<dt>{self.valor(c)}</dt><dd>{escape(str(t))}</dd>'
                for c, t in sorted(enunciados, key=lambda e: _clave_natural(str(e[0])))) + '</dl>')
        orden = sorted(datos, key=lambda p: (ORDEN.index(p) if p in ORDEN else len(ORDEN), p == SKOS.narrower,
                                             self.etiqueta(p)))
        grupos = [(self.etiqueta(p), datos[p]) for p in orden] + self.inversos.get(s, [])
        if grupos:
            filas = []
            for rotulo, valores in grupos:
                valores = sorted(valores, key=lambda o: _clave_natural(str(g.value(o, SKOS.notation) or o)))
                items = ''.join(f'<li>{self.valor(o)}</li>' for o in valores)
                filas.append(f'<dt>{escape(rotulo)}</dt><dd><ul>{items}</ul></dd>')
            partes.append('<dl>' + ''.join(filas) + '</dl>')
        partes.append(f'<p>URI: <code>{escape(str(s))}</code> · <a href="index.ttl">Turtle</a></p>')
        cabecera = '<link rel="alternate" type="text/turtle" href="index.ttl">\n'
        return pagina(nombre, '\n'.join(partes), self.base, cabecera=cabecera)

    def turtle(self, s):
        d = Graph()
        for prefijo, ns in self.g.namespaces():
            d.bind(prefijo, ns, override=True)
        d += self.g.cbd(s)
        return d.serialize(format='turtle')

    def rotos(self):
        prefijo = self.base + 'id/'
        return sorted({str(o) for s in self.sujetos for o in self.g.objects(s, None)
                       if isinstance(o, URIRef) and str(o).startswith(prefijo) and o not in self.sujetos})


def _vocabulario(vocabulario, destino, base):
    voc = Graph().parse(vocabulario)
    cur = str(espacio_cur())
    terminos = sorted({t for t in voc.subjects(RDF.type, None) if str(t).startswith(cur)}, key=str)
    filas = []
    for t in terminos:
        local = str(t)[len(cur):]
        tipo = ', '.join(sorted(voc.namespace_manager.normalizeUri(x) for x in voc.objects(t, RDF.type)))
        detalles = ''.join(f'<li>{rotulo}: <code>{escape(voc.namespace_manager.normalizeUri(o))}</code></li>'
                           for p, rotulo in ((RDFS.subClassOf, 'subclase de'), (RDFS.domain, 'dominio'),
                                             (RDFS.range, 'rango'))
                           for o in voc.objects(t, p) if isinstance(o, URIRef))
        etiqueta = voc.value(t, RDFS.label) or local
        comentario = voc.value(t, RDFS.comment)
        filas.append(f'<section id="{escape(local)}"><h2>cur:{escape(local)}</h2>'
                     f'<p class="tipo">{escape(tipo)} · {escape(str(etiqueta))}</p>'
                     + (f'<p>{escape(str(comentario))}</p>' if comentario else '')
                     + (f'<ul>{detalles}</ul>' if detalles else '') + '</section>')
    cuerpo = (f'<h1>Vocabulario cur</h1>\n<p>Espacio de nombres: <code>{escape(cur)}</code> · '
              f'<a href="../cur.ttl">Turtle</a></p>\n' + '\n'.join(filas))
    (destino / 'def' / 'cur').mkdir(parents=True, exist_ok=True)
    (destino / 'def' / 'cur' / 'index.html').write_text(
        pagina('Vocabulario cur', cuerpo, base, cabecera='<link rel="alternate" type="text/turtle" href="../cur.ttl">\n'),
        encoding='utf-8')
    shutil.copyfile(vocabulario, destino / 'def' / 'cur.ttl')


def _portada(g, base, destino):
    version = g.value(URIRef(f'{base}id/curriculo'), OWL.versionInfo)
    enlaces = [(f'{base}id/curriculo', 'Esquema de conceptos del currículo'),
               (f'{base}id/descriptores', 'Competencias clave y descriptores operativos'),
               (f'{base}def/cur', 'Vocabulario cur')]
    if version is not None:
        enlaces.append((f'{REPOSITORIO}/releases/tag/v{version}', f'Versión {version}: JSON, CSV y Turtle completos'))
    cuerpo = ('<h1>Currículo LOMLOE de Canarias</h1>\n<p>Datos enlazados del currículo: cada URI '
              '<code>' + escape(base) + 'id/…</code> tiene una ficha y su descripción en Turtle.</p>\n<ul>'
              + ''.join(f'<li><a href="{escape(u)}">{escape(t)}</a></li>' for u, t in enlaces)
              + f'</ul>\n<p><a href="{REPOSITORIO}">Repositorio</a></p>')
    (destino / 'index.html').write_text(pagina('Currículo LOMLOE de Canarias', cuerpo, base), encoding='utf-8')


def generar(g, base, destino, vocabulario=VOCABULARIO):
    """Escribe el sitio en `destino`. Devuelve el número de sujetos con ficha."""
    fichas = _Fichas(g, base, vocabulario)
    rutas = {s: ruta(base, s) for s in fichas.sujetos}
    rotos = fichas.rotos()
    if rotos:
        raise ValueError(f'{len(rotos)} enlaces a URIs que no están en el grafo: ' + ', '.join(rotos[:20]))
    destino = Path(destino)
    for s, r in rutas.items():
        carpeta = destino / r
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / 'index.html').write_text(fichas.html(s), encoding='utf-8')
        (carpeta / 'index.ttl').write_text(fichas.turtle(s), encoding='utf-8')
    _vocabulario(vocabulario, destino, base)
    _portada(g, base, destino)
    shutil.copytree(RECURSOS, destino / 'recursos', dirs_exist_ok=True)
    (destino / '.nojekyll').touch()
    return len(rutas)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--ttl', default=str(DIST / 'curriculo.ttl'), help='Turtle del corpus (por defecto dist/curriculo.ttl)')
    p.add_argument('--destino', default=str(DIST / 'sitio'), help='carpeta del sitio (por defecto dist/sitio)')
    p.add_argument('--base', help='base de las URIs; por defecto la de config/corpus.yaml')
    args = p.parse_args(argv)
    destino = Path(args.destino)
    if destino.exists():
        if not (destino / '.nojekyll').exists():
            sys.exit(f'{destino} existe y no es un sitio generado (falta .nojekyll): no se borra')
        shutil.rmtree(destino)
    g = Graph().parse(args.ttl)
    n = generar(g, args.base or base_uri(), destino)
    print(f'{destino}: {n} URIs con ficha y Turtle')
    return 0


if __name__ == '__main__':
    sys.exit(main())
