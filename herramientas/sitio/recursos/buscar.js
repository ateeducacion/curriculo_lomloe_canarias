/* Buscador, sugerencias y pestañas del sitio.
 * Sin dependencias salvo MiniSearch, que se carga (junto con buscar.json) la primera vez que
 * alguien enfoca un buscador: navegar por el sitio no descarga el índice. */
(function () {
  'use strict';
  var BASE = document.currentScript.getAttribute('data-base');
  var ETAPAS = { INF: 'Infantil', PRI: 'Primaria', ESO: 'ESO', BAC: 'Bachillerato' };
  var ORDEN_ETAPAS = ['INF', 'PRI', 'ESO', 'BAC'];
  var motor = null;
  var cargando = null;

  function normalizar(t) {
    return t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  }

  function recortar(t, n) {
    return t.length > n ? t.slice(0, n - 1) + '…' : t;
  }

  function demorar(fn, ms) {
    var t;
    return function () { clearTimeout(t); t = setTimeout(fn, ms); };
  }

  function nodo(tag, clase, texto) {
    var n = document.createElement(tag);
    if (clase) n.className = clase;
    if (texto !== undefined) n.textContent = texto;
    return n;
  }

  function cargar() {
    if (motor) return Promise.resolve(motor);
    if (cargando) return cargando;
    cargando = new Promise(function (ok, mal) {
      var s = document.createElement('script');
      s.src = BASE + 'recursos/minisearch.js';
      s.onload = ok;
      s.onerror = mal;
      document.head.appendChild(s);
    }).then(function () {
      return fetch(BASE + 'buscar.json');
    }).then(function (r) {
      if (!r.ok) throw new Error('buscar.json: ' + r.status);
      return r.json();
    }).then(function (datos) {
      var m = new window.MiniSearch({
        idField: 'u',
        fields: ['c', 't', 'r'],
        storeFields: ['u', 'c', 't', 'k', 'r', 'e', 'm'],
        processTerm: normalizar,
        // Una errata como mucho, y solo en palabras de 5 letras o más: con más tolerancia,
        // «fracciones» encontraría «acciones».
        searchOptions: { prefix: true, fuzzy: function (t) { return t.length >= 5 ? 1 : 0; }, boost: { c: 3 }, combineWith: 'AND' }
      });
      m.addAll(datos);
      motor = m;
      return m;
    });
    cargando.catch(function () { cargando = null; });
    return cargando;
  }

  // Contenido de un resultado: tipo, código, texto y ruta.
  function contenido(li, r, largo) {
    li.appendChild(nodo('span', 'tipo', r.k));
    li.appendChild(document.createTextNode(' '));
    li.appendChild(nodo('strong', null, r.c));
    li.appendChild(document.createTextNode(' ' + recortar(r.t, largo)));
    if (r.r) li.appendChild(nodo('span', 'ruta', r.r));
  }

  // Sugerencias mientras se escribe (cabecera y portada).
  function sugerencias(input) {
    var form = input.form;
    var lista = nodo('ul', 'sugerencias');
    lista.id = input.id + '-lista';
    lista.setAttribute('role', 'listbox');
    lista.hidden = true;
    form.appendChild(lista);
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-controls', lista.id);
    input.setAttribute('aria-expanded', 'false');
    var opciones = [];
    var activo = -1;

    function cerrar() {
      lista.hidden = true;
      input.setAttribute('aria-expanded', 'false');
      input.removeAttribute('aria-activedescendant');
      activo = -1;
    }

    function marcar(i) {
      opciones.forEach(function (o, j) { o.setAttribute('aria-selected', j === i ? 'true' : 'false'); });
      activo = i;
      if (i >= 0) input.setAttribute('aria-activedescendant', opciones[i].id);
    }

    function opcion(i, url) {
      var li = nodo('li');
      li.id = lista.id + '-' + i;
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', 'false');
      li.addEventListener('mousedown', function (ev) { ev.preventDefault(); location.href = url; });
      li.dataset.url = url;
      return li;
    }

    function pintar() {
      var q = input.value.trim();
      if (q.length < 2) { cerrar(); return; }
      cargar().then(function (m) {
        if (input.value.trim() !== q) return;
        var res = m.search(q);
        lista.textContent = '';
        opciones = [];
        res.slice(0, 8).forEach(function (r, i) {
          var li = opcion(i, r.u);
          contenido(li, r, 90);
          lista.appendChild(li);
          opciones.push(li);
        });
        var todos = opcion(opciones.length, BASE + 'buscar/?q=' + encodeURIComponent(q));
        todos.className = 'todos';
        todos.textContent = res.length ? 'Ver los ' + res.length + ' resultados →' : 'Sin resultados para «' + q + '»';
        lista.appendChild(todos);
        opciones.push(todos);
        lista.hidden = false;
        input.setAttribute('aria-expanded', 'true');
        marcar(-1);
      }).catch(function () { cerrar(); });
    }

    input.addEventListener('focus', function () { cargar().catch(function () {}); });
    input.addEventListener('input', demorar(pintar, 120));
    input.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape') { cerrar(); return; }
      if (lista.hidden) return;
      if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {
        ev.preventDefault();
        var n = opciones.length;
        marcar(ev.key === 'ArrowDown' ? (activo + 1) % n : (activo - 1 + n) % n);
      } else if (ev.key === 'Enter' && activo >= 0) {
        ev.preventDefault();
        location.href = opciones[activo].dataset.url;
      }
    });
    input.addEventListener('blur', function () { setTimeout(cerrar, 150); });
  }

  // Página de resultados con filtros, reflejados en la URL.
  function resultados() {
    var form = document.getElementById('filtros');
    if (!form) return;
    var q = form.elements.q;
    var filtros = { e: form.elements.e, k: form.elements.k, m: form.elements.m };
    var estado = document.getElementById('estado');
    var ol = document.getElementById('resultados');
    var mas = document.getElementById('mas');
    var params = new URLSearchParams(location.search);
    var elegidos = { e: params.get('e') || '', k: params.get('k') || '', m: params.get('m') || '' };
    var lista = [];
    var mostrados = 0;
    q.value = params.get('q') || '';

    function opciones(select, valores, rotulo) {
      var actual = elegidos[select.name];
      while (select.options.length > 1) select.remove(1);
      valores.forEach(function (v) {
        var o = nodo('option', null, rotulo ? rotulo(v) : v);
        o.value = v;
        if (v === actual) o.selected = true;
        select.appendChild(o);
      });
      if (actual && valores.indexOf(actual) < 0) {
        var o = nodo('option', null, rotulo ? rotulo(actual) : actual);
        o.value = actual;
        o.selected = true;
        select.appendChild(o);
      }
    }

    function distintos(res, clave) {
      var vistos = {};
      res.forEach(function (r) { if (r[clave]) vistos[r[clave]] = true; });
      return Object.keys(vistos);
    }

    function mostrar() {
      var hasta = Math.min(mostrados + 50, lista.length);
      for (var i = mostrados; i < hasta; i++) {
        var li = nodo('li', 'resultado');
        var a = nodo('a');
        a.href = lista[i].u;
        contenido(a, lista[i], 400);
        li.appendChild(a);
        ol.appendChild(li);
      }
      mostrados = hasta;
      mas.hidden = mostrados >= lista.length;
    }

    function actualizar() {
      var texto = q.value.trim();
      var todos = texto.length ? motor.search(texto) : [];
      opciones(filtros.e, distintos(todos, 'e').sort(function (a, b) {
        return ORDEN_ETAPAS.indexOf(a) - ORDEN_ETAPAS.indexOf(b);
      }), function (v) { return ETAPAS[v] || v; });
      opciones(filtros.k, distintos(todos, 'k').sort());
      opciones(filtros.m, distintos(todos, 'm').sort(function (a, b) { return a.localeCompare(b, 'es'); }));
      lista = todos.filter(function (r) {
        return (!elegidos.e || r.e === elegidos.e) && (!elegidos.k || r.k === elegidos.k) &&
               (!elegidos.m || r.m === elegidos.m);
      });
      ol.textContent = '';
      mostrados = 0;
      estado.textContent = !texto ? 'Escribe un texto o un código para buscar.' :
        lista.length === 1 ? '1 resultado para «' + texto + '».' :
        lista.length + ' resultados para «' + texto + '».';
      mostrar();
      var url = new URLSearchParams();
      if (texto) url.set('q', texto);
      ['e', 'k', 'm'].forEach(function (k) { if (elegidos[k]) url.set(k, elegidos[k]); });
      var cadena = url.toString();
      history.replaceState(null, '', location.pathname + (cadena ? '?' + cadena : ''));
    }

    estado.textContent = 'Cargando el índice…';
    cargar().then(actualizar).catch(function () {
      estado.textContent = 'No se pudo cargar el índice de búsqueda.';
    });
    form.addEventListener('submit', function (ev) { ev.preventDefault(); if (motor) actualizar(); });
    q.addEventListener('input', demorar(function () { if (motor) actualizar(); }, 200));
    Object.keys(filtros).forEach(function (k) {
      filtros[k].addEventListener('change', function () { elegidos[k] = filtros[k].value; if (motor) actualizar(); });
    });
    mas.addEventListener('click', mostrar);
  }

  // Pestañas de la materia en un curso. Sin JavaScript, los paneles se ven seguidos.
  function pestanas() {
    Array.prototype.forEach.call(document.querySelectorAll('.pestanas'), function (barra) {
      var tabs = Array.prototype.slice.call(barra.querySelectorAll('[role="tab"]'));
      document.documentElement.classList.add('js-pestanas');
      barra.hidden = false;
      function activar(t, enfocar, recordar) {
        tabs.forEach(function (x) {
          var sel = x === t;
          x.setAttribute('aria-selected', sel ? 'true' : 'false');
          x.tabIndex = sel ? 0 : -1;
          document.getElementById(x.getAttribute('aria-controls')).hidden = !sel;
        });
        if (enfocar) t.focus();
        if (recordar) history.replaceState(null, '', '#' + t.getAttribute('aria-controls'));
      }
      tabs.forEach(function (t, i) {
        t.addEventListener('click', function () { activar(t, false, true); });
        t.addEventListener('keydown', function (ev) {
          var d = ev.key === 'ArrowRight' ? 1 : ev.key === 'ArrowLeft' ? -1 : 0;
          if (ev.key === 'Home') d = -i;
          if (ev.key === 'End') d = tabs.length - 1 - i;
          if (!d) return;
          ev.preventDefault();
          activar(tabs[(i + d + tabs.length) % tabs.length], true, true);
        });
      });
      var inicial = tabs.filter(function (t) { return '#' + t.getAttribute('aria-controls') === location.hash; })[0];
      activar(inicial || tabs[0], false, false);
    });
  }

  Array.prototype.forEach.call(document.querySelectorAll('#q-cabecera, #q-portada'), sugerencias);
  resultados();
  pestanas();
})();
