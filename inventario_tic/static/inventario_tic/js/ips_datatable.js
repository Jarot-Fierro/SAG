/**
 * ============================================================================
 * Script de Administración y Listado de Direcciones IP (DataTables Server-Side)
 * ============================================================================
 * Este archivo gestiona la inicialización de DataTable con procesamiento del lado
 * del servidor (server-side), filtros específicos por segmento IP, búsqueda global,
 * exportación de datos y renderizado de acciones (edición y desactivación).
 */

document.addEventListener('DOMContentLoaded', function () {
    const tableEl = document.querySelector('#myTable');
    if (!tableEl) return;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    const urlEditTemplate = (tableEl && tableEl.dataset.urlEdit) || (typeof urlEditarIps !== 'undefined' ? urlEditarIps : '');
    const urlDeleteTemplate = (tableEl && tableEl.dataset.urlDelete) || (typeof urlEliminarIps !== 'undefined' ? urlEliminarIps : '');

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
            data: "ip",
            title: "Dirección IP",
            render: function (data) {
                return `<strong>${escapeHtml(data || '')}</strong>`;
            }
        },
        {
            data: "mascara",
            title: "Máscara",
            defaultContent: "",
            render: function (data) {
                return escapeHtml(data || '-');
            }
        },
        {
            data: "gateway",
            title: "Gateway",
            defaultContent: "",
            render: function (data) {
                return escapeHtml(data || '-');
            }
        },
        {
            data: "vlan",
            title: "VLAN",
            defaultContent: "",
            render: function (data) {
                return escapeHtml(data || '-');
            }
        },
        {
            data: "asignado",
            title: "Estado",
            className: "text-center",
            render: function (data) {
                if (data === true || data === 'true' || data === 1) {
                    return '<span class="badge bg-success">Asignado</span>';
                }
                return '<span class="badge bg-secondary">Disponible</span>';
            }
        },
        {
            data: "observacion",
            title: "Observación",
            defaultContent: "",
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
                const rowId = (row && row.id) || (data && data.id) || '';
                const rowName = (row && row.ip) || (data && data.ip) || `ID ${rowId}`;
                const editUrl = getEditUrl(rowId);
                const deleteUrl = getDeleteUrl(rowId);

                return `
                    <div class="d-flex gap-1 justify-content-center">
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
                    action: function () {
                        const segFilter = document.querySelector('#segmento-filter');
                        if (segFilter) {
                            if (segFilter.tomselect) {
                                segFilter.tomselect.setValue('');
                            } else {
                                segFilter.value = '';
                            }
                        }
                        table.search('').draw();
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
                const segFilter = document.querySelector('#segmento-filter');
                if (segFilter && segFilter.value) {
                    d.segmento = segFilter.value;
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

    const segmentoFilterEl = document.querySelector('#segmento-filter');
    if (segmentoFilterEl) {
        segmentoFilterEl.addEventListener('change', function () {
            table.ajax.reload();
        });
    }
});
