import pytest
import yaml

from herramientas import correcciones


@pytest.fixture
def carpeta(tmp_path, monkeypatch):
    monkeypatch.setattr(correcciones, 'CORRECCIONES', tmp_path)

    def escribir(nombre, cambios, estado='aprobada'):
        (tmp_path / nombre).write_text(yaml.safe_dump({'id': nombre[:4], 'titulo': 't', 'estado': estado,
                                                       'cambios': cambios}, allow_unicode=True), encoding='utf-8')
    return escribir


def _nodos():
    return {'sb:A': {'id': 'sb:A', 'definition': 'Texto viejo.', 'scopeNote': 'Sobra.'},
            'sb:B': {'id': 'sb:B', 'definition': 'Otro.'}}


def test_aplica_modificar_quitar_eliminar_y_crear(carpeta):
    carpeta('0001-x.yaml', [
        {'nodo': 'sb:A', 'campo': 'definition', 'valor': 'Texto nuevo.  '},
        {'nodo': 'sb:A', 'campo': 'scopeNote', 'valor': None},
        {'nodo': 'sb:B', 'accion': 'eliminar'},
        {'nodo': 'sb:C', 'accion': 'crear', 'datos': {'tipo': 'SaberBasico', 'definition': 'Creado.'}},
    ])
    nodos = _nodos()
    avisos, resumen = correcciones.aplicar(nodos)
    assert avisos == []
    # El valor se limpia como los textos importados: sin espacios de no separación ni sobrantes.
    assert nodos['sb:A'] == {'id': 'sb:A', 'definition': 'Texto nuevo.'}
    assert 'sb:B' not in nodos
    assert nodos['sb:C'] == {'id': 'sb:C', 'tipo': 'SaberBasico', 'definition': 'Creado.'}
    assert resumen[0]['cambios'] == 4


def test_solo_se_aplican_las_aprobadas(carpeta):
    carpeta('0001-x.yaml', [{'nodo': 'sb:A', 'campo': 'definition', 'valor': 'Propuesto.'}], estado='propuesta')
    nodos = _nodos()
    correcciones.aplicar(nodos)
    assert nodos['sb:A']['definition'] == 'Texto viejo.'


def test_avisos(carpeta):
    carpeta('0001-x.yaml', [
        {'nodo': 'sb:Z', 'campo': 'definition', 'valor': 'x'},
        {'nodo': 'sb:A', 'campo': 'tipo', 'valor': 'x'},
        {'nodo': 'sb:B', 'campo': 'definition', 'valor': 'Otro.'},
        {'nodo': 'sb:A', 'accion': 'crear', 'datos': {}},
    ])
    avisos, _ = correcciones.aplicar(_nodos())
    assert [(a['regla'], a['nivel']) for a in avisos] == [
        ('correccion_nodo_inexistente', 'error'), ('correccion_campo_no_editable', 'error'),
        ('correccion_innecesaria', 'aviso'), ('correccion_innecesaria', 'aviso')]


def test_se_aplican_en_orden_de_fichero(carpeta):
    carpeta('0002-b.yaml', [{'nodo': 'sb:A', 'campo': 'definition', 'valor': 'Segunda.'}])
    carpeta('0001-a.yaml', [{'nodo': 'sb:A', 'campo': 'definition', 'valor': 'Primera.'}])
    nodos = _nodos()
    correcciones.aplicar(nodos)
    assert nodos['sb:A']['definition'] == 'Segunda.'
