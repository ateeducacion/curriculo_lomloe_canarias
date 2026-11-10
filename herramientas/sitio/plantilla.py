"""Página base del sitio: cabecera con buscador, ruta de navegación, contenido y pie."""
from html import escape

REPOSITORIO = 'https://github.com/ateeducacion/curriculo_lomloe_canarias'
SITIO = 'Currículo LOMLOE de Canarias'
LICENCIA = 'https://creativecommons.org/licenses/by/4.0/'


def e(x):
    return escape(str(x))


def migas_html(migas):
    """Ruta de navegación: pares (URL, rótulo); el último, la página actual, sin enlace."""
    if not migas:
        return ''
    partes = [f'<a href="{e(u)}">{e(r)}</a>' if u else f'<span aria-current="page">{e(r)}</span>' for u, r in migas]
    return '<nav class="migas" aria-label="Ruta de navegación">' + ' <span aria-hidden="true">›</span> '.join(partes) + '</nav>\n'


def pagina(titulo, cuerpo, base, migas=(), cabecera='', version=None):
    pie_version = f'Versión {e(version)} · ' if version else ''
    return (
        f'<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{e(titulo)} · {SITIO}</title>\n{cabecera}'
        f'<link rel="stylesheet" href="{e(base)}recursos/estilo.css">\n'
        f'<script defer src="{e(base)}recursos/buscar.js" data-base="{e(base)}"></script>\n'
        f'</head>\n<body>\n'
        f'<header class="cabecera"><div class="ancho">'
        f'<a class="marca" href="{e(base)}">{SITIO}</a>'
        f'<form class="buscador" action="{e(base)}buscar/" role="search">'
        f'<label class="oculto" for="q-cabecera">Buscar en el currículo</label>'
        f'<input id="q-cabecera" name="q" type="search" placeholder="Buscar en el currículo…" autocomplete="off">'
        f'</form></div></header>\n'
        f'<main class="ancho">\n{migas_html(migas)}{cuerpo}\n</main>\n'
        f'<footer class="pie"><div class="ancho">{pie_version}'
        f'Datos <a href="{LICENCIA}">CC BY 4.0</a> · '
        f'<a href="{e(base)}id/curriculo">Datos enlazados</a> · '
        f'<a href="{e(base)}id/descriptores">Competencias clave y descriptores</a> · '
        f'<a href="{e(base)}def/cur">Vocabulario</a> · '
        f'<a href="{REPOSITORIO}">Repositorio</a>'
        f'</div></footer>\n</body>\n</html>\n')
