"""Contrasta el corpus construido con los ODT oficiales descargados.

Para cada documento del manifiesto que tenga fichero local y `secciones`, compara
enunciados, explicaciones, criterios, descriptores y saberes. No modifica nada:
produce informes/contraste.md y informes/contraste.json.
"""
import argparse
import sys
from collections import Counter

from . import odt
from .comun import DIST, FUENTES, INFORMES, escribir_json, leer_json, leer_yaml


def contrastar(nodos, manifiesto):
    resultados = []
    for doc in manifiesto.get('documentos', []):
        if not doc.get('fichero') or not doc.get('secciones'):
            continue
        ruta = FUENTES / 'documentos' / doc['fichero']
        if not ruta.exists():
            resultados.append({'documento': doc['id'], 'estado': 'fichero ausente', 'diferencias': []})
            continue
        leido = odt.leer(ruta, doc['secciones'])
        dif = []

        def d(tipo, nodo, detalle=''):
            dif.append({'tipo': tipo, 'nodo': nodo, 'detalle': detalle})

        for rotulo, conf in doc['secciones'].items():
            sec = leido['secciones'].get(rotulo)
            if not sec:
                continue
            pref, nn = conf['materia'], conf['curso']
            vistos = set()
            for b in sec['bloques_competenciales']:
                for c in b['competencias']:
                    ce = f'ce:{pref}C{c["num"]}'
                    _cmp(d, nodos, ce, 'definition', c['enunciado'], 'enunciado de competencia')
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
            prefijos = (f'crit:{pref}{nn}CE', f'sb:{pref}{nn}SB')
            for nid in nodos:
                if nid.startswith(prefijos) and nid not in vistos:
                    d('nodo del corpus que no está en el documento', nid)
        resultados.append({'documento': doc['id'], 'estado': 'contrastado', 'avisos_lectura': leido['avisos'],
                           'diferencias': dif})
    return resultados


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
        lineas.append('Ningún documento del manifiesto tiene fichero local y secciones definidas.')
    for r in resultados:
        lineas.append(f"## {r['documento']} — {r['estado']}")
        tipos = Counter(x['tipo'] for x in r['diferencias'])
        if not tipos:
            lineas.append('Sin diferencias.')
        for t, n in tipos.most_common():
            ejemplos = [x['nodo'] for x in r['diferencias'] if x['tipo'] == t][:5]
            lineas.append(f'- {t}: {n} (p. ej. {", ".join(ejemplos)})')
        for a in r.get('avisos_lectura', []):
            lineas.append(f'- aviso de lectura: {a}')
        lineas.append('')
    return '\n'.join(lineas)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus', default=str(DIST / 'curriculo.json'))
    args = p.parse_args(argv)
    from pathlib import Path
    if Path(args.corpus).exists():
        corpus = leer_json(args.corpus)
    else:
        from .construir import construir
        corpus, _, _ = construir()
    nodos = {n['id']: n for n in corpus['nodos']}
    resultados = contrastar(nodos, leer_yaml(FUENTES / 'manifiesto.yaml'))
    escribir_json(INFORMES / 'contraste.json', resultados)
    (INFORMES / 'contraste.md').write_text(informe_md(resultados) + '\n', encoding='utf-8')
    print(informe_md(resultados))
    return 0


if __name__ == '__main__':
    sys.exit(main())
