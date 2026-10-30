/**
 * ============================================================================
 * Script de Administración y Listado de Activos con Columnas Dinámicas
 * ============================================================================
 * Este archivo gestiona la inicialización de DataTable con procesamiento del lado
 * del servidor (server-side), soporte para columnas dinámicas según el tipo
 * de activo seleccionado, filtros avanzados, exportación de datos y renderizado
 * seguro de acciones y celdas.
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
        let url = urlEditTemplate.replace('/0/', `/${id}/`).replace('/0', `/${id}`);
        if (defaultTipo) {
            url += (url.includes('?') ? '&' : '?') + 'tipo=' + encodeURIComponent(defaultTipo);
        }
        return url;
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

    function getBaseColumns() {
        return [
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
                data: "contrato",
                title: "Contrato",
                render: function (data) {
                    return escapeHtml(data || '-');
                }
            }
        ];
    }

    function getActionColumn() {
        return {
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
        };
    }

    function buildColumnsConfig(dynCols) {
        const dynamicColDefs = (dynCols || []).map(col => ({
            data: `caracteristica_${col.id}`,
            title: escapeHtml(col.nombre),
            defaultContent: "-",
            orderable: false,
            render: function (data) {
                if (data === null || data === undefined || data === '') {
                    return '-';
                }
                return escapeHtml(data);
            }
        }));

        return [...getBaseColumns(), ...dynamicColDefs, getActionColumn()];
    }

    function rebuildThead(columnsConfig) {
        const thead = tableEl.querySelector('thead');
        if (!thead) return;
        thead.innerHTML = '';
        const tr = document.createElement('tr');
        columnsConfig.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col.title || '';
            if (col.className) {
                th.className = col.className;
            }
            tr.appendChild(th);
        });
        thead.appendChild(tr);
    }

    let table = null;
    let activeColumnsSignature = '';
    let lastRequestId = 0;

    function initDataTable(dynCols) {
        const columns = buildColumnsConfig(dynCols);
        const actionColIndex = columns.length - 1;

        if (table) {
            table.destroy();
            table = null;
        }

        rebuildThead(columns);

        table = new DataTable(tableEl, {
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
                            resetFiltersAndReload();
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
                    if (defaultTipo) {
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
    }

    async function updateColumnsAndReload(tipoId, isInitial = false) {
        const reqId = ++lastRequestId;

        let dynCols = [];
        if (tipoId) {
            try {
                const formData = new FormData();
                formData.append('action', 'get_columns');
                formData.append('tipo', tipoId);

                const response = await fetch(window.location.pathname + window.location.search, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData
                });

                if (reqId !== lastRequestId) return;

                if (response.ok) {
                    const resJson = await response.json();
                    dynCols = resJson.columns || [];
                }
            } catch (err) {
                if (reqId !== lastRequestId) return;
                console.error('Error al obtener columnas dinámicas:', err);
            }
        }

        if (reqId !== lastRequestId) return;

        const newSignature = dynCols.map(c => `${c.id}:${c.nombre}:${c.tipo_campo}`).join('|');

        if (!isInitial && newSignature === activeColumnsSignature && table) {
            table.ajax.reload(null, false);
            return;
        }

        activeColumnsSignature = newSignature;
        initDataTable(dynCols);
    }

    function resetFiltersAndReload() {
        if (table) {
            table.search('').draw();
        }
    }

    // Inicialización inicial
    const initDynColsEl = document.getElementById('initial-dynamic-columns');
    let initialDynCols = [];
    if (initDynColsEl) {
        try {
            initialDynCols = JSON.parse(initDynColsEl.textContent) || [];
        } catch (e) {
            initialDynCols = [];
        }
    }

    activeColumnsSignature = initialDynCols.map(c => `${c.id}:${c.nombre}:${c.tipo_campo}`).join('|');
    initDataTable(initialDynCols);
});
