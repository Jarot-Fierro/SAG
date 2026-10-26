/**
 * ============================================================================
 * Script de DataTables Server-Side para Equipos Disponibles para Baja
 * ============================================================================
 */

let dtEquiposBaja = null;

document.addEventListener('DOMContentLoaded', function () {
    const tableEl = document.querySelector('#myTable');
    if (!tableEl) return;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    const ajaxUrl = tableEl.dataset.ajaxUrl || window.location.pathname;

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        })[character]);
    }

    const columns = [
        {
            data: "id",
            title: "ID",
            className: "text-center",
            width: "50px"
        },
        {
            data: "codigo_barra",
            title: "Código",
            render: function (data) {
                return `<strong>${escapeHtml(data || '')}</strong>`;
            }
        },
        {
            data: "tipo",
            title: "Tipo",
            render: function (data) {
                return escapeHtml(data || '-');
            }
        },
        {
            data: "marca_modelo",
            title: "Marca / Modelo",
            render: function (data) {
                return escapeHtml(data || '-');
            }
        },
        {
            data: "serie",
            title: "Serie",
            render: function (data) {
                return escapeHtml(data || '-');
            }
        },
        {
            data: null,
            title: "Acción",
            defaultContent: "",
            orderable: false,
            searchable: false,
            className: "text-center",
            width: "70px",
            render: function (data, type, row) {
                const rowId = (row && row.id) || (data && data.id) || '';
                return `
                    <button type="button" class="btn btn-success btn-sm btn-add-cart" data-id="${rowId}" title="Agregar al carrito">
                        <i class="bi bi-plus-circle"></i>
                    </button>
                `;
            }
        }
    ];

    const filterForm = document.getElementById('filter-form');

    dtEquiposBaja = new DataTable('#myTable', {
        serverSide: true,
        processing: true,
        responsive: true,
        ajax: {
            url: ajaxUrl,
            type: "POST",
            headers: {
                'X-CSRFToken': csrfToken
            },
            data: function (d) {
                d.action = 'search';
                if (filterForm) {
                    const formData = new FormData(filterForm);
                    for (const [key, val] of formData.entries()) {
                        if (val) {
                            d[key] = val;
                        }
                    }
                }
            },
            error: function (xhr, error, thrown) {
                console.error("Error al cargar datos en DataTable:", error, thrown);
            }
        },
        columns: columns,
        order: [[1, 'asc']],
        pageLength: 10,
        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.3.6/i18n/es-ES.json',
            paginate: {
                first: '<i class="bi bi-chevron-double-left"></i>',
                previous: '<i class="bi bi-chevron-left"></i>',
                next: '<i class="bi bi-chevron-right"></i>',
                last: '<i class="bi bi-chevron-double-right"></i>'
            }
        }
    });

    if (filterForm) {
        filterForm.addEventListener('submit', function (e) {
            e.preventDefault();
            dtEquiposBaja.ajax.reload();
        });

        const btnLimpiar = document.getElementById('btn-limpiar-filtros');
        if (btnLimpiar) {
            btnLimpiar.addEventListener('click', function () {
                filterForm.reset();
                const selects = filterForm.querySelectorAll('select');
                selects.forEach(sel => {
                    if (sel.tomselect) {
                        sel.tomselect.clear();
                    } else {
                        sel.value = '';
                    }
                });
                dtEquiposBaja.ajax.reload();
            });
        }
    }
});
