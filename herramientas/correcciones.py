"""Aplica las correcciones de correcciones/*.yaml sobre los nodos importados.

Formato de un fichero de corrección:

    id: '0001'
    titulo: Texto breve
    motivo: Por qué hace falta
    fuente: {documento: eso-matematicas, ubicacion: '…'}
    estado: propuesta | aprobada | rechazada
    aprobada_por: nombre o usuario
    cambios:
      - {nodo: ce:SMATC2, campo: definition, valor: '…'}
      - {nodo: sb:XXXX, accion: eliminar}
      - {nodo: sb:YYYY, accion: crear, datos: {tipo: SaberBasico, …}}

Solo se aplican las correcciones con estado «aprobada». Si un cambio ya no altera
nada (la fuente ya trae ese valor), se avisa de que la corrección puede retirarse.
"""
from .comun import CORRECCIONES, leer_yaml

CAMPOS_EDITABLES = {'definition', 'scopeNote', 'prefLabel', 'descriptores', 'agrupa', 'broader', 'bloque'}


def cargar():
    return [(ruta.name, leer_yaml(ruta)) for ruta in sorted(CORRECCIONES.glob('*.yaml'))]


def aplicar(nodos):
    avisos, resumen = [], []
    for nombre, c in cargar():
        estado = c.get('estado', 'propuesta')
        resumen.append({'fichero': nombre, 'id': c.get('id'), 'titulo': c.get('titulo'),
                        'estado': estado, 'cambios': len(c.get('cambios') or [])})
        if estado != 'aprobada':
            continue
        for ch in c.get('cambios') or []:
            nid, accion = ch.get('nodo'), ch.get('accion', 'modificar')
            if accion == 'crear':
                if nid in nodos:
                    avisos.append(_aviso('correccion_innecesaria', 'aviso', nid, nombre, 'El nodo ya existe'))
                    continue
                nodos[nid] = {'id': nid, **(ch.get('datos') or {})}
                continue
            if nid not in nodos:
                avisos.append(_aviso('correccion_nodo_inexistente', 'error', nid, nombre, 'El nodo no existe'))
                continue
            if accion == 'eliminar':
                del nodos[nid]
                continue
            campo = ch.get('campo')
            if campo not in CAMPOS_EDITABLES:
                avisos.append(_aviso('correccion_campo_no_editable', 'error', nid, nombre, f'Campo no editable: {campo}'))
                continue
            if nodos[nid].get(campo) == ch.get('valor'):
                avisos.append(_aviso('correccion_innecesaria', 'aviso', nid, nombre,
                                     f'La base ya trae este valor de {campo}; la corrección puede retirarse'))
            nodos[nid][campo] = ch.get('valor')
    return avisos, resumen


def _aviso(regla, nivel, nodo, fichero, detalle):
    return {'regla': regla, 'nivel': nivel, 'nodo': nodo, 'detalle': f'{fichero}: {detalle}'}
