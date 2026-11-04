"""Texto de las normas publicadas en el BOC, para comprobar qué versión de un texto es la oficial.

fuentes/boletines/<norma>.txt es la salida de `pdftotext` (sin opciones) del PDF del BOC
cuyo enlace y sha256 están en el manifiesto (`boletin_pdf`, `boletin_pdf_sha256`).
Se quitan las cabeceras y pies de página y se unen las palabras partidas a final de línea.
"""
import re
import unicodedata

from .comun import FUENTES

_CABECERA = re.compile(r'^\s*(Boletín Oficial de Canarias núm\.|https?://|boc-a-\d|Folio \d|\d+\s*$|'
                       r'(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo) \d+ de )')


def _palabras(s):
    return re.sub(r'\W+', ' ', (s or '').lower()).strip()


def _literal(s):
    s = (s or '').replace('\xa0', ' ').replace('“', '"').replace('”', '"').replace('’', "'")
    return re.sub(r'\s+', ' ', s).strip()


class Boletin:
    def __init__(self, texto):
        lineas = [l for l in unicodedata.normalize('NFC', texto).splitlines() if not _CABECERA.match(l)]
        unido = re.sub(r'(\w)-\n(\w)', r'\1\2', '\n'.join(lineas))
        self.palabras = _palabras(unido)
        self.literal = _literal(unido)

    def contiene(self, s):
        """El texto aparece en el boletín: mismas palabras, sin tener en cuenta la puntuación."""
        return _buscar(_palabras(s), self.palabras)

    def contiene_literal(self, s):
        """Como contiene(), pero con la puntuación exacta (espacios y comillas normalizados)."""
        return _buscar(_literal(s), self.literal)

    def exacto(self, s):
        """El texto aparece completo, sin tolerar ningún trozo que no se encuentre."""
        return _buscar(_palabras(s), self.palabras, tolerancia=0)


def _buscar(n, en, tolerancia=1):
    """Busca el texto por trozos de 10 palabras completas, en orden.

    Se tolera que falle un trozo de cada texto largo: un salto de página en medio puede
    intercalar una cabecera que no siempre se reconoce.
    """
    palabras = n.split(' ')
    if not n:
        return False
    if len(palabras) <= 10:
        return f' {n} ' in f' {en} '
    trozos = [' '.join(palabras[i:i + 10]) for i in range(0, len(palabras), 10)]
    pos, fallos = 0, 0
    for trozo in trozos:
        j = f' {en} '.find(f' {trozo} ', pos)
        if j < 0:
            fallos += 1
            if fallos > tolerancia:
                return False
            continue
        pos = j + len(trozo)
    return fallos == 0 or len(trozos) >= 4


_cache = {}


def de_norma(manifiesto, norma_id):
    """Boletín de una norma del manifiesto, o None si no tiene texto registrado."""
    if norma_id not in _cache:
        norma = next((n for n in manifiesto.get('normas', []) if n['id'] == norma_id), None)
        ruta = FUENTES / norma['boletin_texto'] if norma and norma.get('boletin_texto') else None
        _cache[norma_id] = Boletin(ruta.read_text(encoding='utf-8')) if ruta and ruta.exists() else None
    return _cache[norma_id]
