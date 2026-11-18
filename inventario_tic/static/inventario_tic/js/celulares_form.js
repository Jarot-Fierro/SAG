document.addEventListener('DOMContentLoaded', function () {
    const telefonoInput = document.getElementById('id_numero_telefonico');

    // Formatear Teléfono: +569XXXXXXXX
    function formatTelefono(value) {
        let nums = value.replace(/\D/g, '');
        if (nums.startsWith('569')) {
            nums = nums.slice(3);
        } else if (nums.startsWith('9')) {
            nums = nums.slice(1);
        }

        // Solo tomar los últimos 8 dígitos si hay más
        if (nums.length > 8) {
            nums = nums.slice(-8);
        }

        return nums ? '+569' + nums : '';
    }

    if (telefonoInput) {
        telefonoInput.value = formatTelefono(telefonoInput.value);

    telefonoInput.addEventListener('input', function () {
        this.value = formatTelefono(this.value);
    });

    telefonoInput.addEventListener('blur', function () {
        this.value = formatTelefono(this.value);
    });
    }

    if (typeof TomSelect !== 'undefined') {
        document.querySelectorAll('.tom-select').forEach((el) => {
            if (!el.tomselect) {
                new TomSelect(el, {
                    render: {
                        no_results: function () {
                            return '<div class="no-results">No se encontraron resultados</div>';
                        }
                    }
                });
            }
        });
    }

    const marcaSelect = document.getElementById('marca_celular');
    const modeloSelect = document.getElementById('modelo_celular');
    const modelosData = document.getElementById('celulares-modelos');
    if (!marcaSelect || !modeloSelect || !modelosData) return;

    const modelos = JSON.parse(modelosData.textContent);

    function actualizarModelos(conservarSeleccion = false) {
        const marcaId = marcaSelect.value;
        const seleccion = conservarSeleccion ? modeloSelect.value : '';
        const disponibles = modelos.filter(modelo => String(modelo.marca_id) === marcaId);
        const placeholder = !marcaId
            ? 'Seleccione primero una marca'
            : disponibles.length ? 'Seleccione un modelo' : 'Sin modelos para esta marca';
        const seleccionValida = disponibles.some(modelo => String(modelo.id) === seleccion);

        if (modeloSelect.tomselect) {
            const control = modeloSelect.tomselect;
            control.clear(true);
            control.clearOptions();
            control.addOptions(disponibles.map(modelo => ({
                value: String(modelo.id), text: modelo.nombre
            })));
            control.settings.placeholder = placeholder;
            control.inputState();
            if (marcaId) control.enable();
            else control.disable();
            if (seleccionValida) control.setValue(seleccion, true);
            control.refreshOptions(false);
        } else {
            modeloSelect.replaceChildren(new Option(placeholder, ''));
            disponibles.forEach(modelo => {
                modeloSelect.add(new Option(modelo.nombre, String(modelo.id)));
            });
            modeloSelect.disabled = !marcaId;
            modeloSelect.value = seleccionValida ? seleccion : '';
        }
    }

    marcaSelect.addEventListener('change', () => actualizarModelos());
    actualizarModelos(true);
});
