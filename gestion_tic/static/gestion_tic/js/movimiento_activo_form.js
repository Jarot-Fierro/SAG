/**
 * ============================================================================
 * Script de Formularios de Movimiento de Activos (Tom Select)
 * ============================================================================
 */

document.addEventListener('DOMContentLoaded', function () {
    // Inicializar Tom Select en todos los selects con clase .tom-select o .select2
    const selectElements = document.querySelectorAll('select.tom-select, select.select2');
    selectElements.forEach(selectEl => {
        if (selectEl && !selectEl.tomselect) {
            try {
                if (typeof TomSelect !== 'undefined') {
                    new TomSelect(selectEl, {
                        create: false,
                        allowEmptyOption: true,
                        maxItems: 1,
                        placeholder: selectEl.getAttribute('placeholder') || 'Seleccione una opción...',
                        render: {
                            no_results: function (data, escape) {
                                return '<div class="no-results">No se encontraron resultados</div>';
                            }
                        }
                    });
                }
            } catch (err) {
                console.warn('No se pudo inicializar TomSelect en', selectEl, err);
            }
        }
    });

    // Enfoque automático al buscador de escáner
    const inputQ = document.getElementById('q');
    if (inputQ && !inputQ.value) {
        inputQ.focus();
    }
});
