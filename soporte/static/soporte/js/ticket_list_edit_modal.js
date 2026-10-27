/**
 * ============================================================================
 * Script de Modal de Confirmación y Eliminación de Tickets de Soporte
 * ============================================================================
 * Este archivo gestiona el flujo de confirmación y eliminación de registros
 * mediante modal de SweetAlert2 y peticiones asíncronas AJAX.
 */

document.addEventListener('DOMContentLoaded', function () {
    // ------------------------------------------------------------------------
    // 1. OBTENCIÓN DE CONFIGURACIÓN Y TOKENS
    // ------------------------------------------------------------------------

    // Token CSRF necesario para autenticar peticiones POST en Django
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    // ------------------------------------------------------------------------
    // 2. FUNCIONES AUXILIARES Y HELPERS
    // ------------------------------------------------------------------------

    /**
     * Escapa caracteres especiales en cadenas para prevenir vulnerabilidades XSS
     * al inyectar contenido dinámico dentro del modal HTML.
     * @param {string|any} value - Valor a sanitizar.
     * @returns {string} Cadena segura con entidades HTML escapadas.
     */
    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        })[character]);
    }

    // ------------------------------------------------------------------------
    // 3. CONTROLADOR DE EVENTO PARA ELIMINAR REGISTRO CON SWEETALERT2 Y AJAX
    // ------------------------------------------------------------------------

    /**
     * Delegación de eventos para el botón de eliminación (.btn-eliminar-ticket).
     * Muestra un modal de confirmación con SweetAlert2 mostrando el nombre y el ID
     * del ticket, indicando que la acción no es reversible. Al confirmar,
     * envía una petición asíncrona AJAX vía POST a la vista basada en función.
     */
    $('#myTable tbody').on('click', '.btn-cerrar-ticket', function (e) {
        e.preventDefault();
        const modalEl = document.getElementById('cerrarTicketModal');
        const form = document.getElementById('cerrarTicketForm');
        form.reset();
        form.action = this.dataset.url;
        bootstrap.Modal.getOrCreateInstance(modalEl).show();
    });

    $('#myTable tbody').on('click', '.btn-eliminar-ticket', function (e) {
        e.preventDefault();

        // Extraer los datos del ticket desde los atributos data-* del botón
        const btn = $(this);
        const recordId = btn.data('id');
        const recordName = btn.data('name');
        const deleteUrl = btn.data('url');

        if (!deleteUrl || deleteUrl === '#') {
            Swal.fire({
                icon: 'error',
                title: 'Error de configuración',
                text: 'No se encontró la ruta para eliminar este registro.'
            });
            return;
        }

        // Modal de confirmación SweetAlert2
        Swal.fire({
            title: '¿Está seguro de eliminar?',
            html: `¿Desea eliminar el ticket <strong>"${escapeHtml(recordName)}"</strong> (ID: <strong>${escapeHtml(recordId)}</strong>)?<br><span class="text-danger small mt-2 d-block">Esta acción no es reversible.</span>`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
            confirmButtonText: '<i class="bi bi-trash me-1"></i> Aceptar',
            cancelButtonText: '<i class="bi bi-x-circle me-1"></i> Cancelar',
            reverseButtons: true,
            focusCancel: true
        }).then((result) => {
            // Si el usuario presiona "Aceptar", se procede con la eliminación AJAX
            if (result.isConfirmed) {
                // Mostrar indicador de carga mientras se ejecuta la petición
                Swal.fire({
                    title: 'Eliminando registro...',
                    text: 'Por favor espere un momento.',
                    allowOutsideClick: false,
                    allowEscapeKey: false,
                    didOpen: () => {
                        Swal.showLoading();
                    }
                });

                // Petición AJAX POST a la vista basada en función de Django
                $.ajax({
                    url: deleteUrl,
                    type: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken
                    },
                    data: {
                        'id': recordId
                    },
                    dataType: 'json',
                    success: function (response) {
                        if (response.success || response.status === 'success') {
                            // Alerta de éxito con SweetAlert2
                            Swal.fire({
                                icon: 'success',
                                title: '¡Eliminado!',
                                text: response.message || 'El registro ha sido eliminado exitosamente.',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            // Recargar los datos del DataTable manteniendo la paginación actual
                            const dataTable = $('#myTable').DataTable();
                            if (dataTable) {
                                dataTable.ajax.reload(null, false);
                            }
                        } else {
                            // Alerta en caso de respuesta con error lógico
                            Swal.fire({
                                icon: 'error',
                                title: 'Error al eliminar',
                                text: response.message || 'No fue posible eliminar el ticket seleccionado.'
                            });
                        }
                    },
                    error: function (xhr, status, error) {
                        // Manejo de errores de red o excepciones HTTP
                        let errorMsg = 'Ocurrió un error al procesar la solicitud.';
                        if (xhr.responseJSON && xhr.responseJSON.message) {
                            errorMsg = xhr.responseJSON.message;
                        }
                        Swal.fire({
                            icon: 'error',
                            title: 'Error del servidor',
                            text: errorMsg
                        });
                    }
                });
            }
        });
    });
});
