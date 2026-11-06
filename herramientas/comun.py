"""Utilidades comunes: rutas, configuración, patrones de códigos y E/S."""
import csv
import hashlib
import json
import re
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
FUENTES = RAIZ / 'fuentes'
CONFIG = RAIZ / 'config'
CORRECCIONES = RAIZ / 'correcciones'
DATOS = RAIZ / 'datos'
ESQUEMA = RAIZ / 'esquema' / 'curriculo.schema.json'
INFORMES = RAIZ / 'informes'
DIST = RAIZ / 'dist'

# Letra inicial de los códigos -> (id de etapa, clave en la exportación, nombre, carpeta)
ETAPAS = {
    'I': ('etapa:INF', 'Educación Infantil', 'Educación Infantil', 'infantil'),
    'P': ('etapa:PRI', 'Educación Primaria', 'Educación Primaria', 'primaria'),
    'S': ('etapa:ESO', 'ESO', 'Educación Secundaria Obligatoria', 'eso'),
    'B': ('etapa:BAC', 'Bachillerato', 'Bachillerato', 'bachillerato'),
}
ETAPA_POR_CLAVE = {v[1]: k for k, v in ETAPAS.items()}

ROMANO = r'(?:XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)'
RE_CLAVE_CE = re.compile(r'^([IPSB])([A-Z0-9]{3})C(\d+)$')
RE_CRITERIO = re.compile(r'^([IPSB])([A-Z0-9]{3})(\d{2})CE(\d+)\.(\d+)$')
RE_SABER = re.compile(rf'^([IPSB])([A-Z0-9]{{3}})(\d{{2}})SB({ROMANO})((?:\.\d+)+)$')
RE_BLOQUE_SABERES = re.compile(rf'^({ROMANO})\.\s+(.+)$')
RE_PREFIJO_NUM = re.compile(r'^\s*(\d+(?:\.\d+)*)\.?\s+(.*)$', re.S)
RE_SECRETO = re.compile(r'sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}'
                        r'|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}'
                        r'|-----BEGIN [A-Z ]*PRIVATE KEY-----')

TIPOS = ['Etapa', 'Curso', 'Materia', 'MateriaCurso', 'CompetenciaEspecifica', 'BloqueCompetencial',
         'CriterioEvaluacion', 'BloqueSaberes', 'SaberBasico']


def curso_id(letra, num):
    return f'curso:{letra}{num}'


def leer_json(ruta):
    with open(ruta, encoding='utf-8') as f:
        return json.load(f)


def escribir_json(ruta, datos):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write('\n')


def leer_yaml(ruta):
    with open(ruta, encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def leer_csv(ruta):
    with open(ruta, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for trozo in iter(lambda: f.read(1 << 16), b''):
            h.update(trozo)
    return h.hexdigest()


def etiqueta(codigo, texto, n=90):
    """prefLabel: código y comienzo del texto, cortado en palabra completa."""
    if not texto:
        return codigo
    texto = ' '.join(texto.split())
    if len(texto) > n:
        texto = texto[:n].rsplit(' ', 1)[0] + '…'
    return f'{codigo} · {texto}'


def descriptores_por_etapa():
    resultado = {}
    for fila in leer_csv(CONFIG / 'descriptores.csv'):
        resultado.setdefault(fila['etapa'], set()).add(fila['codigo'])
    return resultado


def materias_config():
    return {(f['etapa'], f['codigo']): f for f in leer_csv(CONFIG / 'materias.csv')}
