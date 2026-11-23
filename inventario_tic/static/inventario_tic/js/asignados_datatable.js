document.addEventListener('DOMContentLoaded', function () {
    const tableEl = document.getElementById('asignadosTable');
    if (!tableEl) return;
    const text = DataTable.render.text();
    const exportOptions = {columns: ':visible', modifier: {selected: null}};

    new DataTable(tableEl, {
        paging: true,
        processing: true,
        responsive: true,
        serverSide: true,
        pageLength: 10,
        lengthMenu: [10, 25, 50, 100],
        keyTable: true,
        order: [[0, 'asc']],
        select: {style: 'single'},
        ajax: {
            url: tableEl.dataset.url,
            type: 'POST',
            headers: {'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''},
            data: {action: 'search'},
            dataSrc: 'data'
        },
        columns: [
            {data: 'col_funcionario', render: text},
            {data: 'col_destino', render: text},
            {data: 'col_tipo', render: text},
            {data: 'col_descripcion', render: text, defaultContent: ''},
            {data: 'col_inventario', render: text},
            {data: 'col_serie', render: text},
            {data: 'col_cantidad', className: 'text-center'}
        ],
        buttons: {
            dom: {button: {className: 'btn btn-sm btn-outline-secondary'}},
            buttons: [
                {extend: 'copy', text: '<i class="bi bi-copy"></i> Copiar', exportOptions},
                {extend: 'csv', text: '<i class="bi bi-filetype-csv"></i> CSV', exportOptions},
                {extend: 'excel', text: '<i class="bi bi-file-earmark-excel"></i> XLS', exportOptions},
                {extend: 'pdf', text: '<i class="bi bi-file-earmark-pdf"></i> PDF', exportOptions, orientation: 'landscape'},
                {extend: 'print', text: '<i class="bi bi-printer"></i> Imprimir', exportOptions},
                {text: '<i class="bi bi-arrow-clockwise"></i> Recargar', action: (event, dt) => dt.ajax.reload(null, false)},
                {text: '<i class="bi bi-eraser"></i> Limpiar', action: (event, dt) => dt.search('').columns().search('').order([[0, 'asc']]).draw()}
            ]
        },
        layout: {
            topStart: 'pageLength', top: 'buttons', topEnd: 'search',
            bottomStart: 'info', bottomEnd: 'paging'
        },
        language: {
            url: 'https://cdn.datatables.net/plug-ins/2.3.6/i18n/es-ES.json',
            processing: 'Cargando datos, por favor espera...'
        }
    });
});
