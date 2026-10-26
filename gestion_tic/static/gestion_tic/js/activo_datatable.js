/**
 * ============================================================================
 * Script de Administración y Listado de Activos (DataTables Server-Side)
 * ============================================================================
 * Este archivo gestiona la inicialización de DataTable con procesamiento del lado
 * del servidor (server-side), filtros avanzados (tipo, marca, modelo, contrato, etc.),
 * exportación de datos y renderizado de acciones (edición y desactivación).
 */

document.addEventListener('DOMContentLoaded', function () {
    const tableEl = document.querySelector('#myTable');
    if (!tableEl) return;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    const urlEditTemplate = (tableEl && tableEl.dataset.urlEdit) || (typeof urlEditarActivo !== 'undefined' ? urlEditarActivo : '');
    const urlDeleteTemplate = (tableEl && tableEl.dataset.urlDelete) || (typeof urlEliminarActivo !== 'undefined' ? urlEliminarActivo : '');
    const defaultTipo = (tableEl && tableEl.dataset.tipo) || '';

    function getEditUrl(id) {
        if (!urlEditTemplate || id === undefined || id === null || id === '') return '#';
        return urlEditTemplate.replace('/0/', `/${id}/`).replace('/0', `/${id}`);
    }

    function getDeleteUrl(id) {
        if (!urlDeleteTemplate || id === undefined || id === null || id === '') return '#';
        return urlDeleteTemplate.replace('/0/', `/${id}/`).replace('/0', `/${id}`);
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
            width: "70px"
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
            data: "de_baja",
            title: "Estado",
            className: "text-center",
            render: function (data) {
                if (data === true) {
                    return '<span class="badge bg-danger">De Baja</span>';
                }
                return '<span class="badge bg-success">Activo</span>';
            }
        },
        {
            data: null,
            title: "Acciones",
            defaultContent: "",
            orderable: false,
            searchable: false,
            className: "text-center",
            width: "130px",
            render: function (data, type, row) {
                const rowId = (row && row.id) || (data && data.id) || '';
                const rowName = (row && row.codigo_barra) || (data && data.codigo_barra) || `ID ${rowId}`;
                const editUrl = getEditUrl(rowId);
                const deleteUrl = getDeleteUrl(rowId);
                const actaUrl = (row && row.acta_url) || (data && data.acta_url) || null;

                let actaBtn = '';
                if (actaUrl) {
                    actaBtn = `
                        <a href="${escapeHtml(actaUrl)}"
                           class="btn btn-sm btn-outline-danger"
                           title="Ver Acta PDF"
                           target="_blank"
                           rel="noopener noreferrer"
                           aria-label="Ver Acta PDF">
                            <i class="bi bi-file-earmark-pdf"></i>
                        </a>
                    `;
                }

                return `
                    <div class="d-flex gap-1 justify-content-center">
                        ${actaBtn}
                        <a href="${editUrl}"
                           class="btn btn-sm btn-outline-primary"
                           title="Editar"
                           aria-label="Editar"
                           data-bs-toggle="tooltip">
                            <i class="bi bi-pencil"></i>
                        </a>
                        <button type="button"
                                class="btn btn-sm btn-outline-danger btn-desactivar"
                                data-id="${escapeHtml(rowId)}"
                                data-name="${escapeHtml(rowName)}"
                                data-url="${deleteUrl}"
                                title="Desactivar"
                                aria-label="Desactivar"
                                data-bs-toggle="tooltip">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                `;
            }
        }
    ];

    const actionColIndex = columns.length - 1;

    let table = new DataTable('#myTable', {
        paging: true,
        processing: true,
        responsive: true,
        pageLength: 10,
        lengthMenu: [10, 25, 50, 100],
        keyTable: true,
        order: [[1, 'asc']],

        select: {
            style: 'single',
            selector: `td:not(:nth-child(${actionColIndex + 1}))`
        },

        buttons: {
            dom: {
                button: {
                    className: 'btn btn-sm btn-outline-secondary'
                }
            },
            buttons: [
                {
                    extend: 'copy',
                    text: '<i class="bi bi-copy"></i> Copiar',
                    attr: {title: 'Copiar', 'aria-label': 'Copiar'}
                },
                {
                    extend: 'csv',
                    text: '<i class="bi bi-filetype-csv"></i> CSV',
                    attr: {title: 'Exportar CSV', 'aria-label': 'Exportar CSV'}
                },
                {
                    extend: 'excel',
                    text: '<i class="bi bi-file-earmark-excel"></i> XLS',
                    attr: {title: 'Exportar Excel', 'aria-label': 'Exportar Excel'}
                },
                {
                    extend: 'pdf',
                    text: '<i class="bi bi-file-earmark-pdf"></i> PDF',
                    attr: {title: 'Exportar PDF', 'aria-label': 'Exportar PDF'}
                },
                {
                    extend: 'print',
                    text: '<i class="bi bi-printer"></i> Imprimir',
                    attr: {title: 'Imprimir', 'aria-label': 'Imprimir'}
                },
                {
                    text: '<i class="bi bi-arrow-clockwise"></i> Recargar',
                    attr: {
                        title: 'Recargar tabla',
                        'aria-label': 'Recargar tabla'
                    },
                    action: function (e, dt) {
                        dt.ajax.reload(null, false);
                    }
                },
                {
                    text: '<i class="bi bi-eraser"></i> Limpiar',
                    attr: {
                        title: 'Limpiar filtros',
                        'aria-label': 'Limpiar filtros'
                    },
                    action: function (e, dt) {
                        const filterForm = document.querySelector('#filter-form');
                        if (filterForm) {
                            filterForm.reset();
                            filterForm.querySelectorAll('select').forEach(sel => {
                                if (sel.tomselect) sel.tomselect.clear();
                            });
                        }
                        dt.search('').columns().search('');
                        dt.ajax.reload(null, false);
                    }
                }
            ]
        },

        layout: {
            topStart: 'pageLength',
            top: 'buttons',
            topEnd: 'search',
            bottomStart: 'info',
            bottomEnd: 'paging'
        },

        serverSide: true,

        ajax: {
            url: window.location.pathname + window.location.search,
            type: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            data: function (d) {
                d.action = 'search';

                const filterForm = document.querySelector('#filter-form');
                if (filterForm) {
                    const formData = new FormData(filterForm);
                    for (const [key, val] of formData.entries()) {
                        if (val) {
                            d[key] = val;
                        }
                    }
                } else if (defaultTipo) {
                    d.tipo = defaultTipo;
                }
            },
            dataSrc: 'data'
        },

        columns: columns,

        columnDefs: [
            {
                targets: [actionColIndex],
                orderable: false,
                searchable: false
            }
        ],

        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.3.6/i18n/es-ES.json',
            processing: 'Cargando datos, por favor espera...'
        }
    });

    // Manejo de formulario de filtros
    const filterForm = document.querySelector('#filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', function (e) {
            e.preventDefault();
            table.ajax.reload(null, false);
        });

        const btnLimpiar = document.querySelector('#btn-limpiar-filtros');
        if (btnLimpiar) {
            btnLimpiar.addEventListener('click', function () {
                filterForm.reset();
                filterForm.querySelectorAll('select').forEach(sel => {
                    if (sel.tomselect) sel.tomselect.clear();
                });
                table.search('').columns().search('');
                table.ajax.reload(null, false);
            });
        }
    }
});
