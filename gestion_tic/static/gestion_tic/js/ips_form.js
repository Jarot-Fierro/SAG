/**
 * ============================================================================
 * Script de Formulario de Direcciones IP
 * ============================================================================
 * Este archivo inicializa los componentes del formulario de IPs, incluyendo
 * TomSelect en los elementos con clase .tom-select.
 */

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
});
