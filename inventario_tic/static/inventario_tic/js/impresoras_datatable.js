/**
 * ============================================================================
 * Script de Administración y Listado de Impresoras (DataTables Server-Side)
 * ============================================================================
 * Este archivo gestiona la inicialización de DataTable con procesamiento del lado
 * del servidor (server-side), exportación de datos, filtros de búsqueda y
 * renderizado de acciones (edición y desactivación).
 */

document.addEventListener('DOMContentLoaded', function () {
    // ------------------------------------------------------------------------
    // 1. OBTENCIÓN DE CONFIGURACIÓN Y TOKENS
    // ------------------------------------------------------------------------

    const tableEl = document.querySelector('#impresorasTable');
    if (!tableEl) return;

    const urlActaTemplate = tableEl.dataset.urlActa || '';

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    const urlEditTemplate = (tableEl && tableEl.dataset.urlEdit) || (typeof urlEditarImpresora !== 'undefined' ? urlEditarImpresora : '');
    const urlDeleteTemplate = (tableEl && tableEl.dataset.urlDelete) || (typeof urlEliminarImpresora !== 'undefined' ? urlEliminarImpresora : '');

    // ------------------------------------------------------------------------
    // 2. FUNCIONES AUXILIARES Y HELPERS
    // ------------------------------------------------------------------------

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

    // ------------------------------------------------------------------------
    // 3. DEFINICIÓN DE COLUMNAS
    // ------------------------------------------------------------------------

    const columns = [
        {
            data: 'numero_serie', title: 'Número de Serie', defaultContent: '', render: function (data) {
                return escapeHtml(data ?? '');
            }
        },
        {
            data: 'hh', title: 'HH', defaultContent: '', render: function (data) {
                return escapeHtml(data ?? '');
            }
        },
        {
            data: 'marca__nombre', title: 'Marca', defaultContent: '', render: function (data) {
                return escapeHtml(data ?? '');
            }
        },
        {
            data: 'modelo__nombre', title: 'Modelo', defaultContent: '', render: function (data) {
                return escapeHtml(data ?? '');
            }
        },
        {
            data: 'imprime_color', title: 'Color', defaultContent: '', render: function (data) {
                return data ? 'Sí' : 'No';
            }
        },
        {
            data: 'tiene_ethernet', title: 'Ethernet', defaultContent: '', render: function (data) {
                return data ? 'Sí' : 'No';
            }
        },
        {
            data: 'tiene_wifi', title: 'Wi-Fi', defaultContent: '', render: function (data) {
                return data ? 'Sí' : 'No';
            }
        },
        {
            data: 'toner', title: 'Consumible', defaultContent: '', render: function (data) {
                return escapeHtml(data ?? '');
            }
        },
        {
            data: 'departamento__nombre', title: 'Departamento', defaultContent: '', render: function (data) {
                return escapeHtml(data ?? '');
            }
        },
        {
            data: 'observacion', title: 'Observación', defaultContent: '', render: function (data) {
                return escapeHtml(data ?? '');
            }
        },
        {
            data: null,
            title: "Acciones",
            defaultContent: "",
            orderable: false,
            searchable: false,
            className: "text-center",
            render: function (data, type, row) {
                const rowId = (row && row.id) || (data && data.id) || '';
                const rowName = (row && row.numero_serie) || (data && data.numero_serie) || `ID ${rowId}`;
                const editUrl = getEditUrl(rowId);
                const deleteUrl = getDeleteUrl(rowId);
                const actaUrl = urlActaTemplate.replace('/0/', `/${rowId}/`);
                const actaButton = row?.puede_generar_acta && urlActaTemplate ? `
                        <a href="${escapeHtml(actaUrl)}"
                           class="btn btn-sm btn-outline-danger"
                           target="_blank" rel="noopener noreferrer"
                           title="Generar acta" aria-label="Generar acta"
                           data-bs-toggle="tooltip">
                            <i class="bi bi-file-earmark-pdf"></i>
                        </a>` : '';

                return `
                    <div class="d-flex gap-1 justify-content-center">
                        ${actaButton}
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

    // ------------------------------------------------------------------------
    // 4. INICIALIZACIÓN Y CONFIGURACIÓN DE DATATABLE
    // ------------------------------------------------------------------------

    let table = new DataTable('#impresorasTable', {
        paging: true,
        processing: true,
        responsive: true,
        pageLength: 10,
        lengthMenu: [10, 25, 50, 100],
        keyTable: true,
        order: [[0, 'asc']],

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
                        window.location.reload();
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
            data: {
                'action': 'search'
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
});
