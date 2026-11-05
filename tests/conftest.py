"""Utilidades comunes: un ODT mínimo construido en memoria con la estructura de los oficiales."""
import zipfile
from xml.sax.saxutils import escape

import pytest

CABECERA = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
            'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0">'
            '<office:body><office:text>')
PIE = '</office:text></office:body></office:document-content>'


def p(texto):
    return f'<text:p>{escape(texto)}</text:p>'


def lista(*items):
    """Lista ODT; cada item es un texto o una tupla (texto, lista anidada)."""
    out = []
    for it in items:
        texto, sub = it if isinstance(it, tuple) else (it, '')
        out.append(f'<text:list-item>{p(texto)}{sub}</text:list-item>')
    return f'<text:list>{"".join(out)}</text:list>'


def tabla(*filas):
    """Tabla ODT; cada fila es una lista de celdas y cada celda, una lista de párrafos."""
    return ('<table:table>' + ''.join(
        '<table:table-row>' + ''.join(f'<table:table-cell>{"".join(p(x) for x in celda)}</table:table-cell>'
                                      for celda in fila) + '</table:table-row>'
        for fila in filas) + '</table:table>')


@pytest.fixture
def crear_odt(tmp_path):
    def crear(*partes, nombre='doc.odt'):
        ruta = tmp_path / nombre
        with zipfile.ZipFile(ruta, 'w') as z:
            z.writestr('content.xml', CABECERA + ''.join(partes) + PIE)
        return ruta
    return crear
