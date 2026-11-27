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
    return '<nav class="migas" aria-label="Ruta de navegación">' + ' <span aria-hidden="true">/</span> '.join(partes) + '</nav>\n'


ICONO_LUPA = ('<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
              'stroke-width="2.4" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>')


def buscador(base, ident, clase, marcador, rotulo=None):
    """Formulario de búsqueda; con `rotulo`, la etiqueta se ve (portada), y sin él solo la leen los lectores de pantalla."""
    etiqueta = (f'<label for="{ident}">{e(rotulo)}</label>' if rotulo
                else f'<label class="oculto" for="{ident}">Buscar en el currículo</label>')
    return (f'<form class="{clase}" action="{e(base)}buscar/" role="search">{etiqueta}'
            f'<div class="caja"><input id="{ident}" name="q" type="search" placeholder="{e(marcador)}" autocomplete="off">'
            f'<button type="submit">{ICONO_LUPA}<span>Buscar</span></button></div></form>')


DESCRIPCION = ('Competencias, criterios de evaluación y saberes básicos del currículo LOMLOE de Canarias, '
               'de Infantil a Bachillerato, para consultar, enlazar y descargar como datos abiertos.')


def tarjeta(titulo, base):
    """Etiquetas Open Graph y Twitter para la vista previa al compartir un enlace (og:image, URL absoluta)."""
    imagen = f'{e(base)}recursos/og-image.jpg'
    alt = 'Currículo LOMLOE de Canarias. Tarjeta del ATE con una captura del portal.'
    return (
        f'<meta name="description" content="{DESCRIPCION}">\n'
        f'<meta property="og:type" content="website">\n<meta property="og:locale" content="es_ES">\n'
        f'<meta property="og:site_name" content="{SITIO}">\n'
        f'<meta property="og:title" content="{e(titulo)} · {SITIO}">\n'
        f'<meta property="og:description" content="{DESCRIPCION}">\n'
        f'<meta property="og:image" content="{imagen}">\n<meta property="og:image:type" content="image/jpeg">\n'
        f'<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
        f'<meta property="og:image:alt" content="{alt}">\n'
        f'<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:image" content="{imagen}">\n<meta name="twitter:image:alt" content="{alt}">\n')


def pagina(titulo, cuerpo, base, migas=(), cabecera='', version=None, con_buscador=True):
    pie_version = f'Versión {e(version)} · ' if version else ''
    return (
        f'<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{e(titulo)} · {SITIO}</title>\n{tarjeta(titulo, base)}{cabecera}'
        f'<link rel="stylesheet" href="{e(base)}recursos/estilo.css">\n'
        f'<script defer src="{e(base)}recursos/buscar.js" data-base="{e(base)}"></script>\n'
        f'</head>\n<body>\n'
        f'<header class="cabecera"><div class="ancho">'
        f'<a class="marca" href="{e(base)}"><img src="{e(base)}recursos/logo-ate.png" width="39" height="40" '
        f'alt="Área de Tecnología Educativa"><span>{SITIO}</span></a>'
        + (buscador(base, 'q-cabecera', 'buscador', 'Texto o código…') if con_buscador else '')
        + f'<a class="enlace-doc" href="{e(base)}documentacion/">Documentación</a>'
        f'</div></header>\n'
        f'<main class="ancho">\n{migas_html(migas)}{cuerpo}\n</main>\n'
        f'<footer class="pie"><div class="ancho">'
        f'<p>Proyecto del Área de Tecnología Educativa para facilitar la consulta y reutilización del '
        f'currículo de Canarias. Esta herramienta tiene carácter informativo y no sustituye a la normativa '
        f'publicada en el Boletín Oficial de Canarias.</p><p>{pie_version}'
        f'<a href="{e(base)}documentacion/">Documentación</a> · '
        f'Datos <a href="{LICENCIA}">CC BY 4.0</a> · '
        f'<a href="{e(base)}id/curriculo">Datos enlazados</a> · '
        f'<a href="{e(base)}id/descriptores">Competencias clave y descriptores</a> · '
        f'<a href="{e(base)}def/cur">Vocabulario</a> · '
        f'<a href="{REPOSITORIO}">Repositorio</a></p>'
        f'</div></footer>\n</body>\n</html>\n')
