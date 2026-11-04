"""Contrasta el corpus construido con los ODT oficiales descargados.

Para cada documento del manifiesto que tenga fichero local, compara enunciados,
explicaciones, criterios, descriptores y saberes. No modifica nada: produce
informes/contraste.md y informes/contraste.json.

Las secciones del documento (qué rótulo corresponde a qué materia y curso) se deducen de
los cursos de sus materias en config/materias.csv; las `secciones` del manifiesto, si
existen, las sustituyen.

Con --proponer, además, escribe en correcciones/ correcciones en estado «propuesta», una por
documento y tipo de error, para los casos en que el documento permite arreglar el corpus sin
dudas (ver CATEGORIAS). Los saberes sin texto se emparejan por contenido, no por número,
porque la exportación a veces anida como subsaberes lo que el documento lista al mismo nivel;
los que no se pueden emparejar uno a uno quedan para revisión manual.
"""
import argparse
import difflib
import re
import sys
from collections import Counter

import yaml

from . import odt
from .comun import (CORRECCIONES, ETAPAS, FUENTES, INFORMES, escribir_json, leer_json, leer_yaml,
                    materias_config, sha256)

CICLOS = {1: 'Primer', 2: 'Segundo', 3: 'Tercer'}

# Tipos de error que --proponer corrige: (sufijo del fichero, título, motivo)
CATEGORIAS = {
    'ausente': ('textos-ausentes', 'textos ausentes en la exportación',
                'La exportación de ProIDEAC no trae estos textos. Se toman del documento oficial '
                '(los saberes se emparejan por contenido).'),
    'copiada': ('explicaciones-copiadas', 'explicaciones de bloque copiadas de otro curso',
                'La exportación repite en estos bloques competenciales la explicación de otro curso de la '
                'materia; el documento oficial trae una explicación propia para cada curso.'),
    'otra_materia': ('textos-de-otra-materia', 'textos de saber de otra materia',
                     'La exportación asigna a estos saberes un texto de otra materia (encabezados mezclados '
                     'entre materias). Se toma el texto del documento oficial en la misma posición.'),
    'titulo_y_descripcion': ('titulo-y-descripcion-de-bloques', 'título y descripción de los bloques de saberes',
                             'La exportación junta en el título del bloque de saberes su título y su descripción. '
                             'Se separan como en el documento oficial: título en definition y descripción en scopeNote.'),
}


def _rotulo_curso(letra, num):
    """Rótulo con el que los documentos oficiales encabezan la sección de un curso."""
    n = int(num)
    if letra == 'S':
        return f'{n}.º ESO'
    if letra == 'B':
        return f'{n}.º Bachillerato'
    if letra == 'P':
        return f'{CICLOS[(n + 1) // 2]} ciclo Educación Primaria'
    if letra == 'I':
        return f'{CICLOS[1 if n <= 3 else 2]} ciclo Educación Infantil'
    return None


def secciones_automaticas(doc, materias):
    """Rótulo -> [{materia, curso}] a partir de los cursos de las materias del documento.

    Un rótulo de curso compartido por varias materias del documento vale para todas (Segunda
    Lengua Extranjera: un solo currículo para los tres idiomas), salvo que el documento las
    separe por denominación (Matemáticas A y B en 4.º ESO): se proponen ambos rótulos y se
    usan los que aparezcan. En Primaria, un ciclo abarca dos cursos y la misma sección se
    contrasta con ambos.
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
        secciones.setdefault(rot, []).append({'materia': pref, 'curso': num})
        if len(por_rotulo[rot]) > 1:
            secciones.setdefault(denom, []).append({'materia': pref, 'curso': num})
    return secciones


def _secciones(doc, materias):
    if doc.get('secciones'):
        return {r: c if isinstance(c, list) else [c] for r, c in doc['secciones'].items()}
    return secciones_automaticas(doc, materias)


def contrastar(nodos, manifiesto, materias=None):
    materias = materias_config() if materias is None else materias
    materias_de_texto = {}
    for n in nodos.values():
        if n.get('definition'):
            materias_de_texto.setdefault(_norma(n['definition']), set()).add(n.get('materia'))
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
        if not doc.get('secciones'):
            # Con secciones deducidas sobran rótulos alternativos: solo importa que cada
            # materia y curso quede cubierto por alguna sección encontrada.
            leido['avisos'] = [a for a in leido['avisos'] if not a.startswith('Secciones del manifiesto')]
            cubiertos = {(c['materia'], c['curso']) for r in leido['secciones'] for c in secciones[r]}
            faltan = sorted({(c['materia'], c['curso']) for cs in secciones.values() for c in cs} - cubiertos)
            if faltan:
                leido['avisos'].append('Materias y cursos sin sección en el documento: '
                                       + ', '.join(m + n for m, n in faltan))
            secciones = {r: secciones[r] for r in leido['secciones']}
        dif, huecos, revisar, explicaciones = [], {}, [], {}

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
                        _hueco(huecos, 'ausente', ce, 'definition', c['enunciado'])
                    expl = leido['explicacion_competencias'].get(c['num'])
                    if expl and nodos.get(ce, {}).get('scopeNote') not in (None, expl):
                        d('explicación de competencia distinta', ce)
                if b['competencias']:
                    bc = f'bc:{pref}{nn}BC{b["competencias"][0]["num"]}'
                    _cmp(d, nodos, bc, 'scopeNote', b['explicacion'], 'explicación de bloque')
                    if bc in nodos and b['explicacion']:
                        explicaciones[bc] = b['explicacion']
                    _cmp(d, nodos, bc, 'descriptores', b['descriptores'], 'descriptores de bloque')
                for cr in b['criterios']:
                    cid = f'crit:{pref}{nn}CE{cr["num"]}'
                    vistos.add(cid)
                    _cmp(d, nodos, cid, 'definition', cr['texto'], 'texto de criterio')
                    if cr['descriptores'] is not None:
                        _cmp(d, nodos, cid, 'descriptores', cr['descriptores'], 'descriptores de criterio')
            for b in sec['saberes']:
                base = f'sb:{pref}{nn}SB{b["romano"]}'
                vistos.add(base)
                _cmp(d, nodos, base, 'definition', b['titulo'], 'título de bloque de saberes')
                if b.get('descripcion') or (nodos.get(base) or {}).get('scopeNote'):
                    _cmp(d, nodos, base, 'scopeNote', b.get('descripcion'), 'descripción de bloque de saberes')
                bs = nodos.get(base) or {}
                if (b.get('descripcion') and not bs.get('scopeNote')
                        and _norma(bs.get('definition')) == _norma(b['titulo'] + ' ' + b['descripcion'])):
                    _hueco(huecos, 'titulo_y_descripcion', base, 'definition', b['titulo'])
                    _hueco(huecos, 'titulo_y_descripcion', base, 'scopeNote', b['descripcion'])
                _saberes(d, nodos, base, b['hijos'], vistos)
                _huecos_saberes(nodos, base, b['hijos'], huecos, revisar)
                if doc.get('norma') != 'decreto-86-2025':
                    # Los ámbitos integran por diseño saberes de otras materias.
                    _otra_materia(nodos, base, b['hijos'], leido, materias_de_texto, huecos)
            prefijos = (f'crit:{pref}{nn}CE', f'sb:{pref}{nn}SB')
            for nid in nodos:
                if nid.startswith(prefijos) and nid not in vistos:
                    d('nodo del corpus que no está en el documento', nid)
        _explicaciones_copiadas(nodos, explicaciones, huecos)
        resultados.append({'documento': doc['id'], 'estado': 'contrastado', 'avisos_lectura': leido['avisos'],
                           'diferencias': dif, 'huecos': list(huecos.values()), 'revisar': revisar})
    return resultados


def _hueco(huecos, categoria, nodo, campo, valor):
    huecos[(nodo, campo)] = {'categoria': categoria, 'nodo': nodo, 'campo': campo, 'valor': valor}


def _explicaciones_copiadas(nodos, explicaciones, huecos):
    """Bloques cuya explicación en el corpus es la que el documento da a otro bloque."""
    por_texto = {}
    for bc, e in explicaciones.items():
        por_texto.setdefault(_norma(e), set()).add(bc)
    for bc, esperado in explicaciones.items():
        actual = _norma(nodos[bc].get('scopeNote'))
        if actual and actual != _norma(esperado) and por_texto.get(actual, set()) - {bc}:
            _hueco(huecos, 'copiada', bc, 'scopeNote', esperado)


def _textos_documento(leido):
    textos = set()

    def rec(hs):
        for h in hs:
            textos.add(_norma(h['texto']))
            rec(h['hijos'])
    for sec in leido['secciones'].values():
        for b in sec['saberes']:
            textos.add(_norma(b['titulo']))
            rec(b['hijos'])
    return textos


def _otra_materia(nodos, padre, hijos, leido, materias_de_texto, huecos):
    """Saberes cuyo texto en el corpus es de otra materia y no aparece en el documento.

    Solo si el texto del documento en esa posición es claramente distinto: los saberes que
    varias materias comparten de verdad (los socioafectivos de Matemáticas) no cuentan.
    """
    if 'textos' not in leido:
        leido['textos'] = _textos_documento(leido)
    for i, h in enumerate(hijos, 1):
        nid = f'{padre}.{i}'
        n = nodos.get(nid)
        if n and n.get('definition'):
            actual = _norma(n['definition'])
            if (materias_de_texto.get(actual, set()) - {n.get('materia')} and actual not in leido['textos']
                    and difflib.SequenceMatcher(None, actual, _norma(h['texto'])).ratio() < 0.5):
                _hueco(huecos, 'otra_materia', nid, 'definition', h['texto'])
        _otra_materia(nodos, nid, h['hijos'], leido, materias_de_texto, huecos)


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
                _hueco(huecos, 'ausente', k, 'definition', x)


def proponer(resultados, manifiesto):
    """Escribe una corrección «propuesta» por documento y tipo de error.

    No toca las correcciones existentes: omite los cambios de nodo y campo que ya cubre
    otra corrección (o los nodos que otra corrección crea o elimina).
    """
    existentes = sorted(CORRECCIONES.glob('*.yaml'))
    cubiertos = {(ch.get('nodo'), ch.get('campo')) for r in existentes for ch in (leer_yaml(r).get('cambios') or [])}
    siguiente = max([int(r.name[:4]) for r in existentes if r.name[:4].isdigit()] + [0]) + 1
    docs = {d['id']: d for d in manifiesto.get('documentos', [])}
    escritos = []
    for r in resultados:
        for cat, (sufijo, titulo, motivo) in CATEGORIAS.items():
            cambios = [{k: h[k] for k in ('nodo', 'campo', 'valor')} for h in r.get('huecos', [])
                       if h['categoria'] == cat and (h['nodo'], h['campo']) not in cubiertos
                       and (h['nodo'], None) not in cubiertos]
            if not cambios:
                continue
            doc = docs[r['documento']]
            correccion = {
                'id': f'{siguiente:04d}',
                'titulo': f"{doc['denominacion']} ({ETAPAS[doc['etapa']][2]}): {len(cambios)} {titulo}",
                'motivo': motivo + ' Generada con `contrastar --proponer`.',
                'fuente': {'documento': doc['id'], 'fichero': f"fuentes/documentos/{doc['fichero']}",
                           'sha256': sha256(FUENTES / 'documentos' / doc['fichero']),
                           'ubicacion': 'Tablas de bloques competenciales y saberes básicos de cada sección'},
                'estado': 'propuesta',
                'aprobada_por': None,
                'cambios': sorted(cambios, key=lambda h: (_natural(h['nodo']), h['campo'])),
            }
            ruta = CORRECCIONES / f"{siguiente:04d}-{doc['id']}-{sufijo}.yaml"
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
        for cat, n in Counter(h['categoria'] for h in r.get('huecos', [])).items():
            lineas.append(f"- corregible desde el documento ({CATEGORIAS[cat][1]}): {n}")
        for x in r.get('revisar', []):
            lineas.append(f"- revisar a mano: {', '.join(x['nodos'])} (el documento tiene {len(x['documento'])} "
                          f"saberes en ese tramo)")
        for a in r.get('avisos_lectura', []):
            lineas.append(f'- aviso de lectura: {a}')
        lineas.append('')
    return '\n'.join(lineas)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus', help='curriculo.json ya construido (p. ej. dist/curriculo.json); '
                                    'por defecto se construye el corpus en el momento')
    p.add_argument('--proponer', action='store_true',
                   help='escribe en correcciones/ las correcciones propuestas para los huecos del corpus')
    args = p.parse_args(argv)
    # No se usa dist/ por defecto: puede ser de una construcción anterior y dar un contraste desfasado.
    if args.corpus:
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
