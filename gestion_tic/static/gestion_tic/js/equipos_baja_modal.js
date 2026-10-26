/**
 * ============================================================================
 * Script de Acciones y Modales para Carrito de Baja Masiva
 * ============================================================================
 */

document.addEventListener('DOMContentLoaded', function () {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    const actionUrl = window.location.pathname;

    const cartCounterEl = document.getElementById('cart-counter');
    const btnVaciar = document.getElementById('btn-vaciar-carrito');
    const tbodyCarrito = document.getElementById('tbody-carrito');
    const cartFooter = document.getElementById('cart-footer');
    const btnProcesarBaja = document.getElementById('btn-procesar-baja');

    function updateCartUI(cartCount) {
        if (cartCounterEl) {
            cartCounterEl.textContent = cartCount;
        }
        if (cartCount > 0) {
            btnVaciar?.classList.remove('d-none');
            cartFooter?.classList.remove('d-none');
            const emptyRow = document.getElementById('cart-empty-row');
            if (emptyRow) emptyRow.remove();
        } else {
            btnVaciar?.classList.add('d-none');
            cartFooter?.classList.add('d-none');
            if (tbodyCarrito) {
                tbodyCarrito.innerHTML = `
                    <tr id="cart-empty-row">
                        <td colspan="3" class="text-center py-4 text-muted">
                            No hay equipos seleccionados en el carrito.
                        </td>
                    </tr>
                `;
            }
        }
    }

    // Agregar al carrito
    document.addEventListener('click', function (e) {
        const btnAdd = e.target.closest('.btn-add-cart');
        if (!btnAdd) return;

        const activoId = btnAdd.dataset.id;
        if (!activoId) return;

        const formData = new FormData();
        formData.append('action', 'add');
        formData.append('activo_id', activoId);
        formData.append('is_ajax', 'true');

        fetch(actionUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            toast: true,
                            position: 'top-end',
                            icon: 'success',
                            title: data.message || 'Equipo agregado al carrito',
                            showConfirmButton: false,
                            timer: 2000,
                            timerProgressBar: true
                        });
                    }
                    // Agregar fila a la tabla del carrito
                    if (data.item && tbodyCarrito) {
                        const emptyRow = document.getElementById('cart-empty-row');
                        if (emptyRow) emptyRow.remove();

                        const newRow = document.createElement('tr');
                        newRow.id = `cart-row-${data.item.id}`;
                        newRow.innerHTML = `
                        <td class="fw-bold">${data.item.codigo_barra}</td>
                        <td>${data.item.tipo_marca}</td>
                        <td class="text-center">
                            <button type="button" class="btn btn-outline-danger btn-sm btn-remove-cart" data-id="${data.item.id}" title="Quitar del carrito">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;
                        tbodyCarrito.appendChild(newRow);
                    }
                    updateCartUI(data.cart_count || 1);
                    if (dtEquiposBaja) {
                        dtEquiposBaja.ajax.reload(null, false);
                    }
                } else {
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'warning',
                            title: 'Aviso',
                            text: data.message || 'No se pudo agregar el equipo.',
                            confirmButtonText: 'Entendido'
                        });
                    }
                }
            })
            .catch(err => {
                console.error('Error al agregar al carrito:', err);
            });
    });

    // Quitar del carrito
    document.addEventListener('click', function (e) {
        const btnRemove = e.target.closest('.btn-remove-cart');
        if (!btnRemove) return;

        const activoId = btnRemove.dataset.id;
        if (!activoId) return;

        const formData = new FormData();
        formData.append('action', 'remove');
        formData.append('activo_id', activoId);
        formData.append('is_ajax', 'true');

        fetch(actionUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const row = document.getElementById(`cart-row-${activoId}`);
                    if (row) row.remove();

                    updateCartUI(data.cart_count || 0);

                    if (dtEquiposBaja) {
                        dtEquiposBaja.ajax.reload(null, false);
                    }
                }
            })
            .catch(err => {
                console.error('Error al quitar del carrito:', err);
            });
    });

    // Vaciar carrito
    if (btnVaciar) {
        btnVaciar.addEventListener('click', function () {
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: '¿Vaciar carrito?',
                    text: 'Se quitarán todos los equipos seleccionados del carrito de baja.',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#d33',
                    cancelButtonColor: '#6c757d',
                    confirmButtonText: '<i class="bi bi-trash3 me-1"></i>Sí, vaciar',
                    cancelButtonText: 'Cancelar'
                }).then(result => {
                    if (result.isConfirmed) {
                        ejecutarVaciar();
                    }
                });
            } else if (confirm('¿Vaciar el carrito?')) {
                ejecutarVaciar();
            }
        });
    }

    function ejecutarVaciar() {
        const formData = new FormData();
        formData.append('action', 'clear');
        formData.append('is_ajax', 'true');

        fetch(actionUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateCartUI(0);
                    if (dtEquiposBaja) {
                        dtEquiposBaja.ajax.reload(null, false);
                    }
                }
            });
    }

    // Procesar baja masiva
    if (btnProcesarBaja) {
        btnProcesarBaja.addEventListener('click', function () {
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: '¿Procesar Baja Masiva?',
                    text: 'Esta acción dará de baja todos los equipos que se encuentran en el carrito.',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#dc3545',
                    cancelButtonColor: '#6c757d',
                    confirmButtonText: '<i class="bi bi-arrow-down-circle me-1"></i>Sí, procesar baja',
                    cancelButtonText: 'Cancelar'
                }).then(result => {
                    if (result.isConfirmed) {
                        ejecutarProcesarBaja();
                    }
                });
            } else if (confirm('¿Estás seguro de dar de baja masivamente estos equipos?')) {
                ejecutarProcesarBaja();
            }
        });
    }

    function ejecutarProcesarBaja() {
        const formData = new FormData();
        formData.append('action', 'procesar');
        formData.append('is_ajax', 'true');

        fetch(actionUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'success',
                            title: 'Éxito',
                            text: data.message || 'Se han dado de baja los equipos correctamente.',
                            confirmButtonText: 'Aceptar'
                        }).then(() => {
                            window.location.href = data.redirect_url || '/gestion_tic/activos/';
                        });
                    } else {
                        window.location.href = data.redirect_url || '/gestion_tic/activos/';
                    }
                } else {
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'error',
                            title: 'Error',
                            text: data.message || 'No se pudo procesar la baja.'
                        });
                    }
                }
            })
            .catch(err => {
                console.error('Error al procesar baja:', err);
            });
    }
});
