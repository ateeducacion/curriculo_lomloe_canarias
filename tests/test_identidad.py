from herramientas import identidad


def _nodos(*pares):
    return [{'id': i, 'tipo': t} for i, t in pares]


def test_sin_versiones_publicadas_no_hay_avisos(tmp_path):
    assert identidad.comprobar(_nodos(('sb:A', 'SaberBasico')), tmp_path) == []


def test_compara_con_la_ultima_version(tmp_path):
    identidad.registrar(_nodos(('sb:A', 'SaberBasico')), '1.2.0', tmp_path)
    identidad.registrar(_nodos(('sb:A', 'SaberBasico'), ('sb:B', 'SaberBasico'), ('sb:C', 'BloqueSaberes')),
                        '1.10.0', tmp_path)
    # 1.10.0 es posterior a 1.2.0 aunque como texto ordene antes.
    assert identidad.ultima(tmp_path).name == '1.10.0.csv'
    avisos = identidad.comprobar(_nodos(('sb:A', 'SaberBasico'), ('sb:C', 'SaberBasico'), ('sb:D', 'SaberBasico')),
                                 tmp_path)
    assert [(a['regla'], a['nodo'], a['nivel']) for a in avisos] == [
        ('nodo_publicado_desaparecido', 'sb:B', 'error'), ('tipo_publicado_cambiado', 'sb:C', 'error')]


def test_un_nodo_retirado_sigue_estando(tmp_path):
    identidad.registrar(_nodos(('sb:A', 'SaberBasico')), '1.0.0', tmp_path)
    assert identidad.comprobar([{'id': 'sb:A', 'tipo': 'SaberBasico', 'obsoleto': True}], tmp_path) == []


def test_la_1_0_0_publicada_esta_registrada():
    ruta = identidad.ultima()
    assert ruta is not None and identidad._version(ruta) >= (1, 0, 0)
