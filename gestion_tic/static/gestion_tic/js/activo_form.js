/**
 * ============================================================================
 * Script de Formulario de Activos
 * ============================================================================
 * Este archivo inicializa los componentes del formulario, incluyendo TomSelect /
 * Select2 en los selectores correspondientes y prevención de submit involuntario
 * al escanear códigos de barras.
 */

document.addEventListener('DOMContentLoaded', function () {
    /**
     * ============================================================================
     * Script de Formulario de Tickets de Soporte
     * ============================================================================
     * Inicializa los componentes interactivos del formulario, como TomSelect en los
     * campos con clase .tom-select.
     */
    document.querySelectorAll('select.tom-select').forEach((el) => {
        if (el.tomselect || typeof TomSelect === 'undefined') return;
        new TomSelect(el, {
            render: {
                no_results: function () {
                    return '<div class="no-results">No se encontraron resultados</div>';
                }
            }
        });
    });

    // Evitar que lectores de códigos de barras envíen el formulario al presionar Enter en inputs
    const formActivo = document.querySelector('#form-activo');
    if (formActivo) {
        formActivo.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && e.target.tagName.toLowerCase() === 'input' && e.target.type !== 'submit') {
                e.preventDefault();
                return false;
            }
        });
    }
});
