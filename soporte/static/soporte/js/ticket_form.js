/**
 * ============================================================================
 * Script de Formulario de Tickets de Soporte
 * ============================================================================
 * Inicializa los componentes interactivos del formulario, como TomSelect en los
 * campos con clase .tom-select.
 */

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.tom-select').forEach((el) => {
        new TomSelect(el, {
            render: {
                no_results: function () {
                    return '<div class="no-results">No se encontraron resultados</div>';
                }
            }
        });
    });
});
