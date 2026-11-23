document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('estacion-form');
    if (!form) return;
    const modelos = JSON.parse(document.getElementById('estacion-modelos').textContent);
    const isNew = row => row.querySelector('[name$="-nuevo"]').value.toLowerCase() === 'true';
    const visibleRows = section => [...section.querySelectorAll('.filas > .estacion-fila')].filter(r => !r.hidden);
    const showTab = id => bootstrap.Tab.getOrCreateInstance(form.querySelector(`[data-bs-target="#tab-${id}"]`)).show();
    const initSelect = el => el.tomselect || new TomSelect(el, {create: false});

    function syncDuplicates(section) {
        const rows = visibleRows(section);
        const values = rows.map(r => r.querySelector('.estacion-busqueda').value).filter(Boolean);
        rows.forEach(row => {
            const el = row.querySelector('.estacion-busqueda');
            const ts = el.tomselect;
            if (!ts) return;
            Object.values(ts.options).forEach(option => {
                option.disabled = option.value !== el.value && values.includes(String(option.value));
            });
            ts.clearCache();
            ts.refreshOptions(false);
        });
    }

    function initRow(row, section) {
        const select = row.querySelector('.estacion-busqueda');
        const modal = row.querySelector('.registro-modal');
        const flag = row.querySelector('[name$="-nuevo"]');
        const errors = row.querySelector('.fila-errors');
        const nuevoResumen = row.querySelector('.nuevo-resumen');
        const tipo = section.dataset.tipo;
        const ts = new TomSelect(select, {
            create: false, loadThrottle: 300, preload: 'focus',
            render: {no_results: () => '<div class="no-results p-2">Sin resultados. Puede usar «Registrar nuevo».</div>'},
            load: function(query, callback) {
                const url = new URL(form.dataset.buscar, window.location.origin);
                url.searchParams.set('tipo', tipo);
                url.searchParams.set('q', query);
                fetch(url, {headers: {'Accept': 'application/json'}})
                    .then(r => {if (!r.ok) throw new Error('No se pudo buscar.'); return r.json();})
                    .then(data => {
                        const usados = visibleRows(section).filter(r => r !== row).map(r => r.querySelector('.estacion-busqueda').value);
                        callback(data.results.map(o => ({...o, disabled: usados.includes(o.value)})));
                    }).catch(() => {errors.textContent = 'No se pudo buscar. Revise la conexión e intente nuevamente.'; callback();});
            },
            onChange: () => syncDuplicates(section),
        });
        const marca = modal.querySelector('[name$="-marca"]');
        const modelo = modal.querySelector('[name$="-modelo"]');
        function updateModels(keep) {
            const selected = keep ? modelo.value : '';
            modelo.replaceChildren(new Option('Seleccione un modelo', ''));
            modelos.filter(m => String(m.marca_id) === marca.value).forEach(m => modelo.add(new Option(m.nombre, String(m.id))));
            modelo.value = selected;
            modelo.disabled = !marca.value;
        }
        if (marca && modelo) {
            updateModels(true);
            marca.addEventListener('change', () => updateModels(false));
        }
        // Los selects del modal son nativos para conservar la validación y la dependencia marca/modelo.
        function syncNew() {
            if (isNew(row)) {
                const label = modal.querySelector('[name$="-nombre"], [name$="-numero_serie"]');
                nuevoResumen.textContent = `Nuevo pendiente de guardar: ${label?.value || ''}`;
            } else {
                nuevoResumen.textContent = '';
            }
            if (section.disabled || isNew(row)) ts.disable();
            else ts.enable();
        }
        row.querySelector('.abrir-registro').addEventListener('click', () => {
            bootstrap.Modal.getOrCreateInstance(modal).show();
        });
        row.querySelector('.preparar-registro').addEventListener('click', () => {
            const invalid = [...modal.querySelectorAll('input, select, textarea')].find(el => !el.checkValidity());
            if (invalid) {invalid.reportValidity(); return;}
            flag.value = 'True';
            ts.clear(true);
            syncNew();
            syncDuplicates(section);
            bootstrap.Modal.getOrCreateInstance(modal).hide();
        });
        row.querySelector('.usar-existente').addEventListener('click', () => {flag.value = 'False'; syncNew();});
        row.querySelector('.quitar-fila').addEventListener('click', () => {
            row.querySelector('[name$="-DELETE"]').checked = true;
            row.hidden = true;
            syncDuplicates(section);
            updateAdd(section);
        });
        syncNew();
        if (row.querySelector('[name$="-DELETE"]').checked) row.hidden = true;
        // Mostrar el modal que contiene errores devueltos por Django.
        if (isNew(row) && modal.querySelector('.errorlist') && section.closest('.tab-pane').classList.contains('active')) {
            bootstrap.Modal.getOrCreateInstance(modal).show();
        }
    }

    function updateAdd(section) {
        section.querySelector('.agregar-fila').disabled = visibleRows(section).length >= Number(section.dataset.max);
    }

    form.querySelectorAll('fieldset.seccion').forEach(section => {
        const checkbox = section.closest('.tab-pane').querySelector('.incluir-seccion');
        checkbox.addEventListener('change', () => {
            section.disabled = !checkbox.checked;
            visibleRows(section).forEach(row => {
                const ts = row.querySelector('.estacion-busqueda').tomselect;
                if (section.disabled || isNew(row)) ts.disable();
                else ts.enable();
            });
        });
        section.querySelectorAll('.filas > .estacion-fila').forEach(row => initRow(row, section));
        updateAdd(section);
        section.querySelector('.agregar-fila').addEventListener('click', () => {
            // Reutilizar filas eliminadas evita exceder TOTAL_FORMS al quitar y agregar.
            let row = [...section.querySelectorAll('.filas > .estacion-fila')].find(r => r.hidden);
            if (row) {
                row.hidden = false;
                row.querySelector('[name$="-DELETE"]').checked = false;
                row.querySelector('.estacion-busqueda').tomselect.clear();
            } else {
                const total = section.querySelector('[name$="-TOTAL_FORMS"]');
                const html = section.querySelector('template').innerHTML.replaceAll('__prefix__', total.value);
                const holder = document.createElement('div');
                holder.innerHTML = html;
                row = holder.firstElementChild;
                section.querySelector('.filas').append(row);
                total.value = Number(total.value) + 1;
                initRow(row, section);
            }
            updateAdd(section);
            syncDuplicates(section);
        });
    });
    document.querySelectorAll('#tab-destino select').forEach(initSelect);
    const responsable = document.querySelector('[name="destino-responsable"]');
    const funcionario = document.getElementById('funcionarioModalForm');
    let savingFuncionario = false;
    funcionario.addEventListener('submit', async event => {
        event.preventDefault();
        if (savingFuncionario) return;
        savingFuncionario = true;
        const submit = funcionario.querySelector('[type="submit"]');
        const errors = document.getElementById('funcionarioModalErrors');
        submit.disabled = true;
        try {
            const response = await fetch(funcionario.action, {method: 'POST', body: new FormData(funcionario), headers: {'Accept': 'application/json'}});
            const data = await response.json();
            if (!response.ok) throw new Error(Object.values(data.errors || {}).flat().join(' ') || 'No se pudo crear el funcionario.');
            responsable.tomselect.addOption({value: String(data.id), text: data.nombre});
            responsable.tomselect.setValue(String(data.id));
            bootstrap.Modal.getOrCreateInstance(document.getElementById('funcionarioModal')).hide();
            funcionario.reset();
            errors.classList.add('d-none');
        } catch (error) {
            errors.textContent = error.message;
            errors.classList.remove('d-none');
        } finally {savingFuncionario = false; submit.disabled = false;}
    });

    document.getElementById('revisar-entrega').addEventListener('click', () => {
        const resumen = document.getElementById('revision-contenido');
        resumen.replaceChildren();
        let count = 0;
        function line(text) {const p = document.createElement('p'); p.textContent = text; resumen.append(p);}
        form.querySelectorAll('fieldset.seccion').forEach(section => {
            if (section.disabled) return;
            visibleRows(section).forEach(row => {
                const select = row.querySelector('.estacion-busqueda');
                const description = isNew(row) ? row.querySelector('.nuevo-resumen').textContent : select.selectedOptions[0]?.textContent;
                if (!isNew(row) && !select.value) return;
                count++;
                line(`${section.dataset.tipo}: ${description} × ${row.querySelector('[name$="-cantidad"]')?.value || 1}`);
            });
        });
        if (!count) {showTab('computador'); line('Debe incluir al menos un elemento.');}
        document.querySelectorAll('#tab-destino select').forEach(s => line(`${s.previousElementSibling?.textContent || s.name}: ${s.selectedOptions[0]?.textContent || 'Sin seleccionar'}`));
        bootstrap.Modal.getOrCreateInstance(document.getElementById('revisionModal')).show();
    });
    form.addEventListener('submit', () => {
        form.querySelector('[type="submit"]').disabled = true;
        // Un equipo existente no envía los campos del registro nuevo.
        form.querySelectorAll('.filas > .estacion-fila').forEach(row => {
            if (!isNew(row) || row.hidden) row.querySelectorAll('.registro-modal input, .registro-modal select, .registro-modal textarea').forEach(el => {el.disabled = true;});
        });
    });
});
