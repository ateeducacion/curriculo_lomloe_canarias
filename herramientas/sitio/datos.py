"""Lectura del grafo para navegar: tipos, jerarquía, atajos y ruta de navegación.

Indexa una sola vez lo que las páginas consultan miles de veces (hijos por padre y nodos por
atajo), para no recorrer el grafo en cada página.
"""
import re
from collections import defaultdict

from rdflib import BNode, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, SKOS

from ..exportar_rdf import espacio_cur

ROTULOS = {
    'Etapa': 'Etapa', 'Curso': 'Curso', 'Materia': 'Materia', 'MateriaCurso': 'Materia en un curso',
    'CompetenciaEspecifica': 'Competencia específica', 'BloqueCompetencial': 'Bloque competencial',
    'CriterioEvaluacion': 'Criterio de evaluación', 'BloqueSaberes': 'Bloque de saberes',
    'SaberBasico': 'Saber básico',
}
ETAPAS = {'INF': 'Infantil', 'PRI': 'Primaria', 'ESO': 'ESO', 'BAC': 'Bachillerato'}
ATAJOS = ('etapa', 'curso', 'materia', 'materiaCurso', 'bloqueCompetencial')


def clave_natural(texto):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', str(texto))]


class Curriculo:
    def __init__(self, g, base):
        self.g, self.base = g, base
        self.cur = espacio_cur()
        cur = str(self.cur)
        self._tipo = {}
        for s, t in g.subject_objects(RDF.type):
            if isinstance(s, URIRef) and str(t).startswith(cur) and str(t)[len(cur):] in ROTULOS:
                self._tipo[s] = str(t)[len(cur):]
        self._hijos = defaultdict(list)
        for s, p in g.subject_objects(SKOS.broader):
            self._hijos[p].append(s)
        self._con = defaultdict(list)
        for prop in ATAJOS:
            for s, v in g.subject_objects(self.cur[prop]):
                if s in self._tipo:
                    self._con[(prop, v, self._tipo[s])].append(s)
        for bc, ce in g.subject_objects(self.cur.agrupa):
            self._con[('agrupada_por', ce, 'BloqueCompetencial')].append(bc)
        for k in self._con:
            self._con[k].sort(key=self._orden)
        for k in self._hijos:
            self._hijos[k].sort(key=self._orden)

    def _orden(self, u):
        return clave_natural(self.codigo(u) or u)

    # Datos de un nodo
    def tipo(self, u):
        return self._tipo.get(u)

    def nodos(self, tipo):
        return sorted((u for u, t in self._tipo.items() if t == tipo), key=self._orden)

    def _literal(self, u, p):
        v = self.g.value(u, p)
        return str(v) if v is not None else None

    def codigo(self, u):
        return self._literal(u, SKOS.notation) or ''

    def etiqueta(self, u):
        return self._literal(u, SKOS.prefLabel) or self.codigo(u) or str(u)

    def texto(self, u):
        return self._literal(u, SKOS.definition)

    def nota(self, u):
        return self._literal(u, SKOS.scopeNote)

    def retirado(self, u):
        return self.g.value(u, OWL.deprecated) == Literal(True)

    def sustituto(self, u):
        return self.g.value(u, DCTERMS.isReplacedBy)

    def padre(self, u):
        return self.g.value(u, SKOS.broader)

    def hijos(self, u, tipo=None):
        return [h for h in self._hijos.get(u, []) if tipo is None or self.tipo(h) == tipo]

    def con(self, prop, valor, tipo):
        return list(self._con.get((prop, valor, tipo), []))

    def atajo(self, u, prop):
        return self.g.value(u, self.cur[prop])

    def numero(self, u):
        """Número corto para listas: 1.1 (criterio), C1, BC1, I (bloque de saberes), 2.1 (saber)."""
        cod, tipo = self.codigo(u), self.tipo(u)
        if tipo == 'CriterioEvaluacion' and 'CE' in cod:
            return cod.rsplit('CE', 1)[1]
        if tipo == 'CompetenciaEspecifica':
            m = re.search(r'C\d+$', cod)
            return m.group(0) if m else cod
        if tipo == 'BloqueCompetencial' and 'BC' in cod:
            return 'BC' + cod.rsplit('BC', 1)[1]
        if tipo in ('BloqueSaberes', 'SaberBasico') and 'SB' in cod:
            cola = cod.rsplit('SB', 1)[1]
            return cola if tipo == 'BloqueSaberes' else cola.split('.', 1)[1]
        return cod

    def nombre_materia(self, u):
        """Nombre de la materia sin la etapa entre paréntesis: «Matemáticas (ESO)» → «Matemáticas»."""
        m = u if self.tipo(u) == 'Materia' else self.atajo(u, 'materia')
        return re.sub(r'\s*\([^)]*\)$', '', self.etiqueta(m)) if m is not None else self.etiqueta(u)

    def nombre_etapa(self, u):
        return ETAPAS.get(self.codigo(u), self.etiqueta(u))

    def enunciado(self, ce, curso):
        for b in self.g.objects(ce, self.cur.enunciadoEnCurso):
            if isinstance(b, BNode) and self.g.value(b, self.cur.curso) == curso:
                return self._literal(b, SKOS.definition)
        return self.texto(ce)

    def enunciados(self, ce):
        """Enunciados por curso: [(curso, texto)] en orden natural."""
        pares = [(self.g.value(b, self.cur.curso), self._literal(b, SKOS.definition))
                 for b in self.g.objects(ce, self.cur.enunciadoEnCurso)]
        return sorted(((c, t) for c, t in pares if c is not None), key=lambda x: self._orden(x[0]))

    def descriptores(self, u):
        """[(URI, código, competencia clave)] de los descriptores operativos del nodo."""
        res = []
        for d in self.g.objects(u, self.cur.descriptorOperativo):
            clave = self.g.value(d, SKOS.broader)
            nombre = self._literal(clave, SKOS.prefLabel) if clave is not None else None
            res.append((d, self.codigo(d) or str(d).rsplit('/', 1)[-1], nombre or ''))
        return sorted(res, key=lambda x: clave_natural(x[1]))

    def corto(self, u):
        """Rótulo breve para la ruta de navegación."""
        tipo = self.tipo(u)
        if tipo == 'Etapa':
            return self.nombre_etapa(u)
        if tipo == 'MateriaCurso' or tipo == 'Materia':
            return self.nombre_materia(u)
        if tipo == 'CompetenciaEspecifica':
            return f'Competencia {self.numero(u)}'
        if tipo == 'BloqueCompetencial':
            return f'Bloque {self.numero(u)}'
        if tipo == 'CriterioEvaluacion':
            return f'Criterio {self.numero(u)}'
        if tipo in ('BloqueSaberes', 'SaberBasico'):
            texto = self.texto(u) or ''
            texto = texto if len(texto) <= 40 else texto[:39].rstrip() + '…'
            return f'{self.numero(u)}. {texto}'.strip()
        return self.etiqueta(u)

    def migas(self, u):
        """Ruta de navegación: [(URL, rótulo)], de Inicio a la página actual (sin URL)."""
        tipo = self.tipo(u)
        cadena = []
        etapa = u if tipo == 'Etapa' else self.atajo(u, 'etapa')
        if tipo != 'Etapa' and etapa is not None:
            cadena.append(etapa)
        if tipo in ('MateriaCurso', 'BloqueCompetencial', 'BloqueSaberes', 'SaberBasico', 'CriterioEvaluacion'):
            for prop in ('curso', 'materiaCurso'):
                v = self.atajo(u, prop)
                if v is not None:
                    cadena.append(v)
        elif tipo == 'CompetenciaEspecifica':
            v = self.atajo(u, 'materia')
            if v is not None:
                cadena.append(v)
        if tipo == 'CriterioEvaluacion' and self.padre(u) is not None:
            cadena.append(self.padre(u))
        if tipo == 'SaberBasico':
            antecesores, p = [], self.padre(u)
            while p is not None and self.tipo(p) in ('SaberBasico', 'BloqueSaberes'):
                antecesores.append(p)
                p = self.padre(p)
            cadena.extend(reversed(antecesores))
        return [(self.base, 'Inicio')] + [(str(x), self.corto(x)) for x in cadena] + [(None, self.corto(u))]
