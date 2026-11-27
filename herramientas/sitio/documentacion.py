"""Sección de documentación del sitio: páginas escritas a mano para docentes y asesores.

Cada página es un fragmento HTML en textos/; aquí se envuelve con la plantilla común. Los
marcadores {{clave}} se sustituyen al generar (base del sitio, versión y cifras del corpus), para
que los datos no se queden desfasados. Falla si queda algún marcador sin sustituir.
"""
import re
from pathlib import Path

from ..comun import FUENTES, leer_yaml
from .plantilla import REPOSITORIO, e, pagina

TEXTOS = Path(__file__).parent / 'textos'
MANIFIESTO = FUENTES / 'manifiesto.yaml'
# (carpeta bajo documentacion/, fichero en textos/, título)
PAGINAS = [
    ('', 'proyecto.html', 'Sobre el proyecto'),
    ('organizacion', 'organizacion.html', 'Cómo se organiza el currículo'),
    ('fuentes', 'fuentes.html', 'Fuentes y revisión'),
    ('codigos', 'codigos.html', 'Códigos, enlaces y datos'),
]
RE_MARCADOR = re.compile(r'\{\{(\w+)\}\}')


def _miles(n):
    return f'{n:,}'.replace(',', '.')


def valores(c, version, manifiesto=MANIFIESTO):
    """Valores de los marcadores: base, versión, enlaces, cifras de elementos vigentes y número de
    documentos oficiales con los que se contrasta el corpus (los del manifiesto con fichero local)."""
    def cuenta(tipo):
        return _miles(sum(1 for u in c.nodos(tipo) if not c.retirado(u)))
    documentos = sum(1 for d in leer_yaml(manifiesto).get('documentos', []) if d.get('fichero'))
    if version:
        descargas = f'{REPOSITORIO}/releases/tag/v{version}'
        texto_version = f'v{version}'
    else:
        descargas, texto_version = f'{REPOSITORIO}/releases', 'en desarrollo'
    return {
        'base': e(c.base), 'repositorio': REPOSITORIO, 'version': e(texto_version), 'descargas': e(descargas),
        'etapas': cuenta('Etapa'), 'cursos': cuenta('Curso'), 'materias': cuenta('Materia'),
        'competencias': cuenta('CompetenciaEspecifica'), 'bloques': cuenta('BloqueCompetencial'),
        'criterios': cuenta('CriterioEvaluacion'), 'saberes': cuenta('SaberBasico'),
        'documentos': _miles(documentos),
    }


def _sustituir(texto, datos, fichero):
    def cambia(m):
        if m.group(1) not in datos:
            raise ValueError(f'{fichero}: marcador desconocido {m.group(0)}')
        return str(datos[m.group(1)])
    return RE_MARCADOR.sub(cambia, texto)


def _navegacion(base, i):
    def enlace(j, prefijo, sufijo):
        carpeta, _, titulo = PAGINAS[j]
        ruta = f'{base}documentacion/' + (f'{carpeta}/' if carpeta else '')
        return f'<a href="{e(ruta)}">{prefijo}{e(titulo)}{sufijo}</a>'
    anterior = enlace(i - 1, '← ', '') if i > 0 else '<span></span>'
    siguiente = enlace(i + 1, '', ' →') if i + 1 < len(PAGINAS) else '<span></span>'
    return f'<nav class="doc-nav" aria-label="Páginas de la documentación">{anterior}{siguiente}</nav>'


def escribir(c, destino, version):
    """Escribe las páginas en <destino>/documentacion/."""
    base = c.base
    datos = valores(c, version)
    for i, (carpeta, fichero, titulo) in enumerate(PAGINAS):
        cuerpo = _sustituir((TEXTOS / fichero).read_text(encoding='utf-8'), datos, fichero)
        cuerpo = f'<article class="doc">\n{cuerpo}\n{_navegacion(base, i)}\n</article>'
        if carpeta:
            migas = [(base, 'Inicio'), (f'{base}documentacion/', 'Documentación'), (None, titulo)]
        else:
            migas = [(base, 'Inicio'), (None, 'Documentación')]
        salida = Path(destino) / 'documentacion' / carpeta
        salida.mkdir(parents=True, exist_ok=True)
        (salida / 'index.html').write_text(pagina(titulo, cuerpo, base, migas, version=version), encoding='utf-8')
