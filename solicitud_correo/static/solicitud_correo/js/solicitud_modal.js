/**
 * ============================================================================
 * Script de Modales y Confirmación de Acciones (solicitud_correo)
 * ============================================================================
 * Gestiona la confirmación mediante SweetAlert2 para cancelaciones y cambios de estado,
 * así como la recarga asíncrona de DataTables conservando la paginación.
 */

document.addEventListener('DOMContentLoaded', function () {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    // Manejo de cancelación de solicitudes con SweetAlert2
    document.addEventListener('click', function (e) {
        const btnCancel = e.target.closest('.btn-cancelar-solicitud');
        if (!btnCancel) return;

        e.preventDefault();
        const url = btnCancel.dataset.url || btnCancel.getAttribute('href');
        const folio = btnCancel.dataset.folio || '';

        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: '¿Confirmar Cancelación?',
                text: `¿Está seguro de que desea cancelar la solicitud ${folio}? Esta acción no se puede deshacer.`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Sí, cancelar solicitud',
                cancelButtonText: 'No, mantener'
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                        .then(response => {
                            if (response.ok) {
                                Swal.fire(
                                    'Cancelada',
                                    'La solicitud ha sido cancelada exitosamente.',
                                    'success'
                                ).then(() => {
                                    const tableEl = document.querySelector('#myTable');
                                    if (tableEl && typeof DataTable !== 'undefined') {
                                        const dt = DataTable.tables({api: true});
                                        if (dt) dt.ajax.reload(null, false);
                                        else window.location.reload();
                                    } else {
                                        window.location.reload();
                                    }
                                });
                            } else {
                                Swal.fire(
                                    'Error',
                                    'No se pudo cancelar la solicitud.',
                                    'error'
                                );
                            }
                        })
                        .catch(() => {
                            Swal.fire(
                                'Error de conexión',
                                'Ocurrió un error al intentar comunicarse con el servidor.',
                                'error'
                            );
                        });
                }
            });
        } else {
            if (confirm(`¿Está seguro de que desea cancelar la solicitud ${folio}?`)) {
                window.location.href = url;
            }
        }
    });
});
