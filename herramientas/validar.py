"""Reglas de validación sobre el corpus ya corregido.

Nivel «error»: el corpus no debería publicarse con ese problema, salvo que figure en
config/incidencias_aceptadas.yaml. Nivel «aviso»: se informa, pero no bloquea.
"""
import re
from collections import defaultdict

import jsonschema

from .comun import ESQUEMA, leer_json


def _natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', s)]


def validar(corpus, descriptores_validos):
    av = []

    def a(regla, nivel, nodo, detalle):
        av.append({'regla': regla, 'nivel': nivel, 'nodo': nodo, 'detalle': detalle})

    esquema = leer_json(ESQUEMA)
    for e in sorted(jsonschema.Draft202012Validator(esquema).iter_errors(corpus), key=lambda e: list(e.path)):
        ruta = list(e.path)
        nodo = corpus['nodos'][ruta[1]]['id'] if len(ruta) > 1 and ruta[0] == 'nodos' else None
        a('esquema', 'error', nodo, e.message[:200])

    nodos = {n['id']: n for n in corpus['nodos']}
    hijos = defaultdict(list)
    for n in corpus['nodos']:
        for campo in ('broader', 'bloque', 'materia', 'materia_curso', 'curso', 'etapa', 'sustituido_por'):
            if campo in n and n[campo] not in nodos:
                a('referencia_rota', 'error', n['id'], f'{campo} apunta a {n[campo]}, que no existe')
        for ref in n.get('agrupa', []):
            if ref not in nodos:
                a('referencia_rota', 'error', n['id'], f'agrupa apunta a {ref}, que no existe')
        if 'broader' in n:
            hijos[n['broader']].append(n)

    for n in corpus['nodos']:
        if not n.get('obsoleto') and nodos.get(n.get('broader'), {}).get('obsoleto'):
            a('padre_obsoleto', 'error', n['id'], f"Cuelga de {n['broader']}, que está retirado")
        if nodos.get(n.get('sustituido_por'), {}).get('obsoleto'):
            a('sustituto_obsoleto', 'error', n['id'], f"Su sustituto {n['sustituido_por']} también está retirado")

    criterios_por_ce_curso = defaultdict(list)
    explicaciones = defaultdict(list)
    for n in corpus['nodos']:
        t = n['tipo']
        if t == 'CompetenciaEspecifica' and not n.get('definition'):
            a('ce_sin_enunciado', 'error', n['id'], 'Falta el enunciado de la competencia específica')
        if t == 'CriterioEvaluacion':
            if not n.get('definition'):
                a('criterio_sin_texto', 'error', n['id'], 'Falta el texto del criterio')
            if not n.get('descriptores'):
                a('criterio_sin_descriptores', 'aviso', n['id'], 'El criterio no tiene descriptores')
            criterios_por_ce_curso[(n['broader'], n['curso'])].append(int(n['notation'].rsplit('.', 1)[1]))
        if t in ('CriterioEvaluacion', 'BloqueCompetencial'):
            validos = descriptores_validos.get(n['etapa'], set())
            for d in n.get('descriptores', []):
                if d not in validos:
                    a('descriptor_desconocido', 'error', n['id'], f'Descriptor no previsto para la etapa: {d}')
        if t == 'BloqueCompetencial' and n.get('scopeNote'):
            explicaciones[(n['materia'], n['notation'].rsplit('BC', 1)[1], n['scopeNote'])].append(n['id'])
        if t == 'BloqueCompetencial' and not n.get('scopeNote'):
            a('bloque_sin_explicacion', 'aviso', n['id'], 'El bloque competencial no tiene explicación')
        if t == 'SaberBasico':
            if not n.get('definition'):
                if hijos.get(n['id']):
                    a('encabezado_sin_texto', 'aviso', n['id'], 'Encabezado de saberes sin texto')
                else:
                    a('saber_sin_texto', 'error', n['id'], 'Falta el texto del saber')
        if t == 'BloqueSaberes' and not n.get('definition'):
            a('bloque_saberes_sin_titulo', 'error', n['id'], 'Falta el título del bloque de saberes')

    for (ce, curso), numeros in criterios_por_ce_curso.items():
        if sorted(numeros) != list(range(1, len(numeros) + 1)):
            a('numeracion_criterios', 'aviso', ce, f'Numeración de criterios no continua en {curso}: {sorted(numeros)}')
    for padre, lista in hijos.items():
        saberes = [h for h in lista if h['tipo'] == 'SaberBasico']
        if saberes:
            ult = sorted(int(h['notation'].rsplit('.', 1)[1]) for h in saberes)
            if ult != list(range(1, len(ult) + 1)):
                a('numeracion_saberes', 'aviso', padre, f'Numeración de saberes no continua: {ult}')
    for (materia, num, _), ids in explicaciones.items():
        if len(ids) > 1:
            a('explicacion_repetida_entre_cursos', 'aviso', sorted(ids, key=_natural)[0],
              'Misma explicación del bloque competencial en ' + ', '.join(sorted(ids, key=_natural)))
    return av
