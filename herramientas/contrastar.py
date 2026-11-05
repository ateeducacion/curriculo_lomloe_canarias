"""Contrasta el corpus construido con los ODT oficiales descargados.

Para cada documento del manifiesto que tenga fichero local, compara enunciados,
explicaciones, criterios, descriptores y saberes. No modifica nada: produce
informes/contraste.md y informes/contraste.json.

Las secciones del documento (qué rótulo corresponde a qué materia y curso) se deducen de
los cursos de sus materias en config/materias.csv; las `secciones` del manifiesto, si
existen, las sustituyen.

Además comprueba con qué número imprime el BOC cada criterio: si es otro (p. ej. 5.1 y 6.1
intercambiados), lo informa aparte como errata del BOC, sin contarlo como diferencia.

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

from . import boletin, odt
from .comun import (CONFIG, CORRECCIONES, ETAPAS, FUENTES, INFORMES, escribir_json, leer_json, leer_yaml,
                    descriptores_por_etapa, materias_config, sha256)

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
    'version': ('version-publicada', 'textos de la versión publicada en el BOC',
                'El texto de la exportación no coincide con el publicado en el BOC y el del documento oficial sí '
                '(comprobado contra fuentes/boletines). Se toma el del documento.'),
    'puntuacion': ('puntuacion-publicada', 'textos con la puntuación publicada en el BOC',
                   'El texto de la exportación solo difiere del documento oficial en la puntuación, y la del '
                   'documento es la que figura en el BOC (comprobado contra fuentes/boletines). Revisar con '
                   'atención: en las tablas, el texto extraído del BOC intercala los descriptores.'),
    'descriptores': ('descriptores-publicados', 'descriptores publicados en el BOC',
                     'Los descriptores de estos criterios no coinciden con los del documento oficial, y la lista del '
                     'documento es la que figura completa en el BOC (fuentes/boletines). Los de cada bloque se '
                     'recalculan como la unión de los de sus criterios, igual que hace el importador.'),
    'cortado': ('textos-cortados', 'textos cortados en la exportación',
                'El texto de la exportación es solo un trozo del texto del documento oficial, que figura completo '
                'en el BOC (fuentes/boletines). Se toma el texto completo.'),
    'otro_curso': ('textos-de-otro-curso', 'textos de otro curso',
                   'El texto de la exportación es el que el documento oficial da a otro curso o ciclo de la misma '
                   'materia; los dos figuran en el BOC. Se toma el que corresponde a este curso.'),
    'espacios': ('espacios', 'textos que solo difieren en espacios',
                 'El texto de la exportación solo difiere del documento oficial en espacios (dobles, de no '
                 'separación o al principio o final). Se toma el del documento.'),
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
    notas = {(n['nodo'], n.get('tipo')): n['motivo'] for n in (leer_yaml(CONFIG / 'notas_contraste.yaml') or {}).get('notas') or []} \
        if (CONFIG / 'notas_contraste.yaml').exists() else {}
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
        dif, huecos, revisar, explicaciones, textos, avisos_doc, numeracion_boc = [], {}, [], {}, [], [], []
        bol = boletin.de_norma(manifiesto, doc.get('norma'))
        conocidos = descriptores_por_etapa().get(ETAPAS[doc['etapa']][0], set())

        def d(tipo, nodo, detalle='', campo=None, esperado=None, **extra):
            dif.append({'tipo': tipo, 'nodo': nodo, 'detalle': detalle, 'campo': campo, 'esperado': esperado, **extra})

        for rotulo, conf in ((r, c) for r, cs in secciones.items() for c in cs):
            sec = leido['secciones'].get(rotulo)
            if not sec:
                continue
            pref, nn = conf['materia'], conf['curso']
            vistos = set()
            for b in sec['bloques_competenciales']:
                for c in b['competencias']:
                    ce = f'ce:{pref}C{c["num"]}'
                    _cmp(d, nodos, ce, 'definition', c['enunciado'], 'enunciado de competencia', textos)
                    if ce in nodos and not nodos[ce].get('definition') and c['enunciado']:
                        _hueco(huecos, 'ausente', ce, 'definition', c['enunciado'])
                    expl = leido['explicacion_competencias'].get(c['num'])
                    if expl and nodos.get(ce, {}).get('scopeNote') not in (None, expl):
                        d('explicación de competencia distinta', ce)
                if b['competencias']:
                    bc = f'bc:{pref}{nn}BC{b["competencias"][0]["num"]}'
                    _cmp(d, nodos, bc, 'scopeNote', b['explicacion'], 'explicación de bloque', textos)
                    if bc in nodos and b['explicacion']:
                        explicaciones[bc] = b['explicacion']
                    _descriptores_bloque(d, nodos, bc, b, pref, nn, bol, conocidos, huecos, avisos_doc)
                for cr in b['criterios']:
                    cid = f'crit:{pref}{nn}CE{cr["num"]}'
                    vistos.add(cid)
                    _cmp(d, nodos, cid, 'definition', cr['texto'], 'texto de criterio', textos)
            if bol:
                numeracion_boc += _numeracion_boc(nodos, bol, [cid for cid in vistos if cid.startswith('crit:')])
            for b in sec['saberes']:
                base = f'sb:{pref}{nn}SB{b["romano"]}'
                vistos.add(base)
                _cmp(d, nodos, base, 'definition', b['titulo'], 'título de bloque de saberes', textos)
                if b.get('descripcion') or (nodos.get(base) or {}).get('scopeNote'):
                    _cmp(d, nodos, base, 'scopeNote', b.get('descripcion'), 'descripción de bloque de saberes', textos)
                bs = nodos.get(base) or {}
                if (b.get('descripcion') and not bs.get('scopeNote')
                        and _norma(bs.get('definition')) == _norma(b['titulo'] + ' ' + b['descripcion'])):
                    _hueco(huecos, 'titulo_y_descripcion', base, 'definition', b['titulo'])
                    _hueco(huecos, 'titulo_y_descripcion', base, 'scopeNote', b['descripcion'])
                _saberes(d, nodos, base, b['hijos'], vistos, textos)
                _huecos_saberes(nodos, base, b['hijos'], huecos, revisar)
                if doc.get('norma') != 'decreto-86-2025':
                    # Los ámbitos integran por diseño saberes de otras materias.
                    _otra_materia(nodos, base, b['hijos'], leido, materias_de_texto, huecos)
            prefijos = (f'crit:{pref}{nn}CE', f'sb:{pref}{nn}SB')
            for nid in nodos:
                if nid.startswith(prefijos) and nid not in vistos:
                    d('nodo del corpus que no está en el documento', nid)
        _explicaciones_copiadas(nodos, explicaciones, huecos)
        _explicar(dif, nodos, bol, conocidos, notas)
        _version_publicada(nodos, textos, bol, huecos, _textos_documento(leido))
        resultados.append({'documento': doc['id'], 'estado': 'contrastado', 'avisos_lectura': leido['avisos'],
                           'diferencias': dif, 'huecos': list(huecos.values()), 'revisar': revisar,
                           'avisos_documento': avisos_doc, 'numeracion_boc': numeracion_boc})
    return resultados


def _numeracion_boc(nodos, bol, criterios):
    """Criterios que el BOC imprime con otro número (p. ej. 5.1 y 6.1 intercambiados).

    Un mismo texto (o su comienzo) puede repetirse en otros cursos, materias o criterios con
    otro número. Se toman las apariciones de la zona del boletín donde están los criterios de
    la misma materia y curso (alrededor de la mediana de las apariciones únicas) y, de ellas,
    la que coincide en más palabras con el texto completo. No es una diferencia del corpus: se
    informa aparte para revisarla.
    """
    apariciones = {cid: bol.numeros(nodos[cid]['definition']) for cid in criterios
                   if nodos.get(cid, {}).get('definition')}
    unicas = sorted(a[0][0] for a in apariciones.values() if len(a) == 1)
    if not unicas:
        return []
    # Zona de la materia y curso: rango intercuartílico de las apariciones únicas, para que no
    # la ensanche un criterio cuyo texto solo se encuentra entero en otra materia.
    centro = unicas[len(unicas) // 2]
    radio = unicas[3 * len(unicas) // 4] - unicas[len(unicas) // 4] + 5000
    avisos = []
    for cid in sorted(apariciones, key=_natural):
        if not apariciones[cid]:
            continue
        cerca = [a for a in apariciones[cid] if abs(a[0] - centro) <= radio] or apariciones[cid]
        _, numero, _ = max(cerca, key=lambda a: (a[2], -abs(a[0] - centro)))
        propio = cid.rsplit('CE', 1)[1]
        if numero and numero != propio:
            avisos.append({'nodo': cid, 'numero': propio, 'boc': numero})
    return avisos


def _hueco(huecos, categoria, nodo, campo, valor):
    huecos[(nodo, campo)] = {'categoria': categoria, 'nodo': nodo, 'campo': campo, 'valor': valor}


def _explicar(dif, nodos, bol, conocidos, notas):
    """Añade a cada diferencia su explicación, si la hay, para que ninguna quede sin justificar.

    Explicaciones automáticas, comprobables con el texto del BOC (fuentes/boletines):
    - el valor del corpus es el publicado en el BOC y el del documento no;
    - solo cambia la puntuación y el texto extraído del BOC no permite decidirla;
    - un saber del corpus que falta en el documento está publicado en el BOC;
    - un saber del documento que falta en el corpus no está publicado en el BOC;
    - los descriptores del documento traen códigos que no existen en la etapa;
    - los descriptores de un bloque derivan de criterios cuyas diferencias están explicadas.
    El resto necesita una nota en config/notas_contraste.yaml (nodo, tipo y motivo) o una corrección.
    """
    for x in dif:
        nota = notas.get((x['nodo'], x['tipo'])) or notas.get((x['nodo'], None))
        x['explicacion'] = f'nota: {nota}' if nota else (_explicacion_automatica(x, nodos, bol, conocidos) if bol else None)
    pendientes = {x['nodo'] for x in dif if x['tipo'] == 'descriptores de criterio distinto' and not x['explicacion']}
    for x in dif:
        if x['tipo'] == 'descriptores de bloque distinto' and not x['explicacion'] and not pendientes & set(x.get('criterios') or []) \
                and x.get('criterios'):
            x['explicacion'] = 'los descriptores del bloque derivan de los de sus criterios, cuyas diferencias están explicadas'


def _explicacion_automatica(x, nodos, bol, conocidos):
    tipo, campo, esperado = x['tipo'], x.get('campo'), x.get('esperado')
    actual = (nodos.get(x['nodo']) or {}).get(campo) if campo else None
    if campo == 'descriptores':
        if esperado and any(c not in conocidos for c in esperado):
            return 'el documento trae códigos de descriptor que no existen en la etapa (errata)'
        if actual and bol.contiene_descriptores(actual) and not bol.contiene_descriptores(esperado or []):
            return 'la lista del corpus es la publicada en el BOC; la del documento no'
        return None
    if tipo == 'nodo del corpus que no está en el documento':
        texto = (nodos.get(x['nodo']) or {}).get('definition')
        return 'el saber del corpus está publicado en el BOC; falta en el documento' if texto and bol.exacto(texto) else None
    if tipo.startswith('falta en el corpus'):
        return 'el texto del documento no está publicado en el BOC' if esperado and not bol.contiene(esperado) else None
    if not (actual and esperado):
        return None
    if _norma(actual) == _norma(esperado):
        if bol.contiene_literal(actual) and not bol.contiene_literal(esperado):
            return 'la puntuación del corpus es la publicada en el BOC'
        if bol.contiene_literal(actual) == bol.contiene_literal(esperado):
            return 'solo cambia la puntuación y el texto del BOC no permite decidirla'
        return None
    if bol.exacto(actual) and not bol.exacto(esperado):
        return 'el texto del corpus es el publicado en el BOC; el del documento no'
    if x['nodo'].startswith('ce:') and bol.exacto(actual) and bol.exacto(esperado):
        return ('la competencia tiene un enunciado distinto en cada curso en el BOC; el corpus guarda '
                'uno por materia (limitación del modelo)')
    return None


def _union(listas):
    """Unión de listas de descriptores conservando el orden de aparición, como el importador."""
    salida = []
    for lista in listas:
        salida += [x for x in lista if x not in salida]
    return salida


def _descriptores_bloque(d, nodos, bc, b, pref, nn, bol, conocidos, huecos, avisos_doc):
    """Descriptores de los criterios de un bloque y del propio bloque.

    El corpus calcula los del bloque como la unión de los de sus criterios. Por eso el bloque
    se compara con esa unión en el documento, no con la cabecera de su tabla; si la cabecera
    no cuadra con los criterios, o trae códigos que no existen, es una incoherencia del
    documento y se anota aparte. En Infantil los criterios no llevan descriptores y el
    bloque se compara con la cabecera.
    """
    criterios = [(f'crit:{pref}{nn}CE{cr["num"]}', cr['descriptores']) for cr in b['criterios']]
    con_descriptores = [(cid, ds) for cid, ds in criterios if ds is not None and cid in nodos]
    for cid, ds in con_descriptores:
        actual = nodos[cid].get('descriptores') or []
        if set(actual) == set(ds):
            continue
        d('descriptores de criterio distinto', cid, f'documento: {ds}', 'descriptores', ds)
        desconocidos = [x for x in ds if x not in conocidos]
        if desconocidos:
            # Errata en el propio documento (y en el BOC, p. ej. «CCE3»): no se puede saber qué código era.
            avisos_doc.append(f'{cid}: los descriptores del criterio traen códigos que no existen: {", ".join(desconocidos)}')
        elif bol is not None and bol.contiene_descriptores(ds) and not bol.contiene_descriptores(actual):
            _hueco(huecos, 'descriptores', cid, 'descriptores', ds)
    if bc not in nodos:
        return
    cabecera = b['descriptores']
    desconocidos = [x for x in cabecera if x not in conocidos]
    if desconocidos:
        avisos_doc.append(f'{bc}: la cabecera del bloque trae códigos que no existen: {", ".join(desconocidos)}')
    if con_descriptores:
        esperado = _union(ds for _, ds in con_descriptores)
        if set(cabecera) != set(esperado):
            avisos_doc.append(f'{bc}: la cabecera del bloque no coincide con sus criterios '
                              f'(cabecera: {", ".join(cabecera)}; criterios: {", ".join(esperado)})')
    else:
        esperado = [x for x in cabecera if x in conocidos]
    actual = nodos[bc].get('descriptores') or []
    if set(actual) == set(esperado):
        return
    d('descriptores de bloque distinto', bc, f'documento: {esperado}', 'descriptores', esperado,
      criterios=[cid for cid, _ in con_descriptores])
    corregidos = [huecos[(cid, 'descriptores')]['valor'] if (cid, 'descriptores') in huecos
                  else nodos[cid].get('descriptores') or [] for cid, _ in con_descriptores]
    if con_descriptores and set(_union(corregidos)) == set(esperado):
        _hueco(huecos, 'descriptores', bc, 'descriptores', esperado)


def _contiene_otro_saber(nodos, nid, texto):
    """El texto incluye el de otro saber del mismo bloque: el documento ha juntado dos saberes."""
    if not nid.startswith('sb:'):
        return False
    bloque = nid.split('.', 1)[0]
    return any(k != nid and k.startswith(bloque + '.') and n.get('definition')
               and len(_norma(n['definition'])) > 20 and _norma(n['definition']) in texto
               for k, n in nodos.items())


def _version_publicada(nodos, textos, bol, huecos, textos_doc=frozenset()):
    """Textos del corpus que no están en el BOC cuando el del documento sí lo está.

    En los saberes se exige además que ambos textos se parezcan: si no, lo más probable es que
    el documento y la exportación numeren distinto y se estén comparando saberes diferentes.
    """
    for nid, campo, esperado in textos:
        actual = (nodos.get(nid) or {}).get(campo)
        if not esperado or actual == esperado or (nid, campo) in huecos:
            continue
        if not actual:
            if bol is not None and bol.contiene(esperado):
                _hueco(huecos, 'ausente', nid, campo, esperado)
            continue
        if re.sub(r'\s+', ' ', actual.replace('\xa0', ' ')).strip() == esperado:
            _hueco(huecos, 'espacios', nid, campo, esperado)
            continue
        if bol is None:
            continue
        na, ne = _norma(actual), _norma(esperado)
        if _contiene_otro_saber(nodos, nid, ne):
            continue
        if na != ne and bol.exacto(esperado) and na in ne:
            _hueco(huecos, 'cortado', nid, campo, esperado)
            continue
        if (na != ne and not nid.startswith('ce:') and na in textos_doc and bol.exacto(actual)
                and bol.exacto(esperado)):
            _hueco(huecos, 'otro_curso', nid, campo, esperado)
            continue
        if bol.contiene(actual) and bol.contiene(esperado):
            if _norma(actual) == _norma(esperado):
                # Mismas palabras: decide la puntuación exacta.
                if not (bol.contiene_literal(esperado) and not bol.contiene_literal(actual)):
                    continue
            elif not (bol.exacto(esperado) and not bol.exacto(actual)):
                # Los dos aparecen tolerando un trozo: solo decide si uno aparece completo y el otro no.
                continue
        elif not bol.contiene(esperado) or bol.contiene(actual):
            continue
        if nid.startswith('sb:') and difflib.SequenceMatcher(None, _norma(actual), _norma(esperado)).ratio() < 0.6:
            continue
        _hueco(huecos, 'puntuacion' if _norma(actual) == _norma(esperado) else 'version', nid, campo, esperado)


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
    """Todos los textos del documento (normalizados): competencias, criterios, explicaciones y saberes."""
    textos = set()
    for sec in leido['secciones'].values():
        for b in sec['bloques_competenciales']:
            textos.update(_norma(c['enunciado']) for c in b['competencias'])
            textos.update(_norma(c['texto']) for c in b['criterios'])
            textos.add(_norma(b['explicacion']))

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


def _saberes(d, nodos, base, hijos, vistos, textos=None):
    """Compara los saberes de un bloque emparejándolos por contenido, no por número.

    La exportación y el documento no siempre numeran ni anidan igual (un subsaber de la
    exportación puede ser un saber del mismo nivel en el documento), así que comparar por
    posición da diferencias falsas. Se alinean las dos listas en orden; dentro de un tramo
    que no coincide, se empareja por posición si los tramos tienen el mismo tamaño y, si
    no, por parecido. Los saberes del documento sin pareja se informan como ausentes; los
    del corpus quedan fuera de `vistos` y se informan como sobrantes.
    """
    ids = sorted((k for k in nodos if k.startswith(base + '.')), key=_natural)
    con_hijos = {k.rsplit('.', 1)[0] for k in ids}
    doc = []

    def aplanar(padre, hs):
        for i, h in enumerate(hs, 1):
            doc.append((f'{padre}.{i}', h['texto']))
            aplanar(f'{padre}.{i}', h['hijos'])
    aplanar(base, hijos)
    a = [_norma(nodos[k].get('definition')) for k in ids]
    b = [_norma(t) for _, t in doc]
    parejas, sueltos = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == 'equal' or i2 - i1 == j2 - j1:
            parejas += list(zip(ids[i1:i2], doc[j1:j2]))
            continue
        libres = list(range(i1, i2))
        for j in range(j1, j2):
            mejor = max(libres, key=lambda i: difflib.SequenceMatcher(None, a[i], b[j]).ratio(), default=None)
            if mejor is not None and difflib.SequenceMatcher(None, a[mejor], b[j]).ratio() >= 0.5:
                parejas.append((ids[mejor], doc[j]))
                libres.remove(mejor)
            else:
                sueltos.append(doc[j])
    for k, (_, texto) in parejas:
        vistos.add(k)
        _cmp(d, nodos, k, 'definition', texto, 'texto de saber', textos)
    for ruta, texto in sueltos:
        d('falta en el corpus: texto de saber', ruta, f'documento: {texto[:80]!r}', 'definition', texto)
    # Los encabezados vacíos con subsaberes son estructura de la exportación, no saberes sobrantes.
    vistos.update(k for k in ids if k in con_hijos and not nodos[k].get('definition'))


def _cmp(d, nodos, nid, campo, esperado, etiqueta, textos=None):
    if nid not in nodos:
        d(f'falta en el corpus: {etiqueta}', nid, '', campo, esperado)
    elif campo == 'descriptores' and set(nodos[nid].get(campo) or []) == set(esperado or []):
        return
    elif nodos[nid].get(campo) != esperado:
        d(f'{etiqueta} distinto', nid, f'documento: {str(esperado)[:80]!r}', campo, esperado)
        if textos is not None and campo in ('definition', 'scopeNote'):
            textos.append((nid, campo, esperado))


def informe_md(resultados):
    total = sum(len(r['diferencias']) for r in resultados)
    sin = sum(1 for r in resultados for x in r['diferencias'] if not x.get('explicacion'))
    lineas = ['# Contraste con los documentos oficiales', '',
              f'- Documentos contrastados: {len(resultados)}; sin diferencias: '
              f"{sum(1 for r in resultados if not r['diferencias'])}",
              f'- Diferencias: {total}; explicadas: {total - sin}; **sin explicar: {sin}**',
              f"- Criterios que el BOC imprime con otro número (erratas del BOC, no son diferencias del corpus): "
              f"{sum(len(r.get('numeracion_boc') or []) for r in resultados)}", '']
    if not resultados:
        lineas.append('Ningún documento del manifiesto tiene fichero local.')
    for r in resultados:
        lineas.append(f"## {r['documento']} — {r['estado']}")
        sin = [x for x in r['diferencias'] if not x.get('explicacion')]
        tipos = Counter(x['tipo'] for x in sin)
        if not r['diferencias']:
            lineas.append('Sin diferencias.')
        elif not sin:
            lineas.append(f"Sin diferencias por explicar ({len(r['diferencias'])} explicadas).")
        for t, n in tipos.most_common():
            ejemplos = [x['nodo'] for x in sin if x['tipo'] == t][:5]
            lineas.append(f'- sin explicar — {t}: {n} (p. ej. {", ".join(ejemplos)})')
        for e, n in Counter(x['explicacion'] for x in r['diferencias'] if x.get('explicacion')).most_common():
            lineas.append(f'- explicadas — {e}: {n}')
        for cat, n in Counter(h['categoria'] for h in r.get('huecos', [])).items():
            lineas.append(f"- corregible desde el documento ({CATEGORIAS[cat][1]}): {n}")
        for x in r.get('revisar', []):
            lineas.append(f"- revisar a mano: {', '.join(x['nodos'])} (el documento tiene {len(x['documento'])} "
                          f"saberes en ese tramo)")
        for a in r.get('avisos_lectura', []):
            lineas.append(f'- aviso de lectura: {a}')
        if r.get('numeracion_boc'):
            lineas.append('- numeración distinta en el BOC (revisar; el corpus sigue el documento): '
                          + ', '.join(f"{x['nodo']} (BOC: {x['boc']})" for x in r['numeracion_boc']))
        if r.get('avisos_documento'):
            lineas.append(f"- incoherencias del propio documento (no son diferencias del corpus): "
                          f"{len(r['avisos_documento'])}, p. ej. {r['avisos_documento'][0]}")
        lineas.append('')
    return '\n'.join(lineas)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus', help='curriculo.json ya construido (p. ej. dist/curriculo.json); '
                                    'por defecto se construye el corpus en el momento')
    p.add_argument('--proponer', action='store_true',
                   help='escribe en correcciones/ las correcciones propuestas para los huecos del corpus')
    p.add_argument('--estricto', action='store_true',
                   help='sale con código 1 si queda alguna diferencia sin explicar (CI)')
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
    if args.estricto and any(not x.get('explicacion') for r in resultados for x in r['diferencias']):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
