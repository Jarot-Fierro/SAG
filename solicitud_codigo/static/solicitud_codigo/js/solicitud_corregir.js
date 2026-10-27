/**
 * ============================================================================
 * Script de Formulario de Corrección de Solicitud de Código (solicitud_codigo)
 * ============================================================================
 * Gestiona la carga en cascada de Subáreas según Área, y la búsqueda de
 * coincidencias en tiempo real en la Maestra de Códigos SISSA durante la corrección.
 */

document.addEventListener('DOMContentLoaded', function () {
    const areaSelect = $('#id_area');
    const subareaSelect = $('#id_subarea');
    const productoInput = $('#id_producto_base');
    const searchInput = $('#searchHelperInput');
    const searchList = $('#searchHelperList');
    const searchEmpty = $('#searchHelperEmpty');
    const searchLoading = $('#searchLoading');
    const matchBadge = $('#matchBadgeCount');

    // URLs API desde variables globales o data attributes
    const urlApiSubareas = (typeof urlSubareas !== 'undefined' ? urlSubareas : '/solicitud-codigo/api/subareas/');
    const urlApiCoincidencias = (typeof urlCoincidencias !== 'undefined' ? urlCoincidencias : '/solicitud-codigo/api/buscar-coincidencias/');

    // Guardar subárea actual seleccionada inicialmente (para re-selección tras carga)
    const initialSubareaId = subareaSelect.val();

    // 1. Carga en cascada de Subáreas según Área
    areaSelect.on('change', function () {
        const areaId = $(this).val();
        subareaSelect.empty().append('<option value="">Cargando subáreas...</option>');

        if (!areaId) {
            subareaSelect.empty().append('<option value="">Seleccione una subárea (opcional)</option>');
            return;
        }

        $.getJSON(urlApiSubareas, {area_id: areaId})
            .done(function (data) {
                subareaSelect.empty().append('<option value="">Seleccione una subárea (opcional)</option>');
                if (data.subareas && data.subareas.length > 0) {
                    $.each(data.subareas, function (idx, item) {
                        const opt = $('<option>', {
                            value: item.id,
                            text: item.nombre + (item.codigo ? ' (' + item.codigo + ')' : '')
                        });
                        if (String(item.id) === String(initialSubareaId)) {
                            opt.prop('selected', true);
                        }
                        subareaSelect.append(opt);
                    });
                }
            })
            .fail(function () {
                subareaSelect.empty().append('<option value="">Error al cargar subáreas</option>');
            });
    });

    // 2. Búsqueda de Coincidencias en Maestra SISSA / Productos
    let searchTimeout = null;

    function runSearch(term) {
        if (!term || term.trim().length < 2) {
            searchList.addClass('d-none').empty();
            searchEmpty.removeClass('d-none').html('<i class="bi bi-journal-text fs-2 d-block mb-1 text-secondary opacity-50"></i>Escriba al menos 2 letras para consultar coincidencias.');
            matchBadge.text('0 coincidencias').removeClass('bg-warning bg-success').addClass('bg-info text-dark');
            return;
        }

        searchLoading.removeClass('d-none');
        searchEmpty.addClass('d-none');

        const areaId = areaSelect.val();

        $.getJSON(urlApiCoincidencias, {q: term, area_id: areaId})
            .done(function (data) {
                searchLoading.addClass('d-none');
                searchList.empty();

                if (data.coincidencias && data.coincidencias.length > 0) {
                    matchBadge.text(data.total + ' coincidencia(s)').removeClass('bg-info text-dark').addClass('bg-warning text-dark');
                    searchList.removeClass('d-none');
                    searchEmpty.addClass('d-none');

                    $.each(data.coincidencias, function (idx, item) {
                        const li = $(`
                            <li class="list-group-item p-2 border-bottom">
                                <div class="d-flex justify-content-between align-items-start">
                                    <span class="badge bg-secondary font-monospace">${item.codigo}</span>
                                    <span class="badge bg-light text-dark border">${item.origen}</span>
                                </div>
                                <div class="fw-bold mt-1 text-dark">${item.nombre}</div>
                                <div class="text-muted small">Presentación: ${item.presentacion}</div>
                                <div class="text-secondary small">Área/Catálogo: ${item.area}</div>
                            </li>
                        `);
                        searchList.append(li);
                    });
                } else {
                    matchBadge.text('0 coincidencias').removeClass('bg-warning text-dark').addClass('bg-success text-white');
                    searchList.addClass('d-none');
                    searchEmpty.removeClass('d-none').html('<i class="bi bi-check-circle-fill text-success fs-3 d-block mb-1"></i>No se encontraron códigos coincidentes. Puede proceder con la solicitud.');
                }
            })
            .fail(function () {
                searchLoading.addClass('d-none');
                searchEmpty.removeClass('d-none').text('Error al realizar la consulta.');
            });
    }

    productoInput.on('input', function () {
        const val = $(this).val();
        searchInput.val(val);
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function () {
            runSearch(val);
        }, 450);
    });

    $('#btnBuscarCoincidencias').on('click', function () {
        const val = productoInput.val();
        searchInput.val(val);
        runSearch(val);
    });

    $('#btnRunSearch').on('click', function () {
        runSearch(searchInput.val());
    });

    searchInput.on('keyup', function (e) {
        if (e.key === 'Enter') {
            runSearch($(this).val());
        }
    });

    // Si ya tiene valor al cargar la vista, ejecutar una búsqueda inicial
    const initialProductVal = productoInput.val();
    if (initialProductVal && initialProductVal.trim().length >= 2) {
        searchInput.val(initialProductVal);
        runSearch(initialProductVal);
    }
});
