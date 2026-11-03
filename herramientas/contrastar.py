"""Contrasta el corpus construido con los ODT oficiales descargados.

Para cada documento del manifiesto que tenga fichero local, compara enunciados,
explicaciones, criterios, descriptores y saberes. No modifica nada: produce
informes/contraste.md y informes/contraste.json.

Las secciones del documento (qué rótulo corresponde a qué materia y curso) se deducen de
los cursos de sus materias en config/materias.csv; las `secciones` del manifiesto, si
existen, las sustituyen.

Con --proponer, además, escribe en correcciones/ una corrección en estado «propuesta» por
documento con los huecos del corpus que el documento permite rellenar: enunciados de
competencia y textos de saber que faltan. Los saberes se emparejan por contenido, no por
número, porque la exportación a veces anida como subsaberes lo que el documento lista al
mismo nivel. Los huecos que no se pueden emparejar uno a uno quedan para revisión manual.
"""
import argparse
import difflib
import re
import sys
from collections import Counter

import yaml

from . import odt
from .comun import (CORRECCIONES, DIST, ETAPAS, FUENTES, INFORMES, escribir_json, leer_json, leer_yaml,
                    materias_config, sha256)

CICLOS = {1: 'Primer', 2: 'Segundo', 3: 'Tercer'}


def _rotulo_curso(letra, num):
    """Rótulo con el que los documentos oficiales encabezan la sección de un curso."""
    n = int(num)
    if letra == 'S':
        return f'{n}.º ESO'
    if letra == 'B':
        return f'{n}.º Bachillerato'
    if letra == 'P':
        return f'{CICLOS[(n + 1) // 2]} ciclo Educación Primaria'
    return None


def secciones_automaticas(doc, materias):
    """Rótulo -> [{materia, curso}] a partir de los cursos de las materias del documento.

    Un rótulo de curso compartido por varias materias del documento (Matemáticas A y B en
    4.º ESO) no las distingue: en ese caso la sección se busca por la denominación.
    En Primaria, un ciclo abarca dos cursos y la misma sección se contrasta con ambos.
    """
    candidatos = []
    for clave in doc.get('materias') or []:
        m = materias.get((clave[0], clave[1:]))
        if not m:
            continue
        pref = clave[0] + m['codigo_en_identificadores']
        for curso in m['cursos'].split('|'):
            rot = _rotulo_curso(curso[0], curso[1:])
            if rot:
                candidatos.append((rot, pref, curso[1:], m['denominacion']))
    por_rotulo = {}
    for rot, pref, _, _ in candidatos:
        por_rotulo.setdefault(rot, set()).add(pref)
    secciones = {}
    for rot, pref, num, denom in candidatos:
        clave = rot if len(por_rotulo[rot]) == 1 else denom
        secciones.setdefault(clave, []).append({'materia': pref, 'curso': num})
    return secciones


def _secciones(doc, materias):
    if doc.get('secciones'):
        return {r: c if isinstance(c, list) else [c] for r, c in doc['secciones'].items()}
    return secciones_automaticas(doc, materias)


def contrastar(nodos, manifiesto, materias=None):
    materias = materias_config() if materias is None else materias
    resultados = []
    for doc in manifiesto.get('documentos', []):
        if not doc.get('fichero'):
            continue
        secciones = _secciones(doc, materias)
        if not secciones:
            continue
        ruta = FUENTES / 'documentos' / doc['fichero']
        if not ruta.exists():
            resultados.append({'documento': doc['id'], 'estado': 'fichero ausente', 'diferencias': []})
            continue
        leido = odt.leer(ruta, secciones)
        dif, huecos, revisar = [], {}, []

        def d(tipo, nodo, detalle=''):
            dif.append({'tipo': tipo, 'nodo': nodo, 'detalle': detalle})

        for rotulo, conf in ((r, c) for r, cs in secciones.items() for c in cs):
            sec = leido['secciones'].get(rotulo)
            if not sec:
                continue
            pref, nn = conf['materia'], conf['curso']
            vistos = set()
            for b in sec['bloques_competenciales']:
                for c in b['competencias']:
                    ce = f'ce:{pref}C{c["num"]}'
                    _cmp(d, nodos, ce, 'definition', c['enunciado'], 'enunciado de competencia')
                    if ce in nodos and not nodos[ce].get('definition') and c['enunciado']:
                        huecos[ce] = {'nodo': ce, 'campo': 'definition', 'valor': c['enunciado']}
                    expl = leido['explicacion_competencias'].get(c['num'])
                    if expl and nodos.get(ce, {}).get('scopeNote') not in (None, expl):
                        d('explicación de competencia distinta', ce)
                if b['competencias']:
                    bc = f'bc:{pref}{nn}BC{b["competencias"][0]["num"]}'
                    _cmp(d, nodos, bc, 'scopeNote', b['explicacion'], 'explicación de bloque')
                    _cmp(d, nodos, bc, 'descriptores', b['descriptores'], 'descriptores de bloque')
                for cr in b['criterios']:
                    cid = f'crit:{pref}{nn}CE{cr["num"]}'
                    vistos.add(cid)
                    _cmp(d, nodos, cid, 'definition', cr['texto'], 'texto de criterio')
                    _cmp(d, nodos, cid, 'descriptores', cr['descriptores'], 'descriptores de criterio')
            for b in sec['saberes']:
                base = f'sb:{pref}{nn}SB{b["romano"]}'
                vistos.add(base)
                _cmp(d, nodos, base, 'definition', b['titulo'], 'título de bloque de saberes')
                _saberes(d, nodos, base, b['hijos'], vistos)
                _huecos_saberes(nodos, base, b['hijos'], huecos, revisar)
            prefijos = (f'crit:{pref}{nn}CE', f'sb:{pref}{nn}SB')
            for nid in nodos:
                if nid.startswith(prefijos) and nid not in vistos:
                    d('nodo del corpus que no está en el documento', nid)
        resultados.append({'documento': doc['id'], 'estado': 'contrastado', 'avisos_lectura': leido['avisos'],
                           'diferencias': dif, 'huecos': list(huecos.values()), 'revisar': revisar})
    return resultados


def _natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', s)]


def _norma(s):
    return re.sub(r'\W+', ' ', (s or '').lower()).strip()


def _huecos_saberes(nodos, base, hijos, huecos, revisar):
    """Empareja por contenido los saberes de un bloque y rellena los que no tienen texto."""
    ids = sorted((k for k in nodos if k.startswith(base + '.')), key=_natural)
    textos = []

    def aplanar(hs):
        for h in hs:
            textos.append(h['texto'])
            aplanar(h['hijos'])
    aplanar(hijos)
    corpus = [_norma(nodos[k].get('definition')) for k in ids]
    sm = difflib.SequenceMatcher(None, corpus, [_norma(x) for x in textos], autojunk=False)
    # Los encabezados vacíos con hijos son un aviso del validador, no un hueco que rellenar.
    con_hijos = {k.rsplit('.', 1)[0] for k in ids}
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        vacios = [k for k in ids[i1:i2] if not nodos[k].get('definition') and k not in con_hijos]
        if op == 'equal' or not vacios:
            continue
        if i2 - i1 != j2 - j1:
            revisar.append({'nodos': vacios, 'documento': textos[j1:j2]})
            continue
        for k, x in zip(ids[i1:i2], textos[j1:j2]):
            if k in vacios:
                huecos[k] = {'nodo': k, 'campo': 'definition', 'valor': x}


def proponer(resultados, manifiesto):
    """Escribe una corrección «propuesta» por documento con los huecos rellenables.

    No toca las correcciones existentes: omite los nodos que ya cubre otra corrección.
    """
    existentes = sorted(CORRECCIONES.glob('*.yaml'))
    cubiertos = {ch.get('nodo') for r in existentes for ch in (leer_yaml(r).get('cambios') or [])}
    siguiente = max([int(r.name[:4]) for r in existentes if r.name[:4].isdigit()] + [0]) + 1
    docs = {d['id']: d for d in manifiesto.get('documentos', [])}
    escritos = []
    for r in resultados:
        cambios = [h for h in r.get('huecos', []) if h['nodo'] not in cubiertos]
        if not cambios:
            continue
        doc = docs[r['documento']]
        n_ce = sum(h['nodo'].startswith('ce:') for h in cambios)
        partes = ([f'{n_ce} enunciados de competencia'] if n_ce else []) + \
                 ([f'{len(cambios) - n_ce} textos de saber'] if len(cambios) > n_ce else [])
        correccion = {
            'id': f'{siguiente:04d}',
            'titulo': f"{doc['denominacion']} ({ETAPAS[doc['etapa']][2]}): " + ' y '.join(partes) + ' ausentes en la exportación',
            'motivo': 'La exportación de ProIDEAC no trae estos textos. Se toman del documento oficial; '
                      'generada con `contrastar --proponer` (los saberes se emparejan por contenido).',
            'fuente': {'documento': doc['id'], 'fichero': f"fuentes/documentos/{doc['fichero']}",
                       'sha256': sha256(FUENTES / 'documentos' / doc['fichero']),
                       'ubicacion': 'Tablas de bloques competenciales y saberes básicos de cada sección'},
            'estado': 'propuesta',
            'aprobada_por': None,
            'cambios': sorted(cambios, key=lambda h: _natural(h['nodo'])),
        }
        ruta = CORRECCIONES / f"{siguiente:04d}-{doc['id']}-textos-ausentes.yaml"
        with open(ruta, 'w', encoding='utf-8') as f:
            yaml.safe_dump(correccion, f, allow_unicode=True, sort_keys=False, width=120)
        escritos.append(ruta)
        siguiente += 1
    return escritos


def _saberes(d, nodos, padre, hijos, vistos):
    for i, h in enumerate(hijos, 1):
        nid = f'{padre}.{i}'
        vistos.add(nid)
        _cmp(d, nodos, nid, 'definition', h['texto'], 'texto de saber')
        _saberes(d, nodos, nid, h['hijos'], vistos)


def _cmp(d, nodos, nid, campo, esperado, etiqueta):
    if nid not in nodos:
        d(f'falta en el corpus: {etiqueta}', nid)
    elif campo == 'descriptores' and set(nodos[nid].get(campo) or []) == set(esperado or []):
        return
    elif nodos[nid].get(campo) != esperado:
        d(f'{etiqueta} distinto', nid, f'documento: {str(esperado)[:80]!r}')


def informe_md(resultados):
    lineas = ['# Contraste con los documentos oficiales', '']
    if not resultados:
        lineas.append('Ningún documento del manifiesto tiene fichero local.')
    for r in resultados:
        lineas.append(f"## {r['documento']} — {r['estado']}")
        tipos = Counter(x['tipo'] for x in r['diferencias'])
        if not tipos:
            lineas.append('Sin diferencias.')
        for t, n in tipos.most_common():
            ejemplos = [x['nodo'] for x in r['diferencias'] if x['tipo'] == t][:5]
            lineas.append(f'- {t}: {n} (p. ej. {", ".join(ejemplos)})')
        if r.get('huecos'):
            lineas.append(f"- huecos del corpus que el documento permite rellenar: {len(r['huecos'])}")
        for x in r.get('revisar', []):
            lineas.append(f"- revisar a mano: {', '.join(x['nodos'])} (el documento tiene {len(x['documento'])} "
                          f"saberes en ese tramo)")
        for a in r.get('avisos_lectura', []):
            lineas.append(f'- aviso de lectura: {a}')
        lineas.append('')
    return '\n'.join(lineas)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus', default=str(DIST / 'curriculo.json'))
    p.add_argument('--proponer', action='store_true',
                   help='escribe en correcciones/ las correcciones propuestas para los huecos del corpus')
    args = p.parse_args(argv)
    from pathlib import Path
    if Path(args.corpus).exists():
        corpus = leer_json(args.corpus)
    else:
        from .construir import construir
        corpus, _, _ = construir()
    nodos = {n['id']: n for n in corpus['nodos']}
    manifiesto = leer_yaml(FUENTES / 'manifiesto.yaml')
    resultados = contrastar(nodos, manifiesto)
    escribir_json(INFORMES / 'contraste.json', resultados)
    (INFORMES / 'contraste.md').write_text(informe_md(resultados) + '\n', encoding='utf-8')
    print(informe_md(resultados))
    if args.proponer:
        for ruta in proponer(resultados, manifiesto):
            print(f'propuesta: {ruta.relative_to(CORRECCIONES.parent)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
