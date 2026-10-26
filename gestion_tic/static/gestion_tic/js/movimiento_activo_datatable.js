/**
 * ============================================================================
 * Script de DataTables Server-Side para Listado de Movimientos / Activos
 * ============================================================================
 */

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
            width: "60px"
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
            data: "contrato",
            title: "Contrato",
            render: function (data) {
                return escapeHtml(data || '-');
            }
        },
        {
            data: null,
            title: "Acciones",
            defaultContent: "",
            orderable: false,
            searchable: false,
            className: "text-center",
            width: "120px",
            render: function (data, type, row) {
                const rowCodigo = (row && row.codigo_barra) || (data && data.codigo_barra) || '';
                const editUrl = (row && row.edit_url) || (data && data.edit_url) || '#';
                const consultUrl = (row && row.consultar_url) || (data && data.consultar_url) || `?q=${encodeURIComponent(rowCodigo)}`;

                return `
                    <div class="btn-group btn-group-sm" role="group">
                        <a href="${consultUrl}" class="btn btn-outline-info" title="Consultar / Registrar Movimientos">
                            <i class="bi bi-arrow-left-right"></i>
                        </a>
                        <a href="${editUrl}" class="btn btn-outline-primary" title="Editar Activo">
                            <i class="bi bi-pencil"></i>
                        </a>
                    </div>
                `;
            }
        }
    ];

    const filterForm = document.getElementById('filter-form');

    const dt = new DataTable('#myTable', {
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
            dt.ajax.reload();
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
                dt.ajax.reload();
            });
        }
    }
});
