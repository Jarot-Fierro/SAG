/**
 * ============================================================================
 * Script de DataTables Server-Side para Activos / Equipos Asignados
 * ============================================================================
 */

document.addEventListener('DOMContentLoaded', function () {
    const tableEl = document.querySelector('#myTable');
    if (!tableEl) return;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    const ajaxUrl = tableEl.dataset.ajaxUrl || window.location.pathname;
    const urlEditTemplate = tableEl.dataset.urlEdit || '';

    function getEditUrl(id) {
        if (!urlEditTemplate || id === undefined || id === null || id === '') return '#';
        return urlEditTemplate.replace('/0/', `/${id}/`).replace('/0', `/${id}`);
    }

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
            data: "ip",
            title: "IP",
            render: function (data) {
                if (!data || data === '-') return '-';
                return `<code class="text-dark">${escapeHtml(data)}</code>`;
            }
        },
        {
            data: "funcionario",
            title: "Funcionario",
            render: function (data) {
                return `<strong>${escapeHtml(data || '-')}</strong>`;
            }
        },
        {
            data: "unidad_organizacional",
            title: "Departamento / Unidad",
            render: function (data, type, row) {
                let html = `<strong>${escapeHtml(data || '-')}</strong>`;
                if (row && row.unidad_padre) {
                    html += `<br><small class="text-muted">${escapeHtml(row.unidad_padre)}</small>`;
                }
                return html;
            }
        },
        {
            data: null,
            title: "Acciones",
            defaultContent: "",
            orderable: false,
            searchable: false,
            className: "text-center",
            width: "110px",
            render: function (data, type, row) {
                const activoId = (row && row.activo_id) || (data && data.activo_id) || '';
                const actaUrl = (row && row.acta_url) || (data && data.acta_url) || '#';
                const editUrl = (row && row.edit_url) || (data && data.edit_url) || getEditUrl(activoId);

                return `
                    <div class="btn-group btn-group-sm" role="group">
                        <a href="${actaUrl}" target="_blank" class="btn btn-outline-danger" title="Ver Acta PDF">
                            <i class="bi bi-file-earmark-pdf"></i>
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
