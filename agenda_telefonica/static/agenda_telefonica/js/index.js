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

        // Solo generar enlaces HTTP o HTTPS válidos.
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

    let table = new DataTable('#myTable', {
        paging: true,
        processing: true,
        select: 'single',
        responsive: true,
        pageLength: 25,
        lengthMenu: [10, 25, 50, 100],
        keyTable: true,
        order: [[0, 'desc']],
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
                    extend: 'excel',
                    text: '<i class="bi bi-file-earmark-excel"></i> XLS',
                    attr: {title: 'Exportar Excel', 'aria-label': 'Exportar Excel'}
                },
                {
                    text: '<i class="bi bi-funnel"></i> Departamento / Servicio',
                    attr: {
                        title: 'Filtrar por departamento o servicio',
                        'aria-label': 'Filtrar por departamento o servicio'
                    },
                    action: function (e, dt) {
                        e.preventDefault();
                        e.stopPropagation();

                        setTimeout(function () {
                            const encabezado = dt.column(5).header();
                            const botonFiltro = encabezado.querySelector(
                                'button.dtcc-button_dropdown'
                            );

                            if (!botonFiltro) {
                                console.warn('No se encontró el filtro de la columna 5');
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
        ],
        columnDefs: [
            {
                targets: [5],
                columnControl: ['order', ['searchList']]
            },
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
