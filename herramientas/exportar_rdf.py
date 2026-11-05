"""Exporta el corpus como datos enlazados: SKOS en Turtle, con doble tipado schema.org.

Uso:
    python -m herramientas.exportar_rdf                       # construye y escribe dist/curriculo.ttl
    python -m herramientas.exportar_rdf --ttl dist/curriculo.ttl --validar     # CI: valida lo publicado

Cada nodo es un skos:Concept de su clase cur:<Tipo> (vocabulario/cur.ttl) y un
schema:DefinedTerm, en el esquema de conceptos del corpus. Su URI es
<base>id/<prefijo>/<código> (crit:SMAT01CE1.1 → <base>id/crit/SMAT01CE1.1), con la base de
config/corpus.yaml (`rdf.base`). Las URIs no llevan versión; el esquema sí (owl:versionInfo).
Los descriptores operativos (config/descriptores.csv) forman un segundo esquema, con las
competencias clave como conceptos superiores.

Con --validar comprueba el grafo con las formas SHACL de esquema/curriculo.shacl.ttl y sale
con código 1 si no las cumple.
"""
import argparse
import re
import shutil
import sys

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, SKOS, XSD

from .comun import CONFIG, DIST, ESQUEMA, FUENTES, RAIZ, leer_csv, leer_json, leer_yaml

SCHEMA = Namespace('https://schema.org/')
VOCABULARIO = RAIZ / 'vocabulario' / 'cur.ttl'
FORMAS = ESQUEMA.parent / 'curriculo.shacl.ttl'
ENLACES = {'materia': 'materia', 'materia_curso': 'materiaCurso', 'curso': 'curso', 'etapa': 'etapa',
           'bloque': 'bloqueCompetencial'}


def base_uri():
    return leer_yaml(CONFIG / 'corpus.yaml')['rdf']['base']


def espacio_cur():
    """Espacio de nombres del vocabulario, tal como lo declara vocabulario/cur.ttl."""
    return Namespace(dict(Graph().parse(VOCABULARIO).namespaces())['cur'])


def uri(base, nid):
    prefijo, codigo = nid.split(':', 1)
    return URIRef(f'{base}id/{prefijo}/{codigo}')


def _clave(codigo):
    return re.match(r'[A-Z]+', codigo).group(0)


def grafo(corpus, descriptores, base, cur=None, normas=()):
    """Grafo RDF del corpus. `descriptores`: filas de config/descriptores.csv."""
    cur = cur or espacio_cur()
    g = Graph()
    for p, ns in (('cur', cur), ('skos', SKOS), ('dcterms', DCTERMS), ('owl', OWL), ('schema', SCHEMA)):
        g.bind(p, ns)
    meta = corpus['corpus']
    esquema = URIRef(f'{base}id/curriculo')
    g.add((esquema, RDF.type, SKOS.ConceptScheme))
    g.add((esquema, RDF.type, SCHEMA.DefinedTermSet))
    g.add((esquema, SKOS.prefLabel, Literal(f"Currículo {meta['marco']} de {meta['ambito']}", lang='es')))
    g.add((esquema, OWL.versionInfo, Literal(meta['version'])))
    if meta.get('generado'):
        g.add((esquema, DCTERMS.modified, Literal(meta['generado'], datatype=XSD.date)))
    if (meta.get('licencia') or {}).get('url'):
        g.add((esquema, DCTERMS.license, URIRef(meta['licencia']['url'])))
    for norma in normas:
        g.add((esquema, DCTERMS.source, URIRef(norma)))

    # Descriptores operativos: un esquema aparte, con las competencias clave como conceptos superiores.
    esquema_desc = URIRef(f'{base}id/descriptores')
    g.add((esquema_desc, RDF.type, SKOS.ConceptScheme))
    g.add((esquema_desc, SKOS.prefLabel, Literal('Competencias clave y descriptores operativos', lang='es')))
    desc_uri = {}
    for fila in descriptores:
        etapa, codigo = fila['etapa'], fila['codigo']
        clave = URIRef(f'{base}id/competencia-clave/{_clave(codigo)}')
        if (clave, RDF.type, cur.CompetenciaClave) not in g:
            g.add((clave, RDF.type, SKOS.Concept))
            g.add((clave, RDF.type, cur.CompetenciaClave))
            g.add((clave, SKOS.notation, Literal(_clave(codigo))))
            g.add((clave, SKOS.prefLabel, Literal(fila['competencia'], lang='es')))
            g.add((clave, SKOS.inScheme, esquema_desc))
            g.add((clave, SKOS.topConceptOf, esquema_desc))
            g.add((esquema_desc, SKOS.hasTopConcept, clave))
        d = URIRef(f"{base}id/descriptor/{etapa.split(':')[1]}/{codigo}")
        desc_uri[(etapa, codigo)] = d
        g.add((d, RDF.type, SKOS.Concept))
        g.add((d, RDF.type, cur.DescriptorOperativo))
        g.add((d, SKOS.notation, Literal(codigo)))
        g.add((d, SKOS.prefLabel, Literal(f"{codigo} · {fila['competencia']}", lang='es')))
        g.add((d, SKOS.inScheme, esquema_desc))
        g.add((d, SKOS.broader, clave))
        g.add((clave, SKOS.narrower, d))
        g.add((d, cur.etapa, uri(base, etapa)))

    for n in corpus['nodos']:
        s = uri(base, n['id'])
        g.add((s, RDF.type, SKOS.Concept))
        g.add((s, RDF.type, cur[n['tipo']]))
        g.add((s, RDF.type, SCHEMA.DefinedTerm))
        g.add((s, SKOS.inScheme, esquema))
        g.add((s, SCHEMA.inDefinedTermSet, esquema))
        g.add((s, DCTERMS.identifier, Literal(n['id'])))
        g.add((s, SKOS.notation, Literal(n['notation'])))
        g.add((s, SCHEMA.termCode, Literal(n['notation'])))
        g.add((s, SKOS.prefLabel, Literal(n['prefLabel'], lang='es')))
        g.add((s, SCHEMA.name, Literal(n['prefLabel'], lang='es')))
        if n.get('definition'):
            g.add((s, SKOS.definition, Literal(n['definition'], lang='es')))
            g.add((s, SCHEMA.description, Literal(n['definition'], lang='es')))
        if n.get('scopeNote'):
            g.add((s, SKOS.scopeNote, Literal(n['scopeNote'], lang='es')))
        if n['tipo'] == 'Etapa':
            g.add((s, SKOS.topConceptOf, esquema))
            g.add((esquema, SKOS.hasTopConcept, s))
        if n.get('broader'):
            g.add((s, SKOS.broader, uri(base, n['broader'])))
            g.add((uri(base, n['broader']), SKOS.narrower, s))
        for campo, prop in ENLACES.items():
            if n.get(campo):
                g.add((s, cur[prop], uri(base, n[campo])))
        for cid in n.get('cursos') or []:
            g.add((s, cur.curso, uri(base, cid)))
        for ce in n.get('agrupa') or []:
            g.add((s, cur.agrupa, uri(base, ce)))
        for codigo in n.get('descriptores') or []:
            d = desc_uri.get((n.get('etapa'), codigo))
            if d is not None:
                g.add((s, cur.descriptorOperativo, d))
        for cid, texto in sorted((n.get('enunciados_curso') or {}).items()):
            e = BNode()
            g.add((s, cur.enunciadoEnCurso, e))
            g.add((e, RDF.type, cur.EnunciadoEnCurso))
            g.add((e, cur.curso, uri(base, cid)))
            g.add((e, SKOS.definition, Literal(texto, lang='es')))
        if n.get('obsoleto'):
            g.add((s, OWL.deprecated, Literal(True)))
        if n.get('sustituido_por'):
            g.add((s, DCTERMS.isReplacedBy, uri(base, n['sustituido_por'])))
    return g


def validar_grafo(g):
    """Comprueba el grafo con las formas SHACL. Devuelve (conforme, informe)."""
    from pyshacl import validate
    conforme, _, informe = validate(g, shacl_graph=Graph().parse(FORMAS), inference='none', allow_warnings=True)
    return conforme, informe


def normas_corpus(corpus):
    manifiesto = leer_yaml(FUENTES / 'manifiesto.yaml')
    ids = set(corpus['corpus'].get('normas') or [])
    return [n['url'] for n in manifiesto.get('normas', []) if n['id'] in ids and n.get('url')]


def escribir(corpus, destino=DIST):
    """Escribe <destino>/curriculo.ttl y copia el vocabulario (cur.ttl). Devuelve el grafo."""
    g = grafo(corpus, leer_csv(CONFIG / 'descriptores.csv'), base_uri(), normas=normas_corpus(corpus))
    destino.mkdir(exist_ok=True)
    g.serialize(destino / 'curriculo.ttl', format='turtle', encoding='utf-8')
    shutil.copyfile(VOCABULARIO, destino / 'cur.ttl')
    return g


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--corpus', help='curriculo.json ya construido; por defecto se construye en el momento')
    p.add_argument('--ttl', help='valida este Turtle ya generado en lugar de exportar')
    p.add_argument('--validar', action='store_true', help='comprueba el grafo con las formas SHACL')
    args = p.parse_args(argv)
    if args.ttl:
        g = Graph().parse(args.ttl)
        print(f'{args.ttl}: {len(g)} tripletas')
    else:
        if args.corpus:
            corpus = leer_json(args.corpus)
        else:
            from .construir import construir
            corpus, _, _ = construir()
        g = escribir(corpus)
        print(f'dist/curriculo.ttl: {len(g)} tripletas')
    if args.validar:
        conforme, informe = validar_grafo(g)
        print(informe if not conforme else 'Formas SHACL: conforme')
        return 0 if conforme else 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
