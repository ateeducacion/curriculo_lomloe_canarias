"""Convierte la exportación de ProIDEAC (curriculo_unificado_ordenado.json) en nodos del modelo.

No corrige nada: traduce la estructura y deja constancia, como avisos, de todo lo que
no encaja. Las correcciones se aplican después (herramientas/correcciones.py).
"""
import unicodedata
from collections import OrderedDict, defaultdict

from .comun import (ETAPAS, ETAPA_POR_CLAVE, RE_BLOQUE_SABERES, RE_CLAVE_CE, RE_CRITERIO,
                    RE_PREFIJO_NUM, RE_SABER, RE_SECRETO, curso_id)

CORTO = {'I': 'Infantil', 'P': 'Primaria', 'S': 'ESO', 'B': 'Bachillerato'}


class Importacion:
    def __init__(self):
        self.nodos = OrderedDict()
        self.avisos = []
        self.items_saber = {}  # código -> registro de la exportación

    def aviso(self, regla, nivel, nodo, detalle):
        self.avisos.append({'regla': regla, 'nivel': nivel, 'nodo': nodo, 'detalle': detalle})

    def nodo(self, **campos):
        n = {k: v for k, v in campos.items() if v is not None}
        self.nodos[n['id']] = n
        return n


def _num_curso(nombre):
    return f'{int(nombre.strip()[0]):02d}'


def _nfc(x):
    """Normaliza a NFC todos los textos: parte de la exportación trae las tildes descompuestas (NFD)."""
    if isinstance(x, str):
        return unicodedata.normalize('NFC', x)
    if isinstance(x, dict):
        return {_nfc(k): _nfc(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_nfc(v) for v in x]
    return x


def importar(exportacion):
    exportacion = _nfc(exportacion)
    imp = Importacion()
    for clave_etapa, cursos in exportacion.items():
        letra = ETAPA_POR_CLAVE.get(clave_etapa)
        if not letra:
            imp.aviso('etapa_desconocida', 'error', None, f'Etapa no reconocida: {clave_etapa}')
            continue
        etapa_id, _, etapa_nombre, _ = ETAPAS[letra]
        imp.nodo(id=etapa_id, tipo='Etapa', notation=etapa_id.split(':')[1], prefLabel=etapa_nombre)
        for nombre_curso, materias in cursos.items():
            nn = _num_curso(nombre_curso)
            cid = curso_id(letra, nn)
            imp.nodo(id=cid, tipo='Curso', notation=f'{letra}{nn}', prefLabel=nombre_curso,
                     broader=etapa_id, etapa=etapa_id)
            for codigo, materia in materias.items():
                _importar_materia(imp, letra, etapa_id, cid, nn, codigo, materia)
    _cerrar(imp)
    return imp


def _importar_materia(imp, letra, etapa_id, cid, nn, codigo, materia):
    mid = f'materia:{letra}{codigo}'
    if mid not in imp.nodos:
        imp.nodo(id=mid, tipo='Materia', notation=f'{letra}{codigo}',
                 prefLabel=f"{materia['denominacion']} ({CORTO[letra]})", etapa=etapa_id, cursos=[])
    imp.nodos[mid]['cursos'].append(cid)

    # ---- Competencias específicas, bloques competenciales y criterios ----
    for clave, ce in (materia.get('competencias_especificas') or {}).items():
        m = RE_CLAVE_CE.match(clave)
        if not m or m.group(1) != letra:
            imp.aviso('clave_ce_invalida', 'error', mid, f'Clave de competencia no reconocida: {clave}')
            continue
        pref, num_clave = clave[:-len(m.group(3)) - 1], int(m.group(3))   # p. ej. SMAT, 1
        if m.group(2) != codigo:
            imp.aviso('codigo_materia_inconsistente', 'aviso', mid,
                      f'La clave de la materia es {codigo}, pero sus identificadores usan {m.group(2)}')
        ce_id = f'ce:{clave}'
        texto = (ce.get('descripcion') or '').strip() or None
        if ce_id in imp.nodos:
            if imp.nodos[ce_id].get('definition') != texto:
                imp.aviso('ce_distinta_entre_cursos', 'aviso', ce_id,
                          f'El enunciado cambia en {cid}; se conserva el primero')
        else:
            imp.nodo(id=ce_id, tipo='CompetenciaEspecifica', notation=clave, definition=texto,
                     broader=mid, materia=mid, etapa=etapa_id)
        bc_id = f'bc:{pref}{nn}BC{num_clave}'
        criterios_ids, numeros, descriptores = [], {num_clave}, []
        for cr in ce.get('criterios_evaluacion') or []:
            cod = (cr.get('codigo') or '').strip()
            mc = RE_CRITERIO.match(cod)
            if not mc:
                imp.aviso('codigo_criterio_invalido', 'error', bc_id, f'Código de criterio no reconocido: {cod!r}')
                continue
            if mc.group(3) != nn:
                imp.aviso('criterio_curso_inconsistente', 'error', f'crit:{cod}',
                          f'El código indica el curso {mc.group(3)} y está en {cid}')
            crit_id = f'crit:{cod}'
            if crit_id in imp.nodos:
                imp.aviso('codigo_duplicado', 'error', crit_id, 'Criterio repetido en la exportación; se conserva el primero')
                continue
            n_ce = int(mc.group(4))
            numeros.add(n_ce)
            destino = f'ce:{mc.group(1)}{mc.group(2)}C{n_ce}'
            if destino not in imp.nodos:
                imp.nodo(id=destino, tipo='CompetenciaEspecifica', notation=destino[3:], broader=mid,
                         materia=mid, etapa=etapa_id)
                imp.aviso('ce_solo_en_criterios', 'aviso', destino,
                          f'La competencia {n_ce} solo aparece en los códigos de criterios del bloque {clave}; '
                          'la exportación no incluye su enunciado')
            desc = [d.strip() for d in cr.get('competencias_clave') or [] if d.strip()]
            for d in desc:
                if d not in descriptores:
                    descriptores.append(d)
            imp.nodo(id=crit_id, tipo='CriterioEvaluacion', notation=cod,
                     definition=(cr.get('descripcion') or '').strip() or None, broader=destino,
                     bloque=bc_id, descriptores=desc, materia=mid, curso=cid, etapa=etapa_id)
            criterios_ids.append(crit_id)
        agrupa = [f'ce:{pref}C{n}' for n in sorted(numeros)]
        if len(agrupa) > 1:
            imp.aviso('bloque_con_varias_ce', 'aviso', bc_id,
                      'El bloque competencial agrupa las competencias ' + ', '.join(a[3:] for a in agrupa))
        imp.nodo(id=bc_id, tipo='BloqueCompetencial', notation=bc_id[3:],
                 prefLabel=f"{materia['denominacion']} · {imp.nodos[cid]['prefLabel']} · bloque competencial "
                           + ' + '.join(f'C{a.rsplit("C", 1)[1]}' for a in agrupa),
                 scopeNote=(ce.get('explicacion_bloque_competencial') or '').strip() or None,
                 broader=mid, agrupa=agrupa, descriptores=descriptores,
                 materia=mid, curso=cid, etapa=etapa_id)

    # ---- Saberes básicos ----
    for clave_bloque, items in ((materia.get('saberes_basicos') or {}).get('bloques') or {}).items():
        if RE_SECRETO.search(clave_bloque):
            imp.aviso('posible_secreto', 'error', mid,
                      'Una clave de bloque de saberes contiene lo que parece una credencial (valor omitido)')
            titulo_bloque = None
        else:
            mb = RE_BLOQUE_SABERES.match(clave_bloque.strip())
            titulo_bloque = (mb.group(1), mb.group(2).strip()) if mb else None
            if not mb:
                imp.aviso('clave_bloque_saberes_invalida', 'aviso', mid,
                          f'Clave de bloque de saberes sin numeración romana: {clave_bloque[:60]!r}')
        for item in items:
            _importar_saber(imp, letra, etapa_id, cid, nn, mid, item, titulo_bloque)


def _importar_saber(imp, letra, etapa_id, cid, nn, mid, item, titulo_bloque):
    cod = (item.get('nombre') or '').strip()
    m = RE_SABER.match(cod)
    if not m and cod.endswith('.') and RE_SABER.match(cod.rstrip('.')):
        ultimo = next((t for t in (item.get('subtitulo_nivel_3'), item.get('subtitulo_nivel_2'),
                                   item.get('subtitulo_nivel_1')) if t), '')
        pm = RE_PREFIJO_NUM.match(ultimo.strip())
        if pm and cod.rstrip('.').endswith('SB' + cod.split('SB', 1)[1].split('.', 1)[0] + '.' + pm.group(1)):
            imp.aviso('codigo_saber_reconstruido', 'aviso', f"sb:{cod.rstrip('.')}",
                      f'Código con punto final en la exportación ({cod!r}); se elimina el punto')
            cod = cod.rstrip('.')
            m = RE_SABER.match(cod)
    if not m and cod.endswith('.'):
        # Código truncado (p. ej. «XXXX02SBII.1.»): se reconstruye con el número del texto más profundo.
        ultimo = next((t for t in (item.get('subtitulo_nivel_3'), item.get('subtitulo_nivel_2'),
                                   item.get('subtitulo_nivel_1')) if t), '')
        pm = RE_PREFIJO_NUM.match(ultimo.strip())
        cola = cod.split('SB', 1)[1].split('.', 1)[1] if 'SB' in cod and '.' in cod.split('SB', 1)[1] else ''
        if pm and pm.group(1).startswith(cola):
            nuevo = cod[:len(cod) - len(cola)] + pm.group(1)
            if RE_SABER.match(nuevo):
                imp.aviso('codigo_saber_reconstruido', 'aviso', f'sb:{nuevo}',
                          f'Código truncado en la exportación ({cod!r}); reconstruido a partir del texto')
                cod, m = nuevo, RE_SABER.match(nuevo)
    if not m:
        imp.aviso('codigo_saber_invalido', 'error', mid, f'Código de saber no reconocido: {cod!r}')
        return
    numero_exportado = None
    if cod in imp.items_saber and imp.items_saber[cod] != item:
        nuevo = _codigo_desde_apartado(cod, m, item)
        if nuevo and nuevo not in imp.items_saber:
            imp.aviso('codigo_saber_reconstruido', 'aviso', f'sb:{nuevo}',
                      f'Código repetido en la exportación ({cod!r}) con un apartado distinto en el texto; '
                      'reconstruido a partir del texto')
            numero_exportado = m.group(5).strip('.')
            cod, m = nuevo, RE_SABER.match(nuevo)
    if m.group(3) != nn:
        imp.aviso('saber_curso_inconsistente', 'error', f'sb:{cod}', f'El código indica el curso {m.group(3)} y está en {cid}')
    romano = m.group(4)
    nums = m.group(5).strip('.').split('.')
    base = f'{m.group(1)}{m.group(2)}{m.group(3)}SB{romano}'
    bs_id = f'sb:{base}'
    comunes = dict(materia=mid, curso=cid, etapa=etapa_id)
    if bs_id not in imp.nodos:
        imp.nodo(id=bs_id, tipo='BloqueSaberes', notation=base, broader=mid, **comunes)
    if titulo_bloque and titulo_bloque[0] == romano and 'definition' not in imp.nodos[bs_id]:
        imp.nodos[bs_id]['definition'] = titulo_bloque[1]
    elif titulo_bloque and titulo_bloque[0] != romano:
        imp.aviso('saber_en_bloque_ajeno', 'aviso', f'sb:{cod}',
                  f'Está en el bloque {titulo_bloque[0]} pero su código es del bloque {romano}')
    # Antecesores (apartados) y la hoja
    padre = bs_id
    for k in range(1, len(nums) + 1):
        codigo_k = f"{base}.{'.'.join(nums[:k])}"
        id_k = f'sb:{codigo_k}'
        if id_k not in imp.nodos:
            imp.nodo(id=id_k, tipo='SaberBasico', notation=codigo_k, broader=padre, **comunes)
        padre = id_k
    hoja = imp.nodos[f'sb:{cod}']
    if cod in imp.items_saber:
        if imp.items_saber[cod] == item:
            # Registro idéntico repetido: no se pierde nada al descartarlo.
            imp.aviso('registro_repetido', 'aviso', hoja['id'], 'Saber repetido de forma idéntica en la exportación')
        else:
            imp.aviso('codigo_duplicado', 'error', hoja['id'], 'Saber repetido en la exportación; se conserva el primero')
        return
    imp.items_saber[cod] = item
    numero = '.'.join(nums)
    textos = [item.get(c) for c in ('subtitulo_nivel_1', 'subtitulo_nivel_2', 'subtitulo_nivel_3') if item.get(c)]
    sin_numero = []
    for t in textos:
        pm = RE_PREFIJO_NUM.match(t.strip())
        if not pm:
            sin_numero.append(t.strip())
            continue
        num_t, txt = pm.group(1), pm.group(2).strip()
        if num_t == numero or num_t == numero_exportado:
            _fijar(imp, hoja, 'definition', txt)
        elif numero.startswith(num_t + '.'):
            _fijar(imp, imp.nodos[f'sb:{base}.{num_t}'], 'definition', txt)
        else:
            imp.aviso('encabezado_no_corresponde', 'aviso', hoja['id'],
                      f'Un encabezado numerado «{num_t}» no corresponde al saber {numero}: {txt[:70]!r}')
    for t in sin_numero:
        if 'definition' not in hoja and t is sin_numero[-1] and len(textos) == len(sin_numero):
            hoja['definition'] = t
            imp.aviso('saber_sin_numeracion', 'aviso', hoja['id'], 'El texto del saber no lleva número')
        else:
            destino = imp.nodos[hoja['broader']]
            _fijar(imp, destino, 'scopeNote', t)


def _codigo_desde_apartado(cod, m, item):
    """Código corregido para un saber cuyo código choca con otro y cuyo apartado no es el del texto.

    Caso típico (Bioestadística, III): «3. Inclusión…» / «1.1. Destrezas…» exportado como
    III.1.1, cuando debería ser III.3.1. Solo se reconstruye si el número del encabezado de
    nivel 1 es un apartado entero distinto del del código y el del nivel 2 repite el código
    (numeración relativa al apartado). Si no, devuelve None.
    """
    nums = m.group(5).strip('.').split('.')
    p1 = RE_PREFIJO_NUM.match((item.get('subtitulo_nivel_1') or '').strip())
    p2 = RE_PREFIJO_NUM.match((item.get('subtitulo_nivel_2') or '').strip())
    if not (p1 and p2 and p1.group(1).isdigit() and p1.group(1) != nums[0] and p2.group(1) == '.'.join(nums)):
        return None
    return cod[:len(cod) - len(m.group(5))] + '.' + '.'.join([p1.group(1)] + nums[1:])


def _fijar(imp, nodo, campo, valor):
    actual = nodo.get(campo)
    if actual is None:
        nodo[campo] = valor
    elif actual != valor:
        imp.aviso('texto_en_conflicto', 'aviso', nodo['id'],
                  f'Dos textos distintos para {campo}; se conserva el primero. Descartado: {valor[:70]!r}')


def _cerrar(imp):
    hijos = defaultdict(list)
    for n in imp.nodos.values():
        if 'broader' in n:
            hijos[n['broader']].append(n['id'])
    for cod in sorted(imp.items_saber):
        if hijos.get(f'sb:{cod}'):
            imp.aviso('saber_con_hijos', 'aviso', f'sb:{cod}',
                      'La exportación lo trata como saber, pero tiene subapartados: se modela como encabezado')
    for n in imp.nodos.values():
        if n['tipo'] == 'SaberBasico' and n['notation'] not in imp.items_saber and 'definition' not in n:
            imp.aviso('encabezado_sin_texto', 'aviso', n['id'], 'La exportación no incluye el texto de este encabezado')
