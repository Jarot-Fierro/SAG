document.addEventListener('DOMContentLoaded', function () {
    const tableEl = document.getElementById('estacionesTable');
    if (!tableEl) return;
    const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[char]);
    const exportOptions = {columns: [0, 1, 2, 3], modifier: {selected: null}};

    new DataTable(tableEl, {
        paging: true,
        processing: true,
        responsive: true,
        serverSide: true,
        pageLength: 10,
        lengthMenu: [10, 25, 50, 100],
        keyTable: true,
        order: [[0, 'desc']],
        select: {style: 'single', selector: 'td:not(:nth-child(5))'},
        ajax: {
            url: tableEl.dataset.url,
            type: 'POST',
            headers: {'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''},
            data: {action: 'search'},
            dataSrc: 'data'
        },
        columns: [
            {data: 'id'},
            {data: 'fecha', render: escapeHtml},
            {data: 'establecimiento', render: escapeHtml},
            {data: 'responsable', render: escapeHtml},
            {
                data: null, orderable: false, searchable: false, className: 'text-center',
                render: function (data, type, row) {
                    if (type !== 'display') return '';
                    return `<div class="d-flex gap-1 justify-content-center">
                        <a href="${escapeHtml(row.detalle_url)}" class="btn btn-sm btn-outline-primary"
                           title="Ver entrega" aria-label="Ver entrega"><i class="bi bi-eye"></i></a>
                        <a href="${escapeHtml(row.acta_url)}" class="btn btn-sm btn-outline-danger"
                           target="_blank" rel="noopener noreferrer" title="Acta conjunta" aria-label="Acta conjunta">
                           <i class="bi bi-file-earmark-pdf"></i></a>
                    </div>`;
                }
            }
        ],
        buttons: {
            dom: {button: {className: 'btn btn-sm btn-outline-secondary'}},
            buttons: [
                {extend: 'copy', text: '<i class="bi bi-copy"></i> Copiar', exportOptions},
                {extend: 'csv', text: '<i class="bi bi-filetype-csv"></i> CSV', exportOptions},
                {extend: 'excel', text: '<i class="bi bi-file-earmark-excel"></i> XLS', exportOptions},
                {extend: 'pdf', text: '<i class="bi bi-file-earmark-pdf"></i> PDF', exportOptions},
                {extend: 'print', text: '<i class="bi bi-printer"></i> Imprimir', exportOptions},
                {
                    text: '<i class="bi bi-arrow-clockwise"></i> Recargar',
                    action: (event, dt) => dt.ajax.reload(null, false)
                },
                {
                    text: '<i class="bi bi-eraser"></i> Limpiar',
                    action: (event, dt) => dt.search('').columns().search('').order([[0, 'desc']]).draw()
                }
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
