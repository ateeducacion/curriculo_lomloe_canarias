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


_DESC = r'(?:CCL|CP|STEM|CD|CPSAA|CC|CE|CCEC)\d(?:\.\d)?'
_SECUENCIA_CODIGOS = re.compile(r'\s*\b' + _DESC + r'(?:\s*,\s*' + _DESC + r')*[.,]?(?=\s|$)')
_DESCRIPTOR_ANTES = re.compile(_DESC + r',\s*$')
_DESCRIPTOR_DESPUES = re.compile(r'(?:\.\d|,\s*' + _DESC + ')')


def _palabras(s):
    return re.sub(r'\W+', ' ', (s or '').lower()).strip()


def _literal(s):
    s = (s or '').replace('\xa0', ' ').replace('“', '"').replace('”', '"').replace('’', "'")
    return re.sub(r'\s+', ' ', s).strip()


class Boletin:
    def __init__(self, texto):
        lineas = [l for l in unicodedata.normalize('NFC', texto).splitlines() if not _CABECERA.match(l)]
        unido = re.sub(r'(\w)-\n(\w)', r'\1\2', '\n'.join(lineas))
        # En las tablas, pdftotext intercala los descriptores en mitad del criterio
        # («…de diseño CCL1, STEM1, STEM2 utilizando…»): para buscar textos se quitan.
        sin_codigos = _SECUENCIA_CODIGOS.sub(' ', unido)
        self.palabras = _palabras(sin_codigos)
        self.literal_textos = _literal(sin_codigos)
        self.literal = _literal(unido)

    def contiene(self, s):
        """El texto aparece en el boletín: mismas palabras, sin tener en cuenta la puntuación."""
        return _buscar(_palabras(s), self.palabras)

    def contiene_literal(self, s):
        """Como contiene(), pero con la puntuación exacta (espacios y comillas normalizados)."""
        return _buscar(_literal(s), self.literal_textos)

    def contiene_descriptores(self, lista):
        """La lista de descriptores aparece completa en el boletín, sin otros descriptores pegados."""
        if not lista:
            return False
        s = ', '.join(lista)
        pos = self.literal.find(s)
        while pos >= 0:
            antes = self.literal[max(0, pos - 12):pos]
            despues = self.literal[pos + len(s):pos + len(s) + 12]
            if not _DESCRIPTOR_ANTES.search(antes) and not _DESCRIPTOR_DESPUES.match(despues):
                return True
            pos = self.literal.find(s, pos + 1)
        return False

    def exacto(self, s):
        """El texto aparece completo, sin tolerar ningún trozo que no se encuentre."""
        return _buscar(_palabras(s), self.palabras, tolerancia=0)

    def numeros(self, s, n=12):
        """Apariciones del texto en el boletín, buscando sus primeras `n` palabras.

        Devuelve [(posición, número, palabras que coinciden seguidas desde el inicio)]. Sirve
        para los criterios de evaluación, que el boletín imprime como «5.1. Texto…»; el número
        es None si no lo lleva delante. Un mismo comienzo puede aparecer en varios cursos,
        materias o criterios con números distintos: quien llama elige la aparición.
        """
        palabras = _palabras(s).split(' ')
        inicio = ' '.join(palabras[:n])
        if not inicio:
            return []
        en, encontrados, pos = f' {self.palabras} ', [], 0
        while (j := en.find(f' {inicio} ', pos)) >= 0:
            m = re.search(r'(?:^| )(\d+) (\d+) $', en[max(0, j - 12):j + 1])
            siguientes = en[j + 1:j + 1 + len(' '.join(palabras)) + 1].split(' ')
            iguales = next((k for k, (a, b) in enumerate(zip(palabras, siguientes)) if a != b), min(len(palabras), len(siguientes)))
            encontrados.append((j, f'{m.group(1)}.{m.group(2)}' if m else None, iguales))
            pos = j + 1
        return encontrados


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
