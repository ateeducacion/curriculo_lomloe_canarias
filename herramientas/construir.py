"""Construye el corpus: importa la base, aplica correcciones, valida y escribe datos/.

Uso:
    python -m herramientas.construir              # regenera datos/ e informes/
    python -m herramientas.construir --comprobar  # falla si datos/ no está al día (CI)
    python -m herramientas.construir --dist --version 1.0.0   # además, ficheros de publicación

Sale con código 1 si hay errores de validación que no figuran en
config/incidencias_aceptadas.yaml, si se detecta un posible secreto o si, con
--comprobar, datos/ no coincide con lo que produce el proceso.
"""
import argparse
import csv
import datetime
import io
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict

from . import correcciones, importar_proideac, validar
from .comun import (CONFIG, DATOS, DIST, ETAPAS, INFORMES, RAIZ, RE_SECRETO, TIPOS,
                    descriptores_por_etapa, escribir_json, etiqueta, leer_json, leer_yaml, sha256)

ORDEN = {t: i for i, t in enumerate(TIPOS)}
CAMPOS = ['id', 'tipo', 'notation', 'prefLabel', 'definition', 'scopeNote', 'broader', 'agrupa', 'bloque',
          'descriptores', 'cursos', 'materia', 'curso', 'etapa']


def _natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', s)]


def _clave(n):
    return (ORDEN[n['tipo']], _natural(n['id']))


def _finalizar(nodos):
    for n in nodos.values():
        if n['tipo'] in ('CompetenciaEspecifica', 'CriterioEvaluacion', 'SaberBasico'):
            n['prefLabel'] = etiqueta(n['notation'], n.get('definition'))
        elif n['tipo'] == 'BloqueSaberes':
            romano = n['notation'].rsplit('SB', 1)[1]
            n['prefLabel'] = f"{n['notation']} · {romano}. {n['definition']}" if n.get('definition') else n['notation']
        if 'cursos' in n:
            n['cursos'] = sorted(set(n['cursos']), key=_natural)
    return [{k: n[k] for k in CAMPOS if k in n} for n in sorted(nodos.values(), key=_clave)]


def _escaneo_secretos():
    hallazgos = []
    for ruta in RAIZ.rglob('*'):
        if not ruta.is_file() or any(p in ('.git', 'dist', '__pycache__', '.venv') for p in ruta.parts):
            continue
        if ruta.suffix.lower() not in ('.json', '.yaml', '.yml', '.csv', '.md', '.py', '.txt', '.toml'):
            continue
        try:
            if RE_SECRETO.search(ruta.read_text(encoding='utf-8', errors='ignore')):
                hallazgos.append(str(ruta.relative_to(RAIZ)))
        except OSError:
            pass
    return hallazgos


def construir(version=None):
    conf = leer_yaml(CONFIG / 'corpus.yaml')
    base = RAIZ / conf['base']['fichero']
    imp = importar_proideac.importar(leer_json(base))
    nodos = imp.nodos
    av_corr, resumen_corr = correcciones.aplicar(nodos)
    lista = _finalizar(nodos)
    corpus = {
        'corpus': {
            'marco': conf['marco'], 'ambito': conf['ambito'],
            'version': version or conf.get('version', '0.0.0'),
            'base': {**conf['base'], 'sha256': sha256(base)},
            'normas': conf.get('normas', []),
            'licencia': conf.get('licencia'),
            'correcciones_aplicadas': [c['id'] for c in resumen_corr if c['estado'] == 'aprobada'],
        },
        'nodos': lista,
    }
    avisos = imp.avisos + av_corr + validar.validar(corpus, descriptores_por_etapa())
    return corpus, avisos, resumen_corr


def _ficheros_datos(corpus):
    grupos = defaultdict(list)
    carpeta = {v[0]: v[3] for v in ETAPAS.values()}
    for n in corpus['nodos']:
        if n['tipo'] in ('Etapa', 'Curso'):
            grupos['niveles.json'].append(n)
        else:
            mid = n['id'] if n['tipo'] == 'Materia' else n['materia']
            grupos[f"{carpeta[n['etapa']]}/{mid.split(':')[1]}.json"].append(n)
    salida = {}
    for rel, ns in grupos.items():
        contenido = {'materia': ns[0]['id'] if ns[0]['tipo'] == 'Materia' else None, 'nodos': ns}
        if rel == 'niveles.json':
            contenido = {'nodos': ns}
        salida[rel] = json.dumps(contenido, ensure_ascii=False, indent=2) + '\n'
    return salida


def _clasificar(avisos):
    aceptadas = leer_yaml(CONFIG / 'incidencias_aceptadas.yaml').get('incidencias', []) or []
    claves_ok = {i['clave'] for i in aceptadas}
    errores = [a for a in avisos if a['nivel'] == 'error']
    nuevos = [a for a in errores if f"{a['regla']}:{a['nodo']}" not in claves_ok]
    actuales = {f"{a['regla']}:{a['nodo']}" for a in errores}
    resueltas = sorted(claves_ok - actuales)
    return errores, nuevos, resueltas


def _resumen_md(corpus, avisos, resumen_corr, nuevos, resueltas, secretos, desfase):
    tipos = Counter(n['tipo'] for n in corpus['nodos'])
    reglas = Counter((a['nivel'], a['regla']) for a in avisos)
    l = [f"# Informe de construcción — versión {corpus['corpus']['version']}", '',
         '## Nodos', '', '| Tipo | Nodos |', '|---|---|']
    l += [f'| {t} | {tipos[t]} |' for t in TIPOS if tipos[t]]
    l += ['', f"**Total:** {sum(tipos.values())}", '', '## Incidencias', '',
          '| Nivel | Regla | Casos |', '|---|---|---|']
    l += [f'| {nivel} | {regla} | {n} |' for (nivel, regla), n in sorted(reglas.items())]
    l += ['', f'- Errores nuevos (no aceptados): **{len(nuevos)}**']
    por_regla = defaultdict(list)
    for a in nuevos:
        por_regla[a['regla']].append(a)
    for regla, lista in sorted(por_regla.items()):
        ejemplos = ', '.join(f"`{a['nodo']}`" for a in lista[:5])
        l.append(f"  - `{regla}` ({len(lista)}): {ejemplos}. {lista[0]['detalle']}")
    if resueltas:
        l.append(f'- Incidencias aceptadas que ya no se producen (pueden retirarse): {len(resueltas)}')
    if secretos:
        l.append(f'- **Posibles secretos en el repositorio:** {", ".join(secretos)}')
    if desfase:
        l.append(f'- **datos/ no está al día** ({len(desfase)} ficheros). Ejecuta `python -m herramientas.construir`.')
    l += ['', '## Correcciones', '', '| Fichero | Estado | Cambios | Título |', '|---|---|---|---|']
    l += [f"| {c['fichero']} | {c['estado']} | {c['cambios']} | {c['titulo']} |" for c in resumen_corr]
    return '\n'.join(l) + '\n'


def _dist(corpus):
    DIST.mkdir(exist_ok=True)
    corpus['corpus']['generado'] = datetime.date.today().isoformat()
    ruta = DIST / 'curriculo.json'
    escribir_json(ruta, corpus)
    (DIST / 'curriculo.json.sha256').write_text(f'{sha256(ruta)}  curriculo.json\n', encoding='utf-8')
    with zipfile.ZipFile(DIST / 'curriculo-csv.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        por_tipo = defaultdict(list)
        for n in corpus['nodos']:
            por_tipo[n['tipo']].append(n)
        for tipo, ns in por_tipo.items():
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=CAMPOS, extrasaction='ignore', lineterminator='\n')
            w.writeheader()
            for n in ns:
                w.writerow({k: '|'.join(v) if isinstance(v, list) else v for k, v in n.items()})
            z.writestr(f'{tipo}.csv', buf.getvalue())


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--comprobar', action='store_true', help='no escribe datos/; falla si no está al día')
    p.add_argument('--dist', action='store_true', help='genera dist/ para publicar')
    p.add_argument('--version', help='versión del corpus (por defecto, la de config/corpus.yaml)')
    args = p.parse_args(argv)

    corpus, avisos, resumen_corr = construir(args.version)
    errores, nuevos, resueltas = _clasificar(avisos)
    secretos = _escaneo_secretos()

    ficheros = _ficheros_datos(corpus)
    desfase = []
    existentes = {str(r.relative_to(DATOS)) for r in DATOS.rglob('*.json')}
    for rel, contenido in ficheros.items():
        ruta = DATOS / rel
        if not ruta.exists() or ruta.read_text(encoding='utf-8') != contenido:
            desfase.append(rel)
    desfase += sorted(existentes - set(ficheros))
    if not args.comprobar:
        for rel in existentes - set(ficheros):
            (DATOS / rel).unlink()
        for rel in desfase:
            if rel in ficheros:
                (DATOS / rel).parent.mkdir(parents=True, exist_ok=True)
                (DATOS / rel).write_text(ficheros[rel], encoding='utf-8')
        desfase = []

    INFORMES.mkdir(exist_ok=True)
    escribir_json(INFORMES / 'validacion.json', {'errores_nuevos': nuevos, 'incidencias_resueltas': resueltas,
                                                'avisos': avisos})
    md = _resumen_md(corpus, avisos, resumen_corr, nuevos, resueltas, secretos, desfase)
    (INFORMES / 'resumen.md').write_text(md, encoding='utf-8')
    if args.dist:
        _dist(corpus)
    print(md)
    return 1 if (nuevos or secretos or desfase) else 0


if __name__ == '__main__':
    sys.exit(main())
