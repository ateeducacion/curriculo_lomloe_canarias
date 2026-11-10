"""Índice del buscador (buscar.json): una entrada por nodo vigente de los tipos que se buscan.

Claves cortas para que el fichero pese menos: u (URL de la ficha), c (código), t (texto), k (tipo,
en palabras), r (ruta legible), e (etapa) y m (materia de la etapa).
"""
import json

from .datos import ROTULOS

TIPOS_INDEXADOS = ('Materia', 'MateriaCurso', 'CompetenciaEspecifica', 'BloqueCompetencial',
                   'CriterioEvaluacion', 'BloqueSaberes', 'SaberBasico')


def entradas(c):
    res = []
    for tipo in TIPOS_INDEXADOS:
        for u in c.nodos(tipo):
            if c.retirado(u):
                continue
            etapa = c.atajo(u, 'etapa')
            materia = u if tipo == 'Materia' else c.atajo(u, 'materia')
            ruta = ' · '.join(r for url, r in c.migas(u)[1:-1])
            res.append({'u': str(u), 'c': c.codigo(u), 't': c.texto(u) or c.etiqueta(u), 'k': ROTULOS[tipo],
                        'r': ruta, 'e': c.codigo(etapa) if etapa is not None else '',
                        'm': c.nombre_materia(materia) if materia is not None else ''})
    return res


def escribir(c, destino):
    (destino / 'buscar.json').write_text(json.dumps(entradas(c), ensure_ascii=False, separators=(',', ':')),
                                         encoding='utf-8')
