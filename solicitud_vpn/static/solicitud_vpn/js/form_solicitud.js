/**
 * Lógica del formulario de Solicitud de Acceso VPN
 */
$(document).ready(function () {
    const $container = $('#contenedor-filas-beneficiarios');
    const defaultEstablecimiento = $('#vpn-form-container').data('default-establecimiento') || '';
    const funcionarioApiUrlBase = $('#vpn-form-container').data('api-funcionario-url') || '/solicitud-vpn/api/funcionario/0/';

    // Formateo de RUT
    function formatearRut(rut) {
        if (!rut) return '';
        let valor = rut.replace(/[^0-9kK]/g, '').toUpperCase();
        if (valor.length <= 1) return valor;
        let cuerpo = valor.slice(0, -1);
        let dv = valor.slice(-1);
        let puntos = '';
        while (cuerpo.length > 3) {
            puntos = '.' + cuerpo.slice(-3) + puntos;
            cuerpo = cuerpo.slice(0, -3);
        }
        return cuerpo + puntos + '-' + dv;
    }

    $(document).on('blur', '.rut-input', function () {
        $(this).val(formatearRut($(this).val()));
    });

    // BENEFICIARIOS FORMSET DYNAMIC MANAGEMENT
    function actualizarNumeracionBeneficiarios() {
        let visibleIdx = 1;
        $('#contenedor-filas-beneficiarios tr.fila-beneficiario').each(function () {
            if ($(this).is(':visible')) {
                $(this).find('.col-numero-ben').text(visibleIdx);
                visibleIdx++;
            }
        });
    }

    function initSelect2Beneficiarios(context) {
        $(context).find('.select2-funcionario').each(function () {
            if (!$(this).hasClass("select2-hidden-accessible")) {
                $(this).select2({
                    theme: 'bootstrap-5',
                    placeholder: '-- Seleccionar funcionario --',
                    allowClear: true,
                    width: '100%'
                });
            }
        });
    }

    initSelect2Beneficiarios(document);

    $('#btn-agregar-beneficiario').on('click', function (e) {
        e.preventDefault();
        const totalFormsInput = $('#id_beneficiarios-TOTAL_FORMS');
        const totalForms = parseInt(totalFormsInput.val()) || 0;

        const templateHtml = $('#plantilla-fila-beneficiario').html();
        const nuevaFilaHtml = templateHtml.replace(/__prefix__/g, totalForms);
        const $nuevaFila = $(nuevaFilaHtml);

        if (defaultEstablecimiento) {
            $nuevaFila.find('.input-establecimiento').val(defaultEstablecimiento);
        }

        $('#contenedor-filas-beneficiarios').append($nuevaFila);
        totalFormsInput.val(totalForms + 1);

        initSelect2Beneficiarios($nuevaFila);
        actualizarNumeracionBeneficiarios();
    });

    $(document).on('click', '.btn-eliminar-beneficiario', function (e) {
        e.preventDefault();
        const $fila = $(this).closest('tr.fila-beneficiario');
        const filasVisibles = $('#contenedor-filas-beneficiarios tr.fila-beneficiario:visible').length;

        if (filasVisibles <= 1) {
            alert('Debe conservar al menos un beneficiario en la solicitud.');
            return;
        }

        $fila.find('input[name$="-DELETE"]').prop('checked', true);
        $fila.hide();
        actualizarNumeracionBeneficiarios();
    });

    $(document).on('change select2:select', '.select-func-existente', function () {
        const funcId = $(this).val();
        const $fila = $(this).closest('tr.fila-beneficiario');

        if (funcId) {
            const endpoint = funcionarioApiUrlBase.replace('0', funcId).replace(/\/0\/?$/, `/${funcId}/`);
            $.ajax({
                url: endpoint,
                type: 'GET',
                dataType: 'json',
                success: function (response) {
                    if (response && response.status === 'ok') {
                        const d = response.data;
                        $fila.find('.input-rut').val(formatearRut(d.rut || '')).trigger('input');
                        $fila.find('.input-nombres').val(d.nombres || '').trigger('input');
                        $fila.find('.input-apellidos').val(d.apellidos || '');
                        $fila.find('.input-nombre-completo').val(d.nombre_completo || '');
                        $fila.find('.input-establecimiento').val(d.establecimiento || defaultEstablecimiento);
                        $fila.find('.input-cargo').val(d.cargo || '');
                        $fila.find('.input-email').val(d.email || '');
                        $fila.find('.input-telefono').val(d.telefono || '');
                    }
                },
                error: function (err) {
                    console.error('Error obteniendo datos del funcionario:', err);
                }
            });
        }
    });

    // ACCESOS FORMSET DYNAMIC MANAGEMENT
    function actualizarNumeracionAccesos() {
        let visibleIdx = 1;
        $('#contenedor-filas-accesos tr.fila-acceso').each(function () {
            if ($(this).is(':visible')) {
                $(this).find('.col-numero-acc').text(visibleIdx);
                visibleIdx++;
            }
        });
    }

    function initSelect2Accesos(context) {
        $(context).find('.select2-acceso').each(function () {
            if (!$(this).hasClass("select2-hidden-accessible")) {
                $(this).select2({
                    theme: 'bootstrap-5',
                    placeholder: '-- Seleccionar Plataforma / Sistema --',
                    allowClear: true,
                    width: '100%'
                });
            }
        });
    }

    initSelect2Accesos(document);

    $('#btn-agregar-acceso').on('click', function (e) {
        e.preventDefault();
        const totalFormsInput = $('#id_accesos-TOTAL_FORMS');
        const totalForms = parseInt(totalFormsInput.val()) || 0;

        const templateHtml = $('#plantilla-fila-acceso').html();
        const nuevaFilaHtml = templateHtml.replace(/__prefix__/g, totalForms);
        const $nuevaFila = $(nuevaFilaHtml);

        $('#contenedor-filas-accesos').append($nuevaFila);
        totalFormsInput.val(totalForms + 1);

        initSelect2Accesos($nuevaFila);
        actualizarNumeracionAccesos();
    });

    $(document).on('click', '.btn-eliminar-acceso', function (e) {
        e.preventDefault();
        const $fila = $(this).closest('tr.fila-acceso');
        const filasVisibles = $('#contenedor-filas-accesos tr.fila-acceso:visible').length;

        if (filasVisibles <= 1) {
            alert('Debe conservar al menos un acceso en la solicitud.');
            return;
        }

        $fila.find('input[name$="-DELETE"]').prop('checked', true);
        $fila.hide();
        actualizarNumeracionAccesos();
    });

    $(document).on('change select2:select', '.select-acceso-catalogo', function () {
        const $option = $(this).find('option:selected');
        const $fila = $(this).closest('tr.fila-acceso');
        const ip = $option.data('ip') || '';
        $fila.find('.input-ip-preview').val(ip);
    });

    // WIZARD NAVEGACIÓN
    let currentStep = 1;
    const totalSteps = 4;

    function showStep(stepNumber) {
        $('.wizard-step-content').addClass('d-none');
        $(`#step-${stepNumber}-content`).removeClass('d-none');

        $('.wizard-step').removeClass('active');
        $(`.wizard-step[data-step="${stepNumber}"]`).addClass('active');

        if (stepNumber === 1) {
            $('#btn-wizard-prev').addClass('d-none');
        } else {
            $('#btn-wizard-prev').removeClass('d-none');
        }

        if (stepNumber === totalSteps) {
            $('#btn-wizard-next').addClass('d-none');
            $('#btn-wizard-submit').removeClass('d-none');
            actualizarResumen();
        } else {
            $('#btn-wizard-next').removeClass('d-none');
            $('#btn-wizard-submit').addClass('d-none');
        }

        currentStep = stepNumber;
        $('html, body').animate({
            scrollTop: $('#form-solicitud-vpn').offset().top - 80
        }, 200);
    }

    function validarPaso(stepNumber) {
        let valid = true;
        if (stepNumber === 1) {
            if (!$('#id_tecnico_nombre').val().trim()) valid = false;
            if (!$('#id_tecnico_rut').val().trim()) valid = false;
            if (!$('#id_tecnico_email').val().trim()) valid = false;
        } else if (stepNumber === 2) {
            if (!$('#id_accion').val()) valid = false;
        } else if (stepNumber === 3) {
            const benVisibles = $('#contenedor-filas-beneficiarios tr.fila-beneficiario:visible').length;
            if (benVisibles === 0) valid = false;
        }
        return valid;
    }

    $('#btn-wizard-next').on('click', function () {
        if (validarPaso(currentStep)) {
            if (currentStep < totalSteps) {
                showStep(currentStep + 1);
            }
        } else {
            alert('Por favor complete los campos obligatorios antes de continuar.');
        }
    });

    $('#btn-wizard-prev').on('click', function () {
        if (currentStep > 1) {
            showStep(currentStep - 1);
        }
    });

    $('.wizard-step').on('click', function () {
        const step = $(this).data('step');
        if (step < currentStep || validarPaso(currentStep)) {
            showStep(step);
        }
    });

    function actualizarResumen() {
        $('#resumen_tecnico_nombre').text($('#id_tecnico_nombre').val() || '-');
        $('#resumen_tecnico_rut').text($('#id_tecnico_rut').val() || '-');
        $('#resumen_tecnico_establecimiento').text($('#id_tecnico_establecimiento').val() || '-');
        $('#resumen_tecnico_cargo').text($('#id_tecnico_cargo').val() || '-');
        $('#resumen_tecnico_email').text($('#id_tecnico_email').val() || '-');
        $('#resumen_tecnico_telefono').text($('#id_tecnico_telefono').val() || '-');

        const accionText = $('#id_accion option:selected').text();
        $('#resumen_accion').text(accionText || '-');
        $('#resumen_grupo_vpn').text($('#id_grupo_vpn option:selected').text() || 'N/A');
        $('#resumen_fecha_expiracion').text($('#id_fecha_expiracion').val() || 'Indefinida');
        $('#resumen_timeout_vpn').text($('#id_timeout_vpn option:selected').text() || '1 hora');
        $('#resumen_observacion').text($('#id_observacion').val() || 'Sin observaciones');

        let tablaBenHtml = '<table class="table table-sm table-bordered mb-0"><thead><tr class="table-light"><th>#</th><th>Nombre</th><th>RUT</th><th>Establecimiento</th><th>Cargo</th></tr></thead><tbody>';
        let bCount = 0;
        $('#contenedor-filas-beneficiarios tr.fila-beneficiario:visible').each(function (idx) {
            bCount++;
            const nom = $(this).find('.input-nombres').val() + ' ' + $(this).find('.input-apellidos').val();
            const rut = $(this).find('.input-rut').val();
            const est = $(this).find('.input-establecimiento').val();
            const car = $(this).find('.input-cargo').val();
            tablaBenHtml += `<tr><td>${bCount}</td><td>${nom.trim() || '-'}</td><td>${rut || '-'}</td><td>${est || '-'}</td><td>${car || '-'}</td></tr>`;
        });
        tablaBenHtml += '</tbody></table>';
        $('#resumen_tabla_beneficiarios_container').html(tablaBenHtml);

        let tablaAccHtml = '<table class="table table-sm table-bordered mb-0"><thead><tr class="table-light"><th>#</th><th>Plataforma / Sistema</th><th>Dirección IP / Segmento</th></tr></thead><tbody>';
        let aCount = 0;
        $('#contenedor-filas-accesos tr.fila-acceso:visible').each(function (idx) {
            aCount++;
            const plat = $(this).find('.select-acceso-catalogo option:selected').text();
            const ip = $(this).find('.input-ip-preview').val();
            tablaAccHtml += `<tr><td>${aCount}</td><td>${plat || '-'}</td><td><code>${ip || '-'}</code></td></tr>`;
        });
        tablaAccHtml += '</tbody></table>';
        $('#resumen_tabla_accesos_container').html(tablaAccHtml);
    }
});
