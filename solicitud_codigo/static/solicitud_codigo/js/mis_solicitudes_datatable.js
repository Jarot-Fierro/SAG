/**
 * ============================================================================
 * Script de DataTable para Mis Solicitudes (solicitud_codigo)
 * ============================================================================
 * Gestiona la inicialización de DataTable con procesamiento del lado del servidor,
 * filtros por columna y recarga automática para las solicitudes del usuario.
 */

document.addEventListener('DOMContentLoaded', function () {
    const tableEl = document.querySelector('#myTable') || document.querySelector('.table-datatable');
    if (!tableEl) return;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    const ajaxUrl = (tableEl && tableEl.dataset.ajaxUrl) || window.location.pathname + window.location.search;

    const table = new DataTable(tableEl, {
        paging: true,
        processing: true,
        responsive: true,
        pageLength: 10,
        lengthMenu: [10, 25, 50, 100],
        keyTable: true,
        order: [[1, 'desc']],

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
            url: ajaxUrl,
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
                data: 'numero_solicitud',
                render: function (data, type, row) {
                    if (type !== 'display') return data || '';
                    return `<span class="fw-bold font-monospace text-primary">${data || ''}</span>`;
                }
            },
            {
                data: 'fecha_solicitud'
            },
            {
                data: 'area__nombre'
            },
            {
                data: 'subarea__nombre'
            },
            {
                data: 'producto_base',
                render: function (data, type, row) {
                    if (type !== 'display') return data || '';
                    return `<span class="fw-semibold">${data || ''}</span>`;
                }
            },
            {
                data: 'presentacion'
            },
            {
                data: 'estado',
                render: function (data, type, row) {
                    return data || '';
                }
            },
            {
                data: 'acciones',
                orderable: false,
                searchable: false,
                className: 'text-center'
            }
        ],

        columnDefs: [
            {
                targets: [2],
                columnControl: ['order', ['searchList']]
            },
            {
                targets: [3, 4, 5, 6],
                columnControl: ['order', ['searchDropdown']]
            },
            {
                targets: [7],
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

    // Actualización automática cada 3 minutos
    const countdownEl = document.getElementById('countdown');
    const lastUpdateEl = document.getElementById('last-update');

    if (countdownEl) {
        let seconds = 180;
        countdownEl.textContent = '3:00';

        setInterval(function () {
            seconds--;

            if (seconds <= 0) {
                seconds = 180;
                table.ajax.reload(function () {
                    if (lastUpdateEl) {
                        lastUpdateEl.textContent = 'Actualizado: ' + new Date().toLocaleTimeString('es-CL');
                    }
                }, false);
            }

            const mins = Math.floor(seconds / 60);
            const remSecs = seconds % 60;
            countdownEl.textContent = `${mins}:${remSecs < 10 ? '0' : ''}${remSecs}`;
        }, 1000);
    }
});
