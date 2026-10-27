/**
 * ============================================================================
 * Script de Administración y Listado de Tickets de Soporte
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
    const urlEditTemplate = (tableEl && tableEl.dataset.urlEdit) || (typeof urlEditarTicket !== 'undefined' ? urlEditarTicket : '');
    const urlDeleteTemplate = (tableEl && tableEl.dataset.urlDelete) || (typeof urlEliminarTicket !== 'undefined' ? urlEliminarTicket : '');

    // ------------------------------------------------------------------------
    // 2. FUNCIONES AUXILIARES Y HELPERS
    // ------------------------------------------------------------------------

    /**
     * Construye dinámicamente la URL para la edición de un registro reemplazando
     * el identificador temporal (0) por el ID real del ticket.
     * @param {number|string} id - Identificador del registro.
     * @returns {string} URL formateada para editar el ticket.
     */
    function getEditUrl(id) {
        if (!urlEditTemplate || id === undefined || id === null || id === '') return '#';
        return urlEditTemplate.replace('/0/', `/${id}/`).replace('/0', `/${id}`);
    }

    /**
     * Construye dinámicamente la URL para la eliminación de un registro reemplazando
     * el identificador temporal (0) por el ID real del ticket.
     * @param {number|string} id - Identificador del registro.
     * @returns {string} URL formateada para eliminar el ticket.
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

    function renderTexto(data, type) {
        if (!data) {
            return type === 'display'
                ? '<span class="text-body-secondary">Sin asignar</span>'
                : '';
        }

        return type === 'display' ? escapeHtml(data) : data;
    }

    function renderEstado(data, type) {
        if (type !== 'display') {
            return data ?? '';
        }

        const estados = {
            'ABIERTO': {
                label: 'Abierto',
                clase: 'text-bg-primary'
            },
            'EN PROCESO': {
                label: 'En proceso',
                clase: 'text-bg-info'
            },
            'ESPERA': {
                label: 'En espera',
                clase: 'text-bg-warning'
            },
            'CERRADO': {
                label: 'Cerrado',
                clase: 'text-bg-success'
            },
            'RECHAZADO': {
                label: 'Rechazado',
                clase: 'text-bg-danger'
            },
            'CANCELADO': {
                label: 'Cancelado',
                clase: 'text-bg-secondary'
            }
        };

        const estado = estados[data];

        if (!estado) {
            return escapeHtml(data);
        }

        return `
            <span class="badge ${estado.clase}">
                ${escapeHtml(estado.label)}
            </span>
        `;
    }

    const formatoFecha = new Intl.DateTimeFormat('es-CL', {
        dateStyle: 'short',
        timeStyle: 'short'
    });

    function renderFecha(data, type) {
        if (!data) {
            return type === 'display'
                ? '<span class="text-body-secondary">—</span>'
                : '';
        }

        if (type !== 'display' && type !== 'filter') {
            return data;
        }

        const fecha = new Date(data);

        if (Number.isNaN(fecha.getTime())) {
            return type === 'display' ? escapeHtml(data) : data;
        }

        return formatoFecha.format(fecha);
    }

    function abrirFiltro(event, dt, columna) {
        event.preventDefault();
        event.stopPropagation();

        setTimeout(function () {
            const encabezado = dt.column(columna).header();
            const botonFiltro = encabezado.querySelector(
                'button.dtcc-button_dropdown'
            );

            if (!botonFiltro) {
                console.warn(
                    `No se encontró el filtro de la columna ${columna}`
                );
                return;
            }

            botonFiltro.click();
        }, 0);
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
        keys: false,
        order: [[6, 'desc']],

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
                    text: '<i class="bi bi-funnel"></i> Estado',
                    action: function (e, dt) { abrirFiltro(e, dt, 3); }
                },
                {
                    text: '<i class="bi bi-funnel"></i> Área de soporte',
                    action: function (e, dt) { abrirFiltro(e, dt, 4); }
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
            {data: 'numero_ticket', render: renderTexto},
            {data: 'titulo', render: renderTexto},
            {data: 'nombres', render: renderTexto},
            {data: 'estado', render: renderEstado},
            {data: 'area_soporte', render: renderTexto},
            {data: 'asignado_a', render: renderTexto},
            {data: 'created_at', render: renderFecha},
            {data: 'fecha_cierre', render: renderFecha},
            {
                // Columna de Acciones: Botón de Editar y Botón de Eliminar (Modal SweetAlert2)
                data: null,
                defaultContent: "",
                orderable: false,
                searchable: false,
                className: "text-center",
                render: function (data, type, row) {
                    const rowId = (row && row.id) || (data && data.id) || '';
                    const rowName = (row && (row.numero_ticket || row.titulo)) || (data && (data.numero_ticket || data.titulo)) || `ID ${rowId}`;
                    const editUrl = getEditUrl(rowId);
                    const deleteUrl = getDeleteUrl(rowId);

                    if (type !== 'display') return '';
                    const takeUrl = tableEl.dataset.urlTake.replace('/0/', `/${rowId}/`);
                    const closeUrl = tableEl.dataset.urlClose.replace('/0/', `/${rowId}/`);
                    return `
                        <div class="d-flex gap-1 justify-content-center">
                            ${!row.asignado_a ? `<form method="post" action="${escapeHtml(takeUrl)}">
                                <input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(csrfToken)}">
                                <button class="btn btn-sm btn-outline-success" title="Tomar ticket" aria-label="Tomar ticket"><i class="bi bi-person-check"></i></button>
                            </form>` : ''}
                            <button type="button" class="btn btn-sm btn-outline-success btn-cerrar-ticket"
                                    data-url="${escapeHtml(closeUrl)}" title="Cerrar ticket" aria-label="Cerrar ticket">
                                <i class="bi bi-check-circle"></i>
                            </button>
                            <a href="${editUrl}"
                               class="btn btn-sm btn-outline-primary"
                               title="Editar"
                               aria-label="Editar"
                               data-bs-toggle="tooltip">
                                <i class="bi bi-pencil"></i>
                            </a>
                            <button type="button"
                                    class="btn btn-sm btn-outline-danger btn-eliminar-ticket"
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
                targets: [3, 4],
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
