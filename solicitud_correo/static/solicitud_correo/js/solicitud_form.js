/**
 * ============================================================================
 * Script del Formulario de Creación de Solicitud de Correo (solicitud_correo)
 * ============================================================================
 * Gestiona la adición y eliminación dinámica de filas de funcionarios,
 * la selección automática mediante funcionario existente y la inicialización de select2.
 */

document.addEventListener('DOMContentLoaded', function () {
    const contenedor = document.getElementById('contenedor-filas-funcionarios');
    const btnAgregar = document.getElementById('btn-agregar-funcionario');
    const btnAgregarPie = document.getElementById('btn-agregar-funcionario-pie');
    const contador = document.getElementById('contador-funcionarios');

    function inicializarSelect2(elemento) {
        if (typeof $ !== 'undefined' && $.fn.select2) {
            $(elemento).find('.select2').each(function () {
                $(this).select2({
                    theme: 'bootstrap-5',
                    width: '100%',
                    placeholder: '-- Ingreso Manual / Seleccionar --',
                    allowClear: true
                });
            });
        }
    }

    function actualizarNumeracionYBotones() {
        if (!contenedor) return;
        const filas = contenedor.querySelectorAll('.fila-funcionario');
        filas.forEach((fila, idx) => {
            const numCell = fila.querySelector('.numero-fila');
            if (numCell) numCell.textContent = (idx + 1);
            const btnEliminar = fila.querySelector('.btn-eliminar-fila');
            if (btnEliminar) {
                btnEliminar.disabled = (filas.length === 1);
            }
        });
        if (contador) {
            contador.textContent = `Total: ${filas.length} funcionario${filas.length !== 1 ? 's' : ''}`;
        }
    }

    function vincularEventosFila(fila) {
        const select = fila.querySelector('.select-funcionario-existente');
        const inputRut = fila.querySelector('.input-rut');
        const inputNom = fila.querySelector('.input-nombres');
        const inputApe = fila.querySelector('.input-apellidos');
        const inputDep = fila.querySelector('.input-depto');
        const inputCar = fila.querySelector('.input-cargo');
        const btnEliminar = fila.querySelector('.btn-eliminar-fila');

        if (select) {
            function alCambiarFuncionario() {
                const opt = select.options[select.selectedIndex];
                if (opt && opt.value) {
                    if (inputRut) inputRut.value = opt.dataset.rut || '';
                    if (inputNom) inputNom.value = opt.dataset.nombres || '';
                    if (inputApe) inputApe.value = opt.dataset.apellidos || '';
                    if (inputCar) inputCar.value = opt.dataset.cargo || '';
                    if (inputDep) inputDep.value = opt.dataset.depto || '';
                } else {
                    if (inputRut) inputRut.value = '';
                    if (inputNom) inputNom.value = '';
                    if (inputApe) inputApe.value = '';
                    if (inputCar) inputCar.value = '';
                    if (inputDep) inputDep.value = '';
                }
            }

            select.addEventListener('change', alCambiarFuncionario);
            if (typeof $ !== 'undefined') {
                $(select).on('change select2:select select2:clear', alCambiarFuncionario);
            }
        }

        if (btnEliminar) {
            btnEliminar.addEventListener('click', function () {
                const filas = contenedor.querySelectorAll('.fila-funcionario');
                if (filas.length > 1) {
                    if (typeof $ !== 'undefined' && select && $(select).data('select2')) {
                        $(select).select2('destroy');
                    }
                    fila.remove();
                    actualizarNumeracionYBotones();
                }
            });
        }
    }

    function agregarFila() {
        if (!contenedor) return;
        const filas = contenedor.querySelectorAll('.fila-funcionario');
        if (filas.length === 0) return;
        const primeraFila = filas[0];
        const nuevaFila = primeraFila.cloneNode(true);

        // Remover contenedor residual de Select2 si existe
        nuevaFila.querySelectorAll('.select2-container').forEach(el => el.remove());

        // Limpiar inputs en la nueva fila
        nuevaFila.querySelectorAll('input').forEach(inp => inp.value = '');
        const select = nuevaFila.querySelector('select');
        if (select) {
            select.selectedIndex = 0;
            select.removeAttribute('data-select2-id');
            select.removeAttribute('tabindex');
            select.removeAttribute('aria-hidden');
            select.classList.remove('select2-hidden-accessible');
            select.querySelectorAll('option').forEach(opt => opt.removeAttribute('data-select2-id'));
        }

        contenedor.appendChild(nuevaFila);
        vincularEventosFila(nuevaFila);
        inicializarSelect2(nuevaFila);
        actualizarNumeracionYBotones();
    }

    if (contenedor) {
        // Inicializar fila existente
        contenedor.querySelectorAll('.fila-funcionario').forEach(f => {
            vincularEventosFila(f);
            inicializarSelect2(f);
        });

        if (btnAgregar) {
            btnAgregar.addEventListener('click', agregarFila);
        }
        if (btnAgregarPie) {
            btnAgregarPie.addEventListener('click', agregarFila);
        }
    }
});
