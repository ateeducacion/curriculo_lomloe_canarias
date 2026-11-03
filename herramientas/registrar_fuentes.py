"""Registra en el manifiesto los documentos oficiales descargados a mano.

Flujo: descarga el ODT desde la página oficial con el navegador, guárdalo en
fuentes/documentos/<etapa>/ con el mismo nombre que en la URL y ejecuta:

    python -m herramientas.registrar_fuentes

Para cada documento del manifiesto cuyo fichero exista, anota la ruta, el sha256 y
la fecha (si el fichero es nuevo o ha cambiado). Avisa de los que siguen sin descargar.
El portal de la Consejería no admite descargas automatizadas, por eso este script no descarga.
"""
import datetime
import sys

import yaml

from .comun import ETAPAS, FUENTES, sha256


def main():
    ruta = FUENTES / 'manifiesto.yaml'
    texto = ruta.read_text(encoding='utf-8')
    cabecera = ''.join(l for l in texto.splitlines(keepends=True) if l.startswith('#'))
    man = yaml.safe_load(texto)
    hoy = datetime.date.today().isoformat()
    cambios, pendientes = 0, []
    carpeta = {k: v[3] for k, v in ETAPAS.items()}
    for doc in man['documentos']:
        nombre = doc['url_odt'].rsplit('/', 1)[1]
        rel = f"{carpeta[doc['etapa']]}/{nombre}"
        local = FUENTES / 'documentos' / rel
        if not local.exists():
            pendientes.append(doc['id'])
            continue
        h = sha256(local)
        if doc.get('sha256') != h or doc.get('fichero') != rel:
            doc.update(fichero=rel, sha256=h, descargado=hoy)
            cambios += 1
            print(f'registrado: {doc["id"]} ({rel})')
    if cambios:
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(cabecera)
            yaml.safe_dump(man, f, allow_unicode=True, sort_keys=False, width=200)
    print(f'{cambios} documentos registrados; {len(pendientes)} sin descargar.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
