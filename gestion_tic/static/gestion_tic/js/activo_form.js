/**
 * ============================================================================
 * Script de Formulario de Activos
 * ============================================================================
 * Este archivo inicializa los componentes del formulario, incluyendo TomSelect /
 * Select2 en los selectores correspondientes y prevención de submit involuntario
 * al escanear códigos de barras.
 */

document.addEventListener('DOMContentLoaded', function () {
    // Inicializar TomSelect si está disponible
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

    // Inicializar Select2 si está disponible y TomSelect no está presente
    if (typeof $ !== 'undefined' && $.fn && $.fn.select2) {
        $('.select2').each(function () {
            if (!this.tomselect) {
                $(this).select2({
                    theme: 'bootstrap-5',
                    width: '100%'
                });
            }
        });
    }

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
