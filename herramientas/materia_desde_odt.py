"""Crea desde su documento oficial una materia que no está en la exportación de ProIDEAC.

    python -m herramientas.materia_desde_odt bachillerato-musica-expresion-y-espectaculos

La materia tiene que estar ya en config/materias.csv (con su código y cursos) y en las
`materias` del documento en el manifiesto. La herramienta lee el ODT, monta un fragmento
con la misma forma que la exportación de ProIDEAC y lo pasa por el importador, de modo que
los nodos salen con los mismos campos que los importados. El resultado es una corrección
«propuesta» con una acción `crear` por nodo, que se revisa y aprueba como las demás.
"""
import argparse
import sys

import yaml

from . import odt
from .comun import CORRECCIONES, ETAPAS, FUENTES, leer_yaml, materias_config, sha256
from .contrastar import _natural, _secciones
from .importar_proideac import importar


def fragmento(doc, materias):
    """Fragmento con la forma de la exportación: {etapa: {curso: {código: materia}}}."""
    secciones = _secciones(doc, materias)
    leido = odt.leer(FUENTES / 'documentos' / doc['fichero'], secciones)
    avisos = list(leido['avisos'])
    salida = {}
    for rotulo, confs in secciones.items():
        sec = leido['secciones'].get(rotulo)
        if not sec:
            continue
        for conf in confs:
            pref, nn = conf['materia'], conf['curso']
            letra, codigo = pref[0], pref[1:]
            m = next(f for (e, _), f in materias.items() if e == letra and f['codigo_en_identificadores'] == codigo)
            curso = f'{int(nn)}º {ETAPAS[letra][1]}'
            materia = salida.setdefault(ETAPAS[letra][1], {}).setdefault(curso, {}).setdefault(
                m['codigo'], {'denominacion': m['denominacion'], 'competencias_especificas': {},
                              'saberes_basicos': {'bloques': {}}})
            for b in sec['bloques_competenciales']:
                if not b['competencias']:
                    avisos.append(f'{rotulo}: bloque competencial sin competencia')
                    continue
                if len(b['competencias']) > 1:
                    avisos.append(f'{rotulo}: bloque con varias competencias; solo se crea el enunciado de la primera')
                c = b['competencias'][0]
                materia['competencias_especificas'][f'{pref}C{c["num"]}'] = {
                    'descripcion': c['enunciado'],
                    'explicacion_bloque_competencial': b['explicacion'],
                    'criterios_evaluacion': [{'codigo': f'{pref}{nn}CE{cr["num"]}', 'descripcion': cr['texto'],
                                              'competencias_clave': cr['descriptores'] or []}
                                             for cr in b['criterios']],
                }
            for b in sec['saberes']:
                if b.get('descripcion'):
                    avisos.append(f'{rotulo}: el bloque {b["romano"]} tiene descripción; la exportación no la recoge')
                materia['saberes_basicos']['bloques'][f'{b["romano"]}. {b["titulo"]}'] = \
                    _items(f'{pref}{nn}SB{b["romano"]}', b['hijos'])
    return salida, avisos


def _items(base, hijos, ruta=(), textos=()):
    """Un registro por saber hoja, con los textos de sus antecesores numerados, como en la exportación."""
    items = []
    for i, h in enumerate(hijos, 1):
        r, t = ruta + (str(i),), textos + (h['texto'],)
        if h['hijos']:
            items += _items(base, h['hijos'], r, t)
        else:
            item = {'nombre': f"{base}.{'.'.join(r)}"}
            for k in range(len(r)):
                item[f'subtitulo_nivel_{k + 1}'] = f"{'.'.join(r[:k + 1])}. {t[k]}"
            items.append(item)
    return items


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('documento', help='id del documento en fuentes/manifiesto.yaml')
    args = p.parse_args(argv)
    manifiesto = leer_yaml(FUENTES / 'manifiesto.yaml')
    doc = next((d for d in manifiesto['documentos'] if d['id'] == args.documento), None)
    if not doc or not doc.get('fichero') or not doc.get('materias'):
        print('El documento no existe, no está descargado o no tiene materias en el manifiesto.')
        return 1
    frag, avisos = fragmento(doc, materias_config())
    imp = importar(frag)
    nodos = {k: v for k, v in imp.nodos.items() if v['tipo'] not in ('Etapa', 'Curso')}
    for a in avisos + [f"{a['regla']}: {a['nodo']} {a['detalle']}" for a in imp.avisos]:
        print('aviso:', a)
    existentes = sorted(CORRECCIONES.glob('*.yaml'))
    numero = max([int(r.name[:4]) for r in existentes if r.name[:4].isdigit()] + [0]) + 1
    correccion = {
        'id': f'{numero:04d}',
        'titulo': f"{doc['denominacion']} ({ETAPAS[doc['etapa']][2]}): materia ausente en la exportación",
        'motivo': 'La exportación de ProIDEAC no incluye esta materia. Se crea desde el documento oficial con '
                  '`herramientas.materia_desde_odt`, que pasa el documento por el importador para que los nodos '
                  'tengan la misma forma que los importados. Los códigos de materia no proceden de ProIDEAC.',
        'fuente': {'documento': doc['id'], 'fichero': f"fuentes/documentos/{doc['fichero']}",
                   'sha256': sha256(FUENTES / 'documentos' / doc['fichero']),
                   'ubicacion': 'Documento completo'},
        'estado': 'propuesta',
        'aprobada_por': None,
        'cambios': [{'nodo': k, 'accion': 'crear', 'datos': {c: v for c, v in n.items() if c != 'id'}}
                    for k, n in sorted(nodos.items(), key=lambda kv: _natural(kv[0]))],
    }
    ruta = CORRECCIONES / f"{numero:04d}-{doc['id']}-materia-ausente.yaml"
    with open(ruta, 'w', encoding='utf-8') as f:
        yaml.safe_dump(correccion, f, allow_unicode=True, sort_keys=False, width=120)
    print(f'propuesta: {ruta.relative_to(CORRECCIONES.parent)} ({len(nodos)} nodos)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
