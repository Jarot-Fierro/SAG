document.addEventListener('DOMContentLoaded', function () {
    const csrfToken = document.querySelector(
        '[name=csrfmiddlewaretoken]'
    ).value;

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

    const table = new DataTable('#myTable', {
        paging: true,
        processing: true,
        select: 'single',
        responsive: true,
        pageLength: 25,
        lengthMenu: [10, 25, 50, 100],
        keyTable: true,
        order: [[6, 'desc']],

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
                    attr: {
                        title: 'Copiar',
                        'aria-label': 'Copiar'
                    }
                },
                {
                    extend: 'excel',
                    text: '<i class="bi bi-file-earmark-excel"></i> XLS',
                    attr: {
                        title: 'Exportar Excel',
                        'aria-label': 'Exportar Excel'
                    }
                },
                {
                    text: '<i class="bi bi-funnel"></i> Estado',
                    attr: {
                        title: 'Filtrar por estado',
                        'aria-label': 'Filtrar por estado'
                    },
                    action: function (e, dt) {
                        abrirFiltro(e, dt, 3);
                    }
                },
                {
                    text: '<i class="bi bi-funnel"></i> Área de soporte',
                    attr: {
                        title: 'Filtrar por área de soporte',
                        'aria-label': 'Filtrar por área de soporte'
                    },
                    action: function (e, dt) {
                        abrirFiltro(e, dt, 4);
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
                action: 'search'
            },
            dataSrc: 'data'
        },

        columns: [
            {
                data: 'numero_ticket',
                defaultContent: '',
                render: renderTexto
            },
            {
                data: 'titulo',
                defaultContent: '',
                render: renderTexto
            },
            {
                data: 'nombres',
                defaultContent: '',
                render: renderTexto
            },
            {
                data: 'estado',
                defaultContent: '',
                render: renderEstado
            },
            {
                data: 'area_soporte',
                defaultContent: '',
                render: renderTexto
            },
            {
                data: 'asignado_a',
                defaultContent: '',
                render: renderTexto
            },
            {
                data: 'created_at',
                defaultContent: '',
                render: renderFecha
            },
            {
                data: 'fecha_cierre',
                defaultContent: '',
                render: renderFecha
            }
        ],

        columnDefs: [
            {
                targets: [3, 4],
                columnControl: ['order', ['searchList']]
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

    let seconds = 180;
    if (countdownEl) {
        countdownEl.textContent = '3:00';
    }

    const refreshInterval = setInterval(function () {
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
        if (countdownEl) {
            countdownEl.textContent = `${mins}:${remSecs < 10 ? '0' : ''}${remSecs}`;
        }
    }, 1000);

    table.on('destroy', function () {
        clearInterval(refreshInterval);
    });
});
