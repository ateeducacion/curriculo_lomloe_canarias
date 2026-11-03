"""Lector de los ODT oficiales de currículo (formato de materias de Primaria, ESO y Bachillerato).

Se guía por la estructura del documento (tablas de bloques competenciales, niveles de
lista de los saberes y unos pocos rótulos fijos), no por estilos ni posiciones.
Qué sección del documento corresponde a qué materia y curso lo indica el manifiesto.
"""
import re
import zipfile
import xml.etree.ElementTree as ET

from .comun import ROMANO

NS = {'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
      'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
      'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'}
T, TB = '{%s}' % NS['text'], '{%s}' % NS['table']
RE_ROMANO = re.compile(rf'^({ROMANO})\.\s+(.+)$')


def _texto(el):
    """Texto del elemento conservando los espacios tipográficos (solo une saltos y tabuladores)."""
    out = []

    def rec(x):
        if x.tag == T + 's':
            out.append(' ' * int(x.get(T + 'c', '1')))
        elif x.tag in (T + 'tab', T + 'line-break'):
            out.append(' ')
        elif x.text:
            out.append(x.text)
        for c in x:
            rec(c)
            if c.tail:
                out.append(c.tail)
    rec(el)
    return re.sub(r'[ \t\r\n]+', ' ', ''.join(out)).strip(' ')


def _secuencia(cuerpo):
    seq = []

    def recorrer(e, prof):
        for c in e:
            tag = c.tag.split('}')[1]
            if tag == 'list':
                recorrer(c, prof + 1)
            elif tag in ('list-item', 'list-header', 'section'):
                recorrer(c, prof)
            elif tag in ('p', 'h'):
                s = _texto(c)
                if s:
                    seq.append(('p', prof, s))
            elif tag == 'table':
                seq.append(('tabla', 0, c))
    recorrer(cuerpo, 0)
    return seq


def _parrafos_celda(celda):
    return [_texto(p) for p in celda.iter() if p.tag in (T + 'p', T + 'h') and _texto(p)]


def _codigos(parrafos):
    # Algunos documentos cierran la lista de descriptores con punto («CC3.»).
    return [c.strip().rstrip('.') for c in ','.join(parrafos).replace(';', ',').split(',') if c.strip().rstrip('.')]


def _tabla_bloque(tabla, avisos):
    filas = [[_parrafos_celda(c) for c in fila if c.tag == TB + 'table-cell']
             for fila in tabla.iter(TB + 'table-row')]
    cab = filas[0]
    if not cab or not cab[0] or cab[0][0] != 'Competencia específica':
        avisos.append('Tabla sin cabecera «Competencia específica»')
    comps = []
    for p in cab[0][1:]:
        m = re.match(r'^(\d+)\.\s+(.*)$', p)
        if m:
            comps.append({'num': int(m.group(1)), 'enunciado': m.group(2).strip()})
        else:
            avisos.append('Enunciado de competencia sin número: ' + p[:60])
    bloque = {'competencias': comps, 'descriptores': _codigos(cab[1][1:] if len(cab) > 1 else []),
              'criterios': [], 'explicacion': None}
    for fila in filas[1:]:
        plano = [x for c in fila for x in c]
        if not plano or plano[0] == 'Criterios de evaluación':
            continue
        if plano[0] == 'Explicación del bloque competencial':
            bloque['explicacion'] = ' '.join(plano[1:])
            continue
        m = re.match(r'^(\d+)\.(\d+)\.?\s*(.*)$', fila[0][0] if fila[0] else '')
        if not m:
            avisos.append('Fila de tabla no reconocida: ' + ' | '.join(plano)[:80])
            continue
        bloque['criterios'].append({'num': f'{m.group(1)}.{m.group(2)}', 'competencia': int(m.group(1)),
                                    'texto': ' '.join([m.group(3)] + fila[0][1:]).strip(),
                                    'descriptores': _codigos(fila[1] if len(fila) > 1 else [])})
    return bloque


def leer(ruta, secciones):
    """Devuelve la estructura del documento. `secciones`: rótulos de sección del documento."""
    with zipfile.ZipFile(ruta) as z:
        raiz = ET.fromstring(z.read('content.xml'))
    seq = _secuencia(raiz.find('office:body/office:text', NS))
    doc = {'explicacion_competencias': {}, 'secciones': {}, 'avisos': []}
    actual, modo, ce_expl, pila = None, None, None, []
    for tipo, prof, x in seq:
        if tipo == 'p' and prof == 0:
            m = re.match(r'^Competencia específica (\d+) \(C\d+\)$', x)
            if m and actual is None:
                ce_expl = int(m.group(1))
                doc['explicacion_competencias'][ce_expl] = []
                continue
            if x in secciones:
                actual = {'bloques_competenciales': [], 'saberes': []}
                doc['secciones'][x] = actual
                # Algunos documentos (p. ej. Cultura Científica de Bachillerato) omiten el
                # rótulo «Bloques competenciales» y empiezan la sección con las tablas.
                ce_expl, modo = None, 'bc'
                continue
            if actual is None:
                if x == 'Saberes básicos' or x.startswith('Situaciones de aprendizaje'):
                    ce_expl = None
                elif ce_expl is not None:
                    doc['explicacion_competencias'][ce_expl].append(x)
                continue
            if x == 'Bloques competenciales':
                modo = 'bc'
            elif x == 'Saberes básicos':
                modo = 'sb'
            elif modo == 'sb' and RE_ROMANO.match(x):
                m = RE_ROMANO.match(x)
                bloque = {'romano': m.group(1), 'titulo': m.group(2).strip(), 'hijos': []}
                actual['saberes'].append(bloque)
                pila = [bloque]
            else:
                doc['avisos'].append(f'Párrafo no clasificado: {x[:70]}')
        elif tipo == 'tabla' and actual is not None and modo == 'bc':
            actual['bloques_competenciales'].append(_tabla_bloque(x, doc['avisos']))
        elif tipo == 'p' and actual is not None and modo == 'sb' and pila:
            pila = pila[:prof]
            if len(pila) < prof:
                doc['avisos'].append(f'Salto de nivel en saberes: {x[:70]}')
                continue
            padre = pila[-1]
            nodo = {'texto': x, 'hijos': []}
            padre['hijos'].append(nodo)
            pila.append(nodo)
    doc['explicacion_competencias'] = {k: ' '.join(v) for k, v in doc['explicacion_competencias'].items()}
    faltan = [s for s in secciones if s not in doc['secciones']]
    if faltan:
        doc['avisos'].append('Secciones del manifiesto no encontradas: ' + ', '.join(faltan))
    return doc
