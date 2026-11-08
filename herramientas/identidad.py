"""Identidad entre versiones: ningún nodo publicado desaparece ni cambia de tipo.

publicaciones/<versión>.csv guarda el `id` y el `tipo` de cada nodo de una versión
publicada. La construcción compara el corpus con la última: un nodo que falte o haya
cambiado de tipo es un error (un nodo publicado se retira con `accion: retirar`, no se borra).

Uso:
    python -m herramientas.identidad --registrar 1.1.0                 # al preparar una versión
    python -m herramientas.identidad --registrar 1.0.0 --desde curriculo.json   # de un release
"""
import argparse
import csv
import io
import sys

from .comun import RAIZ, leer_json

PUBLICACIONES = RAIZ / 'publicaciones'


def _version(ruta):
    return tuple(int(x) for x in ruta.stem.split('.'))


def ultima(carpeta=None):
    """Ruta de la última versión registrada, o None si no hay ninguna."""
    carpeta = carpeta or PUBLICACIONES
    rutas = sorted(carpeta.glob('*.csv'), key=_version) if carpeta.exists() else []
    return rutas[-1] if rutas else None


def comprobar(nodos, carpeta=None):
    """Avisos (errores) por los nodos de la última versión publicada que faltan o cambian de tipo."""
    ruta = ultima(carpeta)
    if ruta is None:
        return []
    actuales = {n['id']: n['tipo'] for n in nodos}
    avisos = []
    with open(ruta, encoding='utf-8', newline='') as f:
        for fila in csv.DictReader(f):
            if fila['id'] not in actuales:
                avisos.append({'regla': 'nodo_publicado_desaparecido', 'nivel': 'error', 'nodo': fila['id'],
                               'detalle': f'Publicado en la {ruta.stem} y ya no está: retíralo con '
                                          '«accion: retirar» en lugar de borrarlo'})
            elif actuales[fila['id']] != fila['tipo']:
                avisos.append({'regla': 'tipo_publicado_cambiado', 'nivel': 'error', 'nodo': fila['id'],
                               'detalle': f"Era {fila['tipo']} en la {ruta.stem} y ahora es {actuales[fila['id']]}"})
    return avisos


def registrar(nodos, version, carpeta=None):
    """Escribe publicaciones/<versión>.csv con el id y el tipo de cada nodo."""
    carpeta = carpeta or PUBLICACIONES
    carpeta.mkdir(exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(['id', 'tipo'])
    for n in nodos:
        w.writerow([n['id'], n['tipo']])
    ruta = carpeta / f'{version}.csv'
    ruta.write_text(buf.getvalue(), encoding='utf-8')
    return ruta


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--registrar', metavar='VERSION', required=True, help='versión que se publica (X.Y.Z)')
    p.add_argument('--desde', help='curriculo.json publicado; por defecto se construye el corpus')
    args = p.parse_args(argv)
    if args.desde:
        corpus = leer_json(args.desde)
    else:
        from .construir import construir
        corpus, _, _ = construir(args.registrar)
    ruta = registrar(corpus['nodos'], args.registrar)
    print(f'{ruta.relative_to(RAIZ)}: {len(corpus["nodos"])} nodos')
    return 0


if __name__ == '__main__':
    sys.exit(main())
