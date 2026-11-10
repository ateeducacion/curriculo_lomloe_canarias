"""Páginas para personas: portada, etapa, curso, materia, materia en un curso y fichas.

Cada función devuelve (título, cuerpo HTML, ruta de navegación); la plantilla pone el resto.
"""
from rdflib.namespace import DCTERMS

from .datos import ROTULOS, clave_natural
from .plantilla import REPOSITORIO, e

ORDEN_ETAPAS = ['INF', 'PRI', 'ESO', 'BAC']
EJEMPLOS = ['fracciones', 'SMAT01CE1.1', 'contaminación lumínica']


def _n(cantidad, singular, plural):
    return f'{cantidad} {singular if cantidad == 1 else plural}'


def _a(u, texto, clase=None):
    cls = f' class="{clase}"' if clase else ''
    return f'<a href="{e(u)}"{cls}>{e(texto)}</a>'


def _cabecera_tipo(c, u):
    tipo = c.tipo(u)
    return (f'<p><span class="tipo tipo-{tipo}">{e(ROTULOS[tipo])}</span>'
            f'<span class="codigo">{e(c.codigo(u))}</span></p>')


def _aviso_retirado(c, u):
    if not c.retirado(u):
        return ''
    s = c.sustituto(u)
    sust = f' Lo sustituye {_a(s, c.etiqueta(s))}.' if s is not None else ''
    return f'<p class="aviso">Elemento retirado: se conserva para no romper los enlaces.{sust}</p>'


def _chips(c, u):
    return ' '.join(f'<a class="chip" href="{e(d)}" title="{e(nombre)}">{e(cod)}</a>'
                    for d, cod, nombre in c.descriptores(u))


def _li(c, u, contenido):
    cls = ' class="retirado"' if c.retirado(u) else ''
    return f'<li{cls}>{contenido}</li>'


def _tecnico(c, u):
    ident = c.g.value(u, DCTERMS.identifier)
    return ('<details class="tecnico"><summary>Datos técnicos</summary><ul>'
            f'<li>URI: <code>{e(u)}</code></li>'
            + (f'<li>Identificador: <code>{e(ident)}</code></li>' if ident is not None else '')
            + '<li><a href="index.ttl">Descripción en Turtle</a></li></ul></details>')


def _relacionado(filas):
    filas = [(r, v) for r, v in filas if v]
    if not filas:
        return ''
    return '<dl class="relacionado">' + ''.join(f'<dt>{e(r)}</dt><dd>{v}</dd>' for r, v in filas) + '</dl>'


def _lista(items):
    return '<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>' if items else ''


def _arbol(c, u):
    """Saberes que cuelgan de u, en árbol; los retirados, marcados."""
    hijos = c.hijos(u)
    if not hijos:
        return ''
    filas = []
    for h in hijos:
        texto = c.texto(h) or c.etiqueta(h)
        filas.append(_li(c, h, f'<a href="{e(h)}"><span class="num">{e(c.numero(h))}</span></a> {e(texto)}'
                                + _arbol(c, h)))
    return '<ul class="arbol">' + ''.join(filas) + '</ul>'


def _vigentes(c, nodos):
    return [n for n in nodos if not c.retirado(n)]


def _criterio_en_lista(c, crit):
    chips = _chips(c, crit)
    return _li(c, crit, f'<a href="{e(crit)}"><span class="num">{e(c.numero(crit))}</span></a> '
                        f'{e(c.texto(crit) or c.etiqueta(crit))} <span class="codigo">{e(c.codigo(crit))}</span>'
                        + (f'<br>{chips}' if chips else ''))


# Portada y niveles superiores

def _etapas(c):
    return sorted(c.nodos('Etapa'), key=lambda u: (ORDEN_ETAPAS.index(c.codigo(u)) if c.codigo(u) in ORDEN_ETAPAS
                                                    else len(ORDEN_ETAPAS), clave_natural(c.codigo(u))))


def _cursos(c, etapa):
    return c.con('etapa', etapa, 'Curso') or c.hijos(etapa, 'Curso')


def portada(c, version, total):
    base = c.base
    tarjetas = []
    for et in _etapas(c):
        cursos = ' '.join(_a(cu, c.etiqueta(cu)) for cu in _cursos(c, et))
        materias = len(c.con('etapa', et, 'Materia'))
        tarjetas.append(f'<div class="tarjeta"><h2>{_a(et, c.nombre_etapa(et))}</h2>'
                        f'<p class="cursos">{cursos}</p><p class="cifras">{_n(materias, "materia", "materias")}</p></div>')
    ejemplos = ' · '.join(f'<a href="{e(base)}buscar/?q={e(x)}">{e(x)}</a>' for x in EJEMPLOS)
    pie = [f'{total:,}'.replace(',', '.') + ' elementos del currículo']
    if version:
        pie.insert(0, f'Versión {e(version)}')
        pie.append(f'<a href="{REPOSITORIO}/releases/tag/v{e(version)}">Descargas (JSON, CSV y Turtle)</a>')
    pie.append(f'<a href="{REPOSITORIO}">Qué es este proyecto</a>')
    cuerpo = (
        '<section class="portada"><h1>Currículo LOMLOE de Canarias</h1>'
        '<p class="lema">Competencias, criterios de evaluación y saberes básicos, de Infantil a Bachillerato</p>'
        f'<form class="buscador-portada" action="{e(base)}buscar/" role="search">'
        '<label class="oculto" for="q-portada">Buscar en el currículo</label>'
        '<input id="q-portada" name="q" type="search" placeholder="Busca un criterio, un saber, una materia…" autocomplete="off">'
        f'</form><p class="ejemplos">Por ejemplo: {ejemplos}</p></section>'
        f'<div class="etapas">{"".join(tarjetas)}</div>'
        f'<p class="cifras">{" · ".join(pie)}</p>')
    return 'Inicio', cuerpo, []


def etapa(c, u):
    cursos = ''.join(f'<li>{_a(cu, c.etiqueta(cu))}</li>' for cu in _cursos(c, u))
    materias = ''.join(f'<li>{_a(m, c.nombre_materia(m))}</li>' for m in c.con('etapa', u, 'Materia'))
    cuerpo = (f'<h1>{e(c.etiqueta(u))}</h1><h2>Cursos</h2><ul class="rejilla">{cursos}</ul>'
              f'<h2>Materias</h2><ul class="rejilla">{materias}</ul>')
    return c.etiqueta(u), cuerpo, c.migas(u)


def _cifras_materia_curso(c, mc):
    crits = _vigentes(c, c.con('materiaCurso', mc, 'CriterioEvaluacion'))
    ces = {c.padre(x) for x in crits}
    saberes = _vigentes(c, c.con('materiaCurso', mc, 'SaberBasico'))
    return ' · '.join([_n(len(ces), 'competencia', 'competencias'), _n(len(crits), 'criterio', 'criterios'),
                       _n(len(saberes), 'saber', 'saberes')])


def curso(c, u):
    filas = ''.join(f'<li>{_a(mc, c.nombre_materia(mc))}<br><span class="cifras">{_cifras_materia_curso(c, mc)}</span></li>'
                    for mc in sorted(c.con('curso', u, 'MateriaCurso'), key=lambda x: c.nombre_materia(x)))
    cuerpo = f'<h1>{e(c.etiqueta(u))}</h1><h2>Materias</h2><ul class="rejilla">{filas}</ul>'
    return c.etiqueta(u), cuerpo, c.migas(u)


def materia(c, u):
    cursos = ''.join(f'<li>{_a(mc, c.etiqueta(mc))}</li>' for mc in c.con('materia', u, 'MateriaCurso'))
    comps = []
    for ce in c.con('materia', u, 'CompetenciaEspecifica'):
        variantes = ''.join(f'<dt>{e(c.etiqueta(cu))}</dt><dd>{e(t)}</dd>' for cu, t in c.enunciados(ce))
        comps.append(f'<div class="competencia"><h3>{_a(ce, c.numero(ce))} <span class="codigo">{e(c.codigo(ce))}</span></h3>'
                     f'<p>{e(c.texto(ce) or c.etiqueta(ce))}</p>'
                     + (f'<details><summary>Enunciado en cada curso</summary><dl>{variantes}</dl></details>' if variantes else '')
                     + '</div>')
    cuerpo = (f'<h1>{e(c.etiqueta(u))}</h1>{_cabecera_tipo(c, u)}<h2>Cursos</h2><ul class="rejilla">{cursos}</ul>'
              f'<h2>Competencias específicas</h2>{"".join(comps) or "<p class=vacio>Sin competencias específicas.</p>"}')
    return c.etiqueta(u), cuerpo, c.migas(u)


def materia_curso(c, u):
    curso_u = c.atajo(u, 'curso')
    # Competencias y criterios
    crits = c.con('materiaCurso', u, 'CriterioEvaluacion')
    por_ce = {}
    for cr in crits:
        por_ce.setdefault(c.padre(cr), []).append(cr)
    bloques_ce = []
    for ce in sorted(por_ce, key=lambda x: clave_natural(c.codigo(x))):
        lista = ''.join(_criterio_en_lista(c, cr) for cr in por_ce[ce])
        bloques_ce.append(f'<div class="competencia"><h3>{_a(ce, "Competencia " + c.numero(ce))} '
                          f'<span class="codigo">{e(c.codigo(ce))}</span></h3>'
                          f'<p>{e(c.enunciado(ce, curso_u) or "")}</p><ul class="lista-criterios">{lista}</ul></div>')
    competencias = ''.join(bloques_ce) or '<p class="vacio">Sin criterios en este curso.</p>'
    # Saberes
    bs = c.hijos(u, 'BloqueSaberes') or c.con('materiaCurso', u, 'BloqueSaberes')
    saberes = ''.join(f'<div class="bloque-saberes"><h3>{_a(b, c.numero(b) + ". " + (c.texto(b) or c.etiqueta(b)))}</h3>'
                      + (f'<p class="nota">{e(c.nota(b))}</p>' if c.nota(b) else '') + _arbol(c, b) + '</div>'
                      for b in bs) or '<p class="vacio">Sin saberes en este curso.</p>'
    # Bloques competenciales
    bcs = c.hijos(u, 'BloqueCompetencial') or c.con('materiaCurso', u, 'BloqueCompetencial')
    filas_bc = []
    for bc in bcs:
        agrupa = ', '.join(_a(ce, 'Competencia ' + c.numero(ce)) for ce in
                           sorted(c.g.objects(bc, c.cur.agrupa), key=lambda x: clave_natural(c.codigo(x))))
        chips = _chips(c, bc)
        filas_bc.append(f'<div class="competencia"><h3>{_a(bc, "Bloque " + c.numero(bc))}</h3>'
                        + (f'<p>Agrupa: {agrupa}</p>' if agrupa else '')
                        + (f'<p>{e(c.nota(bc))}</p>' if c.nota(bc) else '')
                        + (f'<p>{chips}</p>' if chips else '') + '</div>')
    bloques = ''.join(filas_bc) or '<p class="vacio">Sin bloques competenciales en este curso.</p>'
    paneles = [('competencias', 'Competencias y criterios', competencias), ('saberes', 'Saberes básicos', saberes),
               ('bloques', 'Bloques competenciales', bloques)]
    pestanas = ''.join(f'<button type="button" role="tab" id="t-{k}" aria-controls="p-{k}" '
                       f'aria-selected="{"true" if i == 0 else "false"}">{e(r)}</button>'
                       for i, (k, r, _) in enumerate(paneles))
    secciones = ''.join(f'<section class="panel" id="p-{k}" role="tabpanel" aria-labelledby="t-{k}"><h2>{e(r)}</h2>{h}</section>'
                        for k, r, h in paneles)
    materia_u = c.atajo(u, 'materia')
    enlace_materia = (f'<p class="cifras">{_cifras_materia_curso(c, u)} · '
                      f'{_a(materia_u, "La materia en toda la etapa")}</p>' if materia_u is not None else '')
    cuerpo = (f'<h1>{e(c.etiqueta(u))}</h1>{enlace_materia}'
              f'<div class="pestanas" role="tablist" aria-label="Contenido de la materia" hidden>{pestanas}</div>{secciones}')
    return c.etiqueta(u), cuerpo, c.migas(u)


# Fichas

def _resumen(c, u, largo=90):
    t = c.texto(u) or c.etiqueta(u)
    return t if len(t) <= largo else t[:largo - 1].rstrip() + '…'


def ficha(c, u):
    tipo = c.tipo(u)
    mc = c.atajo(u, 'materiaCurso')
    filas = []
    if tipo == 'CriterioEvaluacion':
        ce, bc = c.padre(u), c.atajo(u, 'bloqueCompetencial')
        hermanos = [x for x in c.con('materiaCurso', mc, 'CriterioEvaluacion') if c.padre(x) == ce and x != u] if mc else []
        filas = [('Competencia específica', _a(ce, f'{c.numero(ce)} · {_resumen(c, ce)}') if ce is not None else ''),
                 ('Bloque competencial', _a(bc, 'Bloque ' + c.numero(bc)) if bc is not None else ''),
                 ('Descriptores operativos', _chips(c, u)),
                 (f'Otros criterios de la competencia {c.numero(ce) if ce is not None else ""} en este curso',
                  _lista([f'{_a(x, c.numero(x))} {e(_resumen(c, x))}' for x in hermanos]))]
    elif tipo == 'SaberBasico':
        p = c.padre(u)
        bs = p
        while bs is not None and c.tipo(bs) == 'SaberBasico':
            bs = c.padre(bs)
        filas = [('Bloque de saberes', _a(bs, f'{c.numero(bs)}. {c.texto(bs) or c.etiqueta(bs)}') if bs is not None else ''),
                 ('Apartado superior', _a(p, f'{c.numero(p)}. {_resumen(c, p)}') if p is not None and c.tipo(p) == 'SaberBasico' else ''),
                 ('Saberes que incluye', _arbol(c, u))]
    elif tipo == 'BloqueSaberes':
        filas = [('Saberes', _arbol(c, u))]
    elif tipo == 'CompetenciaEspecifica':
        materia_u = c.atajo(u, 'materia')
        por_curso = []
        for m in c.con('materia', materia_u, 'MateriaCurso') if materia_u is not None else []:
            crits = [x for x in c.con('materiaCurso', m, 'CriterioEvaluacion') if c.padre(x) == u]
            if crits:
                por_curso.append(f'<strong>{_a(m, c.etiqueta(m))}</strong>'
                                 + _lista([f'{_a(x, c.numero(x))} {e(_resumen(c, x))}' for x in crits]))
        enunciados = ''.join(f'<p><strong>{e(c.etiqueta(cu))}:</strong> {e(t)}</p>' for cu, t in c.enunciados(u))
        filas = [('Materia', _a(materia_u, c.etiqueta(materia_u)) if materia_u is not None else ''),
                 ('Enunciado en cada curso', enunciados),
                 ('Criterios por curso', ''.join(por_curso)),
                 ('Bloques competenciales que la agrupan',
                  _lista([_a(b, f'Bloque {c.numero(b)} · {c.etiqueta(c.atajo(b, "materiaCurso"))}')
                          for b in c.con('agrupada_por', u, 'BloqueCompetencial')]))]
    elif tipo == 'BloqueCompetencial':
        agrupa = sorted(c.g.objects(u, c.cur.agrupa), key=lambda x: clave_natural(c.codigo(x)))
        filas = [('Competencias que agrupa', _lista([f'{_a(ce, c.numero(ce))} {e(_resumen(c, ce))}' for ce in agrupa])),
                 ('Criterios del bloque', _lista([f'{_a(x, c.numero(x))} {e(_resumen(c, x))}'
                                                   for x in c.con('bloqueCompetencial', u, 'CriterioEvaluacion')])),
                 ('Descriptores operativos', _chips(c, u))]
    if mc is not None:
        filas.append(('Materia en un curso', _a(mc, c.etiqueta(mc))))
    titulo = f'{ROTULOS[tipo]} {c.numero(u)}'
    cuerpo = (_cabecera_tipo(c, u) + f'<h1>{e(titulo)}</h1>' + _aviso_retirado(c, u)
              + (f'<p class="texto">{e(c.texto(u))}</p>' if c.texto(u) else '')
              + (f'<p class="nota">{e(c.nota(u))}</p>' if c.nota(u) else '')
              + _relacionado(filas) + _tecnico(c, u))
    return f'{titulo} · {c.codigo(u)}', cuerpo, c.migas(u)


PAGINAS = {
    'Etapa': etapa, 'Curso': curso, 'Materia': materia, 'MateriaCurso': materia_curso,
    'CompetenciaEspecifica': ficha, 'BloqueCompetencial': ficha, 'CriterioEvaluacion': ficha,
    'BloqueSaberes': ficha, 'SaberBasico': ficha,
}


def buscar(c):
    cuerpo = (
        '<h1>Buscar en el currículo</h1>'
        '<noscript><p class="aviso">El buscador necesita JavaScript.</p></noscript>'
        '<form id="filtros" role="search" aria-label="Buscar y filtrar">'
        '<label class="oculto" for="q-resultados">Texto o código</label>'
        '<input id="q-resultados" name="q" type="search" placeholder="Texto o código…" autocomplete="off">'
        '<label class="oculto" for="f-e">Etapa</label><select id="f-e" name="e"><option value="">Todas las etapas</option></select>'
        '<label class="oculto" for="f-k">Tipo</label><select id="f-k" name="k"><option value="">Todos los tipos</option></select>'
        '<label class="oculto" for="f-m">Materia</label><select id="f-m" name="m"><option value="">Todas las materias</option></select>'
        '</form><p id="estado" aria-live="polite"></p><ol id="resultados"></ol>'
        '<button type="button" id="mas" hidden>Ver más</button>')
    return 'Buscar', cuerpo, [(c.base, 'Inicio'), (None, 'Buscar')]
