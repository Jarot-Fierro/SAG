/**
 * ============================================================================
 * Script de Administración y Listado de Productos (DataTables Server-Side)
 * ============================================================================
 * Este archivo gestiona la inicialización de DataTable con procesamiento del lado
 * del servidor (server-side), exportación de datos, filtros de búsqueda y
 * renderizado de acciones (edición y desactivación).
 */

document.addEventListener('DOMContentLoaded', function () {
    // ------------------------------------------------------------------------
    // 1. OBTENCIÓN DE CONFIGURACIÓN Y TOKENS
    // ------------------------------------------------------------------------

    const tableEl = document.querySelector('#productosTable');
    if (!tableEl) return;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    const urlEditTemplate = (tableEl && tableEl.dataset.urlEdit) || (typeof urlEditarProducto !== 'undefined' ? urlEditarProducto : '');
    const urlDeleteTemplate = (tableEl && tableEl.dataset.urlDelete) || (typeof urlEliminarProducto !== 'undefined' ? urlEliminarProducto : '');

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
        {data: 'nombre', title: 'Nombre', defaultContent: '', render: function (data) { return escapeHtml(data ?? ''); }},
        {data: 'tipo_producto__nombre', title: 'Tipo de Producto', defaultContent: '', render: function (data) { return escapeHtml(data ?? ''); }},
        {data: 'marca__nombre', title: 'Marca', defaultContent: '', render: function (data) { return escapeHtml(data ?? ''); }},
        {data: 'modelo__nombre', title: 'Modelo', defaultContent: '', render: function (data) { return escapeHtml(data ?? ''); }},
        {data: 'stock_total', title: 'Stock Total', defaultContent: '', render: function (data) { return escapeHtml(data ?? ''); }},
        {data: 'stock_disponible', title: 'Stock Disponible', defaultContent: '', render: function (data) { return escapeHtml(data ?? ''); }},
        {data: 'stock_minimo', title: 'Stock Mínimo', defaultContent: '', render: function (data) { return escapeHtml(data ?? ''); }},
        {data: 'descripcion', title: 'Descripción', defaultContent: '', render: function (data) { return escapeHtml(data ?? ''); }},
        {data: 'observacion', title: 'Observación', defaultContent: '', render: function (data) { return escapeHtml(data ?? ''); }},
        {
            data: null,
            title: "Acciones",
            defaultContent: "",
            orderable: false,
            searchable: false,
            className: "text-center",
            render: function (data, type, row) {
                const rowId = (row && row.id) || (data && data.id) || '';
                const rowName = (row && row.nombre) || (data && data.nombre) || `ID ${rowId}`;
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

    // ------------------------------------------------------------------------
    // 4. INICIALIZACIÓN Y CONFIGURACIÓN DE DATATABLE
    // ------------------------------------------------------------------------

    let table = new DataTable('#productosTable', {
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
