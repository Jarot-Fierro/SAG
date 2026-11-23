document.addEventListener('DOMContentLoaded', () => {
    const root = document.getElementById('inventario-dashboard');
    if (!root) return;
    const filtros = document.getElementById('dashboard-filtros');
    const graficos = new Map();
    const pendientes = new Map();
    let version = 0;
    const widgets = {
        inventario: ['computadores', 'monitores', 'celulares', 'asignados', 'funcionarios'],
        stock: ['stock_bajo', 'agotados'], actividad: ['entregas_mes']
    };

    function estado(bloque, texto, retry) {
        root.querySelectorAll(`[data-bloque="${bloque}"] .dashboard-estado`).forEach(el => {
            el.replaceChildren(document.createTextNode(texto));
            if (retry) {
                const button = document.createElement('button');
                button.type = 'button'; button.className = 'btn btn-sm btn-outline-primary ms-2';
                button.textContent = 'Reintentar'; button.onclick = () => cargar(bloque, version);
                el.append(button);
            }
        });
    }

    async function grafico(clave, categorias, series, horizontal = false, stacked = false) {
        if (typeof ApexCharts === 'undefined') throw new Error('No se pudo cargar la biblioteca de gráficos. Recargue la página.');
        const options = {
            chart: {type: 'bar', height: 300, stacked, toolbar: {show: false}, animations: {enabled: false}},
            series, colors: ['#0d6efd', '#20c997'],
            plotOptions: {bar: {horizontal, borderRadius: 3}},
            dataLabels: {enabled: false},
            xaxis: {categories: categorias},
            yaxis: {decimalsInFloat: 0},
            noData: {text: 'Sin datos para los filtros seleccionados'},
            legend: {position: 'top'},
            tooltip: {shared: true, intersect: false}
        };
        if (graficos.has(clave)) return graficos.get(clave).updateOptions(options);
        const chart = new ApexCharts(document.getElementById(`grafico-${clave}`), options);
        graficos.set(clave, chart);
        return chart.render();
    }

    function tabla(id, filas, campos) {
        const tbody = document.getElementById(id);
        tbody.replaceChildren();
        if (!filas.length) {
            const cell = document.createElement('td'); cell.colSpan = campos.length;
            cell.textContent = 'Sin registros para los filtros seleccionados.';
            const row = document.createElement('tr'); row.append(cell); tbody.append(row); return;
        }
        filas.forEach(fila => {
            const row = document.createElement('tr');
            campos.forEach(campo => {const cell = document.createElement('td'); cell.textContent = fila[campo] ?? ''; row.append(cell);});
            tbody.append(row);
        });
    }

    async function pintar(bloque, data) {
        Object.entries(data.widgets).forEach(([clave, valor]) => {
            root.querySelector(`[data-widget="${clave}"]`).textContent = Number(valor).toLocaleString('es-CL');
        });
        if (bloque === 'inventario') {
            document.getElementById('dashboard-porcentaje').textContent = `${data.porcentaje}% del inventario activo total`;
            await Promise.all([
                grafico('equipos', data.equipos.map(o => o.tipo), [
                    {name: 'Asignados (destino seleccionado)', data: data.equipos.map(o => o.asignados)},
                    {name: 'Disponibles (todos los destinos)', data: data.equipos.map(o => o.disponibles)}
                ], false, true),
                grafico('distribucion', data.distribucion.map(o => o.nombre), [{name: 'Equipos', data: data.distribucion.map(o => o.cantidad)}], true)
            ]);
        } else if (bloque === 'stock') {
            tabla('dashboard-alertas', data.alertas, ['nombre', 'stock_disponible', 'stock_minimo']);
            await grafico('reposicion', data.reposicion.map(o => o.nombre), [
                {name: 'Disponible', data: data.reposicion.map(o => o.stock_disponible)},
                {name: 'Mínimo', data: data.reposicion.map(o => o.stock_minimo)}
            ], true);
        } else {
            tabla('dashboard-ultimas', data.ultimas, ['folio', 'fecha', 'responsable', 'destino', 'cantidad']);
            await Promise.all([
                grafico('evolucion', data.evolucion.map(o => o.mes), [{name: 'Entregas', data: data.evolucion.map(o => o.cantidad)}]),
                grafico('productos', data.productos.map(o => o.producto__nombre), [{name: 'Unidades entregadas', data: data.productos.map(o => o.cantidad)}], true)
            ]);
        }
    }

    async function cargar(bloque, actual) {
        pendientes.get(bloque)?.abort();
        const controller = new AbortController(); pendientes.set(bloque, controller);
        estado(bloque, 'Cargando datos…', false);
        widgets[bloque].forEach(clave => {root.querySelector(`[data-widget="${clave}"]`).textContent = '…';});
        root.querySelectorAll(`[data-bloque="${bloque}"]`).forEach(el => {el.setAttribute('aria-busy', 'true');});
        try {
            const params = new URLSearchParams(new FormData(filtros)); params.set('bloque', bloque);
            const response = await fetch(`${root.dataset.url}?${params}`, {signal: controller.signal, headers: {'Accept': 'application/json'}});
            if (!(response.headers.get('content-type') || '').includes('application/json')) throw new Error('La sesión expiró o el servidor no está disponible.');
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'No se pudieron cargar los datos.');
            if (actual !== version || controller.signal.aborted) return;
            await pintar(bloque, data);
            if (actual !== version || controller.signal.aborted) return;
            estado(bloque, '', false);
            document.getElementById('dashboard-actualizado').textContent = `Último bloque actualizado: ${new Date(data.actualizado).toLocaleString('es-CL')}`;
        } catch (error) {
            if (error.name === 'AbortError' || actual !== version || controller.signal.aborted) return;
            estado(bloque, error.message, true);
            widgets[bloque].forEach(clave => {root.querySelector(`[data-widget="${clave}"]`).textContent = '—';});
        } finally {
            if (actual === version && !controller.signal.aborted) root.querySelectorAll(`[data-bloque="${bloque}"]`).forEach(el => {el.removeAttribute('aria-busy');});
        }
    }

    function actualizar() {
        const error = document.getElementById('dashboard-error');
        if (!filtros.reportValidity()) return;
        if (filtros.elements.desde.value > filtros.elements.hasta.value) {error.textContent = 'La fecha inicial debe ser anterior o igual a la final.'; return;}
        error.textContent = '';
        version++;
        document.getElementById('dashboard-actualizado').textContent = 'Actualizando…';
        ['inventario', 'stock', 'actividad'].forEach(bloque => cargar(bloque, version));
    }
    filtros.addEventListener('submit', event => {event.preventDefault(); actualizar();});
    filtros.addEventListener('change', actualizar);
    filtros.addEventListener('reset', () => setTimeout(actualizar, 0));
    actualizar();
});
