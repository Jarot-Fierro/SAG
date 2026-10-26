/**
 * ============================================================================
 * Script de Administración y Listado de Anexos Telefónicos
 * ============================================================================
 * Este archivo gestiona la inicialización de DataTable con procesamiento del lado
 * del servidor (server-side), exportación de datos, filtros de búsqueda y
 * renderizado de acciones (edición y eliminación).
 */

document.addEventListener('DOMContentLoaded', function () {
    // ------------------------------------------------------------------------
    // 1. OBTENCIÓN DE CONFIGURACIÓN Y TOKENS
    // ------------------------------------------------------------------------

    // Elemento HTML de la tabla
    const tableEl = document.querySelector('#myTable');

    // Token CSRF necesario para autenticar peticiones POST en Django
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    // Plantillas de URL obtenidas desde data-attributes de la tabla o variables globales
    const urlEditTemplate = (tableEl && tableEl.dataset.urlEdit) || (typeof urlEditarAnexo !== 'undefined' ? urlEditarAnexo : '');
    const urlDeleteTemplate = (tableEl && tableEl.dataset.urlDelete) || (typeof urlEliminarAnexo !== 'undefined' ? urlEliminarAnexo : '');

    // ------------------------------------------------------------------------
    // 2. FUNCIONES AUXILIARES Y HELPERS
    // ------------------------------------------------------------------------

    /**
     * Construye dinámicamente la URL para la edición de un registro reemplazando
     * el identificador temporal (0) por el ID real del anexo.
     * @param {number|string} id - Identificador del registro.
     * @returns {string} URL formateada para editar el anexo.
     */
    function getEditUrl(id) {
        if (!urlEditTemplate || id === undefined || id === null || id === '') return '#';
        return urlEditTemplate.replace('/0/', `/${id}/`).replace('/0', `/${id}`);
    }

    /**
     * Construye dinámicamente la URL para la eliminación de un registro reemplazando
     * el identificador temporal (0) por el ID real del anexo.
     * @param {number|string} id - Identificador del registro.
     * @returns {string} URL formateada para eliminar el anexo.
     */
    function getDeleteUrl(id) {
        if (!urlDeleteTemplate || id === undefined || id === null || id === '') return '#';
        return urlDeleteTemplate.replace('/0/', `/${id}/`).replace('/0', `/${id}`);
    }

    /**
     * Escapa caracteres especiales en cadenas para prevenir vulnerabilidades XSS
     * al inyectar contenido dinámico dentro del DOM o de atributos HTML.
     * @param {string|any} value - Valor a sanitizar.
     * @returns {string} Cadena segura con entidades HTML escapadas.
     */
    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        })[character]);
    }

    /**
     * Renderizador personalizado para la columna de Dirección.
     * Si la fila posee un enlace de Google Maps, se crea un hipervínculo con icono.
     * @param {string} data - Texto de la dirección.
     * @param {string} type - Tipo de renderizado ('display', 'filter', etc.).
     * @param {Object} row - Objeto con los datos completos de la fila actual.
     * @returns {string} HTML renderizado o texto plano según corresponda.
     */
    function renderDireccion(data, type, row) {
        if (!data) {
            return type === 'display'
                ? '<span class="text-body-secondary">Sin asignar</span>'
                : '';
        }

        if (type !== 'display') {
            return data;
        }

        const label = escapeHtml(data);
        const enlace = row.unidad_organizacional__direccion__enlace_google_maps;

        if (!enlace) {
            return label;
        }

        // Validación de protocolo seguro HTTP/HTTPS para el enlace
        let url;
        try {
            url = new URL(enlace);
            if (!['http:', 'https:'].includes(url.protocol)) {
                return label;
            }
        } catch {
            return label;
        }

        return `
            <a href="${escapeHtml(url.href)}"
               class="text-decoration-none text-primary"
               target="_blank"
               rel="noopener noreferrer"
               title="Abrir ubicación en Google Maps">
                <i class="bi bi-geo-alt-fill me-1"></i>${label}
            </a>
        `;
    }

    // ------------------------------------------------------------------------
    // 3. INICIALIZACIÓN Y CONFIGURACIÓN DE DATATABLE
    // ------------------------------------------------------------------------

    let table = new DataTable('#myTable', {
        paging: true,
        processing: true,
        responsive: true,
        pageLength: 10,
        lengthMenu: [10, 25, 50, 100],
        keyTable: true,
        order: [[0, 'desc']],

        // Selección de filas (excluyendo la última columna de acciones para permitir clics directos)
        select: {
            style: 'single',
            selector: 'td:not(:last-child)'
        },

        // Botones de exportación y utilidades
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

        // Disposición visual de los componentes de la tabla
        layout: {
            topStart: 'pageLength',
            top: 'buttons',
            topEnd: 'search',
            bottomStart: 'info',
            bottomEnd: 'paging'
        },

        columnControl: ['order'],
        serverSide: true,

        // Configuración de la fuente de datos AJAX para server-side
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

        // Definición de las columnas del DataTable
        columns: [
            {data: "anexo"},
            {data: "anexo_publico"},
            {data: "numero_telefonico"},
            {data: "nombre_anexo"},
            {data: "email"},
            {data: "unidad_organizacional__nombre", defaultContent: ""},
            {
                data: "unidad_organizacional__direccion__nombre",
                defaultContent: "",
                render: renderDireccion
            },
            {data: "encargado_de"},
            {
                // Columna de Acciones: Botón de Editar y Botón de Eliminar (Modal SweetAlert2)
                data: null,
                defaultContent: "",
                orderable: false,
                searchable: false,
                className: "text-center",
                render: function (data, type, row) {
                    const rowId = (row && row.id) || (data && data.id) || '';
                    const rowName = (row && (row.nombre_anexo || row.anexo)) || (data && (data.nombre_anexo || data.anexo)) || `ID ${rowId}`;
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
                                    class="btn btn-sm btn-outline-danger btn-eliminar-anexo"
                                    data-id="${escapeHtml(rowId)}"
                                    data-name="${escapeHtml(rowName)}"
                                    data-url="${deleteUrl}"
                                    title="Eliminar"
                                    aria-label="Eliminar"
                                    data-bs-toggle="tooltip">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    `;
                }
            }
        ],

        // Definición de configuraciones específicas por columna
        columnDefs: [
            {
                targets: [5],
                columnControl: ['order', ['searchList']]
            },
            {
                targets: [8],
                orderable: false,
                searchable: false,
                columnControl: []
            }
        ],

        ordering: {
            indicators: false,
            handler: false
        },

        // Configuración de idioma al español
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.3.6/i18n/es-ES.json',
            processing: 'Cargando datos, por favor espera...'
        }
    });
});
