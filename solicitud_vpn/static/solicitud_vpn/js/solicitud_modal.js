/**
 * Gestión interactiva y de modales para solicitudes VPN
 */
$(document).ready(function () {
    // Manejo de confirmaciones SweetAlert2 si está disponible
    $(document).on('click', '.btn-confirm-action', function (e) {
        e.preventDefault();
        const $btn = $(this);
        const form = $btn.closest('form');
        const title = $btn.data('title') || '¿Está seguro?';
        const text = $btn.data('text') || 'Esta acción modificará la solicitud.';

        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: title,
                text: text,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Sí, continuar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    form.submit();
                }
            });
        } else {
            if (confirm(text)) {
                form.submit();
            }
        }
    });
});
