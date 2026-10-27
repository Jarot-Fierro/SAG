/**
 * DataTables para Bandeja TIC de VPN
 */
let table;

$(document).ready(function () {
    const $table = $('#myTable');
    if (!$table.length) return;

    const ajaxUrl = $table.data('ajax-url') || window.location.href;
    const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();

    table = $table.DataTable({
        paging: true,
        pageLength: 20,
        lengthChange: true,
        lengthMenu: [[10, 20, 50, 100, -1], [10, 20, 50, 100, "Todos"]],
        searching: true,
        ordering: true,
        info: true,
        autoWidth: false,
        responsive: true,
        processing: true,
        serverSide: true,
        order: [[1, 'desc']],
        ajax: {
            url: ajaxUrl,
            type: 'POST',
            data: function (d) {
                d.action = 'search';
                d.csrfmiddlewaretoken = csrfToken;
                d.filtro_estado = $('#filtro_estado_solicitud').val();
            },
            dataSrc: function (json) {
                return json.data || [];
            },
            error: function (xhr, error, thrown) {
                console.error("Error en la carga de datos de Bandeja TIC VPN:", error, thrown);
            }
        },
        columns: [
            {
                data: 'numero_solicitud',
                name: 'numero_solicitud',
                orderable: true
            },
            {
                data: 'fecha_solicitud',
                name: 'fecha_solicitud',
                orderable: true
            },
            {
                data: 'establecimiento',
                name: 'establecimiento__nombre',
                orderable: true
            },
            {
                data: 'solicitante',
                name: 'tecnico_nombre',
                orderable: true
            },
            {
                data: 'accion',
                name: 'accion',
                orderable: true,
                className: 'text-center'
            },
            {
                data: 'beneficiarios',
                name: 'beneficiarios',
                orderable: false,
                className: 'text-center'
            },
            {
                data: 'estado',
                name: 'estado',
                orderable: true,
                className: 'text-center'
            },
            {
                data: 'acciones',
                name: 'acciones',
                orderable: false,
                searchable: false,
                className: 'text-center not-export'
            }
        ],
        layout: {
            topStart: {
                buttons: [
                    {
                        extend: 'copyHtml5',
                        text: '<i class="bi bi-clipboard me-1"></i> Copiar',
                        className: 'btn btn-sm btn-outline-secondary',
                        exportOptions: {
                            columns: ':visible:not(.not-export)'
                        }
                    },
                    {
                        extend: 'excelHtml5',
                        text: '<i class="bi bi-file-earmark-excel me-1"></i> Excel',
                        className: 'btn btn-sm btn-outline-success',
                        exportOptions: {
                            columns: ':visible:not(.not-export)'
                        }
                    },
                    {
                        extend: 'pdfHtml5',
                        text: '<i class="bi bi-file-earmark-pdf me-1"></i> PDF',
                        className: 'btn btn-sm btn-outline-danger',
                        orientation: 'landscape',
                        pageSize: 'A4',
                        exportOptions: {
                            columns: ':visible:not(.not-export)'
                        }
                    },
                    {
                        extend: 'print',
                        text: '<i class="bi bi-printer me-1"></i> Imprimir',
                        className: 'btn btn-sm btn-outline-dark',
                        exportOptions: {
                            columns: ':visible:not(.not-export)'
                        }
                    },
                    {
                        extend: 'colvis',
                        text: '<i class="bi bi-layout-three-columns me-1"></i> Columnas',
                        className: 'btn btn-sm btn-outline-info'
                    }
                ]
            }
        },
        language: {
            url: "https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json",
            search: "_INPUT_",
            searchPlaceholder: "Buscar por folio, solicitante, beneficiario...",
            processing: '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div>'
        },
        drawCallback: function () {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        },
        initComplete: function () {
            const api = this.api();
            const json = api.ajax.json();

            if (json && json.columnControl) {
                // Filtro Acción (col 4)
                if (json.columnControl.accion) {
                    const $headerAccion = $(api.column(4).header());
                    if (!$headerAccion.find('select').length) {
                        const $select = $('<select class="form-select form-select-sm mt-1"><option value="">Todas</option></select>');
                        json.columnControl.accion.forEach(function (opt) {
                            $select.append(`<option value="${opt.value}">${opt.label}</option>`);
                        });
                        $select.on('change', function () {
                            api.column(4).search($(this).val()).draw();
                        });
                        $select.on('click', function (e) {
                            e.stopPropagation();
                        });
                        $headerAccion.append($select);
                    }
                }

                // Filtro Estado (col 6)
                if (json.columnControl.estado) {
                    const $headerEstado = $(api.column(6).header());
                    if (!$headerEstado.find('select').length) {
                        const $select = $('<select class="form-select form-select-sm mt-1"><option value="">Todos</option></select>');
                        json.columnControl.estado.forEach(function (opt) {
                            $select.append(`<option value="${opt.value}">${opt.label}</option>`);
                        });
                        $select.on('change', function () {
                            api.column(6).search($(this).val()).draw();
                        });
                        $select.on('click', function (e) {
                            e.stopPropagation();
                        });
                        $headerEstado.append($select);
                    }
                }
            }
        }
    });

    // Eventos modales dinámicos
    $(document).on('click', '.btn-econecta-modal', function () {
        const id = $(this).data('sol-id');
        const folio = $(this).data('sol-folio');
        const ticket = $(this).data('sol-ticket');

        $('#modal-econecta-folio').text(folio);
        $('#input-modal-ticket').val(ticket || '');
        const urlBase = $table.data('url-econecta') || '/solicitud-vpn/marcar-econecta/0/';
        $('#form-marcar-econecta').attr('action', urlBase.replace('0', id).replace(/\/0\/?$/, `/${id}/`));

        const modal = new bootstrap.Modal(document.getElementById('modalEconecta'));
        modal.show();
    });

    $(document).on('click', '.btn-completar-modal', function () {
        const id = $(this).data('sol-id');
        const folio = $(this).data('sol-folio');

        $('#modal-completar-folio').text(folio);
        const urlBase = $table.data('url-completar') || '/solicitud-vpn/marcar-completado/0/';
        $('#form-marcar-completar').attr('action', urlBase.replace('0', id).replace(/\/0\/?$/, `/${id}/`));

        const modal = new bootstrap.Modal(document.getElementById('modalCompletar'));
        modal.show();
    });

    $(document).on('click', '.btn-notificar-modal', function () {
        const id = $(this).data('sol-id');
        const folio = $(this).data('sol-folio');
        const destinatario = $(this).data('sol-destinatario');
        const email = $(this).data('sol-email');
        const estado = $(this).data('sol-estado');

        $('#modal-notificar-folio').text(folio);
        $('#modal-notificar-destinatario').text(destinatario || '-');
        $('#modal-notificar-email').text(email || 'No registrado');
        $('#modal-notificar-estado').text(estado);
        $('#input-modal-mensaje').val('');
        const urlBase = $table.data('url-notificar') || '/solicitud-vpn/notificar/0/';
        $('#form-notificar-solicitante').attr('action', urlBase.replace('0', id).replace(/\/0\/?$/, `/${id}/`));

        const modal = new bootstrap.Modal(document.getElementById('modalNotificar'));
        modal.show();
    });

    $(document).on('click', '.btn-eliminar-modal', function () {
        const id = $(this).data('sol-id');
        const folio = $(this).data('sol-folio');

        $('#modal-eliminar-folio').text(folio);
        const urlBase = $table.data('url-eliminar') || '/solicitud-vpn/eliminar/0/';
        $('#form-eliminar-solicitud').attr('action', urlBase.replace('0', id).replace(/\/0\/?$/, `/${id}/`));

        const modal = new bootstrap.Modal(document.getElementById('modalEliminar'));
        modal.show();
    });

    // Auto-recarga cada 3 minutos
    setInterval(function () {
        if (table) {
            table.ajax.reload(null, false);
        }
    }, 180000);
});
