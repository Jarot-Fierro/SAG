/**
 * Configuración global de DataTables
 * Compatible con Bootstrap 5 y procesamiento Server-Side.
 */
const DataTableDefaults = {
    processing: true,
    serverSide: true,

    // Paginación
    pageLength: 10,
    lengthMenu: [10, 25, 50, 100],
    paging: true,
    info: true,

    // Búsqueda
    searching: true,
    searchDelay: 400,

    // Rendimiento
    deferRender: true,

    // Orden inicial
    order: [[0, 'asc']],

    // ColumnControl
    columnControl: ['order', 'searchDropdown'],

    // Selección múltiple de filas
    select: {
        style: 'multi',
        selector: 'td:first-child'
    },

    // Idioma español
    language: {
        emptyTable: 'No hay datos disponibles en la tabla',
        info: 'Mostrando _START_ a _END_ de _TOTAL_ registros',
        infoEmpty: 'Mostrando 0 a 0 de 0 registros',
        infoFiltered: '(filtrado de _MAX_ registros totales)',
        lengthMenu: 'Mostrar _MENU_ registros',
        loadingRecords: 'Cargando...',
        processing: 'Procesando...',
        search: 'Buscar:',
        searchPlaceholder: 'Buscar registros...',
        zeroRecords: 'No se encontraron resultados',
        paginate: {
            first: 'Primero',
            last: 'Último',
            next: 'Siguiente',
            previous: 'Anterior'
        },
        select: {
            rows: {
                _: '%d filas seleccionadas',
                0: '',
                1: '1 fila seleccionada'
            }
        },
        columnControl: {
            dropdown: 'Opciones de columna',
            order: 'Ordenar columna',
            orderAsc: 'Ordenar ascendente',
            orderDesc: 'Ordenar descendente',
            orderClear: 'Limpiar orden',
            orderAddAsc: 'Agregar orden ascendente',
            orderAddDesc: 'Agregar orden descendente',
            orderRemove: 'Quitar orden',
            search: 'Buscar en columna',
            searchClear: 'Limpiar búsqueda',
            searchPlaceholder: 'Buscar...',
            searchButton: 'Buscar',
            searchClearButton: 'Limpiar',
            searchDropdown: 'Buscar en columna',
            colVis: 'Visibilidad de columnas',
            colVisDropdown: 'Visibilidad de columnas',
            list: {
                all: 'Seleccionar todos',
                none: 'Deseleccionar todos',
                empty: 'Vacío',
                search: 'Buscar opción...'
            },
            search: {
                text: {
                    contains: 'Contiene',
                    notContains: 'No contiene',
                    equal: 'Igual a',
                    notEqual: 'No es igual a',
                    starts: 'Empieza con',
                    ends: 'Termina con',
                    empty: 'Vacío',
                    notEmpty: 'No está vacío'
                },
                num: {
                    equal: 'Igual a',
                    notEqual: 'No es igual a',
                    greater: 'Mayor que',
                    greaterOrEqual: 'Mayor o igual que',
                    less: 'Menor que',
                    lessOrEqual: 'Menor o igual que',
                    empty: 'Vacío',
                    notEmpty: 'No está vacío'
                },
                date: {
                    equal: 'Igual a',
                    notEqual: 'No es igual a',
                    before: 'Antes de',
                    after: 'Después de',
                    empty: 'Vacío',
                    notEmpty: 'No está vacío'
                }
            }
        }
    }
};


/**
 * Inicializador reutilizable de DataTables.
 *
 * Parámetros:
 * selector      : selector CSS de la tabla.
 * ajaxUrl       : URL del endpoint Django.
 * columns       : definición de columnas.
 * order         : orden inicial.
 * columnControl : configuración específica de ColumnControl.
 * columnDefs    : configuración adicional por columna.
 * extraConfig   : opciones adicionales de DataTables.
 */
function initDataTable({
                           selector,
                           ajaxUrl,
                           columns,
                           order = [[0, 'asc']],
                           columnControl,
                           columnDefs,
                           extraConfig = {}
                       }) {
    const customOptions = {
        ajax: {
            url: ajaxUrl,
            type: 'GET'
        },

        columns: columns,
        order: order
    };

    // Permite personalizar ColumnControl por tabla.
    if (columnControl !== undefined) {
        customOptions.columnControl = columnControl;
    }

    // Permite definir opciones específicas por columna.
    if (columnDefs !== undefined) {
        customOptions.columnDefs = columnDefs;
    }

    // Combina las opciones globales con las específicas.
    const config = $.extend(
        true,
        {},
        DataTableDefaults,
        customOptions,
        extraConfig
    );

    return $(selector).DataTable(config);
}
