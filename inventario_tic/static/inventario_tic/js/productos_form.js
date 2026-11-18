document.addEventListener('DOMContentLoaded', function () {
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

    const marcaSelect = document.getElementById('marca_producto');
    const modeloSelect = document.getElementById('modelo_producto');
    const modelosData = document.getElementById('productos-modelos');
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
