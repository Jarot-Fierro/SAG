/**
 * ============================================================================
 * Script de Modal de Confirmación y Desactivación de Activos
 * ============================================================================
 * Este archivo gestiona el flujo de confirmación y desactivación lógica de registros
 * de Activos mediante modal de SweetAlert2 y peticiones asíncronas AJAX con CSRF.
 */

document.addEventListener('DOMContentLoaded', function () {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        })[character]);
    }

    // Delegación de eventos para el botón de desactivación (.btn-desactivar)
    $('#myTable tbody').on('click', '.btn-desactivar', function (e) {
        e.preventDefault();

        const btn = $(this);
        const recordId = btn.data('id');
        const recordName = btn.data('name');
        const deleteUrl = btn.data('url');

        if (!deleteUrl || deleteUrl === '#') {
            Swal.fire({
                icon: 'error',
                title: 'Error de configuración',
                text: 'No se encontró la ruta para desactivar este registro.'
            });
            return;
        }

        Swal.fire({
            title: '¿Está seguro de desactivar?',
            html: `¿Desea desactivar el activo <strong>"${escapeHtml(recordName)}"</strong> (ID: <strong>${escapeHtml(recordId)}</strong>)?<br><span class="text-warning small mt-2 d-block">El activo quedará marcado como inactivo.</span>`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
            confirmButtonText: '<i class="bi bi-trash me-1"></i> Aceptar',
            cancelButtonText: '<i class="bi bi-x-circle me-1"></i> Cancelar',
            reverseButtons: true,
            focusCancel: true
        }).then((result) => {
            if (result.isConfirmed) {
                Swal.fire({
                    title: 'Desactivando activo...',
                    text: 'Por favor espere un momento.',
                    allowOutsideClick: false,
                    allowEscapeKey: false,
                    didOpen: () => {
                        Swal.showLoading();
                    }
                });

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
                            Swal.fire({
                                icon: 'success',
                                title: '¡Desactivado!',
                                text: response.message || 'El activo ha sido desactivado exitosamente.',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            const dataTable = $('#myTable').DataTable();
                            if (dataTable) {
                                dataTable.ajax.reload(null, false);
                            }
                        } else {
                            Swal.fire({
                                icon: 'error',
                                title: 'Error al desactivar',
                                text: response.message || 'No fue posible desactivar el registro seleccionado.'
                            });
                        }
                    },
                    error: function (xhr, status, error) {
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
