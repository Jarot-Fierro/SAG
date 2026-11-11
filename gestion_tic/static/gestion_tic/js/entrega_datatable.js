/**
 * ============================================================================
 * Script de Listado de Entregas de Activos (DataTables Server-Side)
 * ============================================================================
 * Este archivo gestiona la inicialización de DataTable con procesamiento del lado
 * del servidor (server-side), exportación de datos, filtros de búsqueda y
 * renderizado de acciones y estados de entrega.
 */

document.addEventListener('DOMContentLoaded', function () {
    // ------------------------------------------------------------------------
    // 1. OBTENCIÓN DE CONFIGURACIÓN Y TOKENS
    // ------------------------------------------------------------------------

    const tableEl = document.querySelector('#myTable');
    if (!tableEl) return;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    const urlDetalleTemplate = (tableEl && tableEl.dataset.urlDetalle) || (typeof urlDetalleEntrega !== 'undefined' ? urlDetalleEntrega : '');

    // ------------------------------------------------------------------------
    // 2. FUNCIONES AUXILIARES Y HELPERS
    // ------------------------------------------------------------------------

    /**
     * Construye dinámicamente la URL para el detalle de una entrega reemplazando
     * el identificador temporal (0) por el ID real de la entrega.
     * @param {number|string} id - Identificador de la entrega.
     * @returns {string} URL formateada para ver el detalle de la entrega.
     */
    function getDetalleUrl(id) {
        if (!urlDetalleTemplate || id === undefined || id === null || id === '') return '#';
        return urlDetalleTemplate.replace('/0/', `/${id}/`).replace('/0', `/${id}`);
    }

    /**
     * Escapa caracteres especiales en cadenas para prevenir vulnerabilidades XSS.
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
     * Renderizador para la columna de Estado con badges Bootstrap.
     * @param {string} data - Código del estado.
     * @param {string} type - Tipo de renderizado ('display', 'filter', etc.).
     * @param {Object} row - Objeto con los datos completos de la fila actual.
     * @returns {string} Badge HTML renderizado o texto según corresponda.
     */
    function renderEstado(data, type, row) {
        if (type !== 'display') {
            return (row && row.estado_display) || data || '';
        }
        const estado = (row && row.estado) || data || '';
        const estadoDisplay = (row && row.estado_display) || data || '';
        let badgeClass = 'bg-secondary';
        if (estado === 'borrador') {
            badgeClass = 'bg-secondary';
        } else if (estado === 'pendiente') {
            badgeClass = 'bg-warning text-dark';
        } else if (estado === 'recepcionada') {
            badgeClass = 'bg-success';
        }
        return `<span class="badge ${badgeClass}">${escapeHtml(estadoDisplay)}</span>`;
    }

    /**
     * Renderizador para la columna de Acciones.
     * @param {any} data - Datos de la celda.
     * @param {string} type - Tipo de renderizado.
     * @param {Object} row - Objeto de datos de la fila.
     * @returns {string} Botones de acción HTML.
     */
    function renderAcciones(data, type, row) {
        const rowId = (row && (row.id || row.folio)) || (data && (data.id || data.folio)) || '';
        const detalleUrl = (row && row.detalle_url) || (data && data.detalle_url) || getDetalleUrl(rowId);

        return `
            <div class="d-flex gap-1 justify-content-center">
                <a href="${detalleUrl}"
                   class="btn btn-sm btn-outline-primary"
                   title="Ver entrega"
                   aria-label="Ver entrega"
                   data-bs-toggle="tooltip">
                    <i class="bi bi-eye me-1"></i>Ver entrega
                </a>
            </div>
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

        select: {
            style: 'single',
            selector: 'td:not(:last-child)'
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
                    text: '<i class="bi bi-funnel"></i> Estado',
                    attr: {
                        title: 'Filtrar por estado',
                        'aria-label': 'Filtrar por estado'
                    },
                    action: function (e, dt) {
                        e.preventDefault();
                        e.stopPropagation();

                        setTimeout(function () {
                            const encabezado = dt.column(2).header();
                            const botonFiltro = encabezado ? encabezado.querySelector(
                                'button.dtcc-button_dropdown'
                            ) : null;

                            if (!botonFiltro) {
                                console.warn('No se encontró el filtro de la columna 2');
                                return;
                            }

                            botonFiltro.click();
                        }, 0);
                    }
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

        columnControl: ['order'],
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

        columns: [
            {
                data: "folio",
                title: "Folio",
                className: "text-center",
                width: "80px",
                render: function (data) {
                    return `<strong>${escapeHtml(data || '')}</strong>`;
                }
            },
            {
                data: "funcionario",
                title: "Destinatario",
                render: function (data) {
                    return escapeHtml(data || '-');
                }
            },
            {
                data: "estado",
                title: "Estado",
                render: renderEstado
            },
            {
                data: "created_at",
                title: "Fecha",
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
                width: "140px",
                render: renderAcciones
            }
        ],

        columnDefs: [
            {
                targets: [2],
                columnControl: ['order', ['searchList']]
            },
            {
                targets: [4],
                orderable: false,
                searchable: false,
                columnControl: []
            }
        ],

        ordering: {
            indicators: false,
            handler: false
        },

        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.3.6/i18n/es-ES.json',
            processing: 'Cargando datos, por favor espera...'
        }
    });
});
