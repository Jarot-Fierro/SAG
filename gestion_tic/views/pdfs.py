from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from weasyprint import HTML

from gestion_tic.models import JefeTic, MovimientoActivo


@login_required
def generar_acta_activo(request, pk):
    establecimiento = getattr(request.user, 'establecimiento', None)
    filter_kwargs = {'id': pk}
    if establecimiento:
        filter_kwargs['establecimiento'] = establecimiento

    ultimo_movimiento = get_object_or_404(
        MovimientoActivo.objects.select_related(
            'activo', 'activo__tipo', 'activo__marca', 'activo__modelo', 'activo__establecimiento',
            'funcionario', 'funcionario__unidad_organizacional',
            'unidad_organizacional', 'ip', 'tipo_movimiento', 'jefe_firmante'
        ).prefetch_related('accesorios'),
        **filter_kwargs
    )

    activo = ultimo_movimiento.activo

    # Si existe una copia histórica (snapshot_acta), la utilizamos como fuente de verdad
    if ultimo_movimiento.snapshot_acta:
        snapshot = ultimo_movimiento.snapshot_acta
        activo_info = snapshot.get('activo', {})
        caracteristicas = activo_info.get('caracteristicas', [])
        accesorios = snapshot.get('accesorios', [])
        ip_str = snapshot.get('ip')
        tipo_movimiento_nombre = snapshot.get('tipo_movimiento')
        receptor_nombre = snapshot.get('nombre_completo')
        receptor_depto = snapshot.get('departamento')
        jefe_firmante_info = snapshot.get('jefe_firmante')
        fecha_movimiento = snapshot.get('fecha_movimiento')
        fecha_recepcion = snapshot.get('fecha_recepcion')
        observacion = snapshot.get('observacion')
        establecimiento_nombre = activo_info.get('establecimiento')
    else:
        # Fallback dinámico para movimientos históricos o pendientes
        caracteristicas_qs = activo.caracteristicas.select_related('campo').all().order_by('campo__orden',
                                                                                           'campo__nombre') if activo else []
        caracteristicas = [{'campo': c.campo.nombre, 'valor': c.valor} for c in caracteristicas_qs]

        accesorios_qs = ultimo_movimiento.accesorios.all().order_by('id')
        accesorios = [{
            'nombre': acc.nombre or (acc.accesorio.nombre if acc.accesorio else ''),
            'cantidad': acc.cantidad,
            'observacion': acc.observacion or ''
        } for acc in accesorios_qs]

        ip_str = ultimo_movimiento.ip.ip if ultimo_movimiento.ip else None
        tipo_movimiento_nombre = ultimo_movimiento.tipo_movimiento.nombre if ultimo_movimiento.tipo_movimiento else ''

        # Nombre del receptor: nuevo flujo o respaldo con funcionario histórico
        receptor_nombre = ultimo_movimiento.nombre_completo
        if not receptor_nombre and ultimo_movimiento.funcionario:
            if hasattr(ultimo_movimiento.funcionario, 'nombre') and ultimo_movimiento.funcionario.nombre:
                receptor_nombre = ultimo_movimiento.funcionario.nombre
            else:
                parts = [ultimo_movimiento.funcionario.nombres or '', ultimo_movimiento.funcionario.apellidos or '']
                receptor_nombre = ' '.join(p for p in parts if p).strip()

        # Departamento del receptor
        receptor_depto = ultimo_movimiento.departamento
        if not receptor_depto and ultimo_movimiento.unidad_organizacional:
            receptor_depto = ultimo_movimiento.unidad_organizacional.nombre
        elif not receptor_depto and ultimo_movimiento.funcionario and ultimo_movimiento.funcionario.unidad_organizacional:
            receptor_depto = ultimo_movimiento.funcionario.unidad_organizacional.nombre

        # Jefe firmante
        if ultimo_movimiento.jefe_firmante:
            jefe_firmante_info = {
                'nombre': ultimo_movimiento.jefe_firmante.nombre,
                'posicion': ultimo_movimiento.jefe_firmante.posicion,
            }
        else:
            jefe_tic_fallback = JefeTic.objects.filter(
                establecimiento=activo.establecimiento if activo else establecimiento,
                is_active=True
            ).first()
            jefe_firmante_info = {
                'nombre': jefe_tic_fallback.nombre if jefe_tic_fallback else '',
                'posicion': jefe_tic_fallback.posicion if jefe_tic_fallback else '',
            } if jefe_tic_fallback else None

        fecha_movimiento = ultimo_movimiento.created_at.strftime(
            '%d/%m/%Y %H:%M') if ultimo_movimiento.created_at else ''
        fecha_recepcion = ultimo_movimiento.fecha_recepcion.strftime(
            '%d/%m/%Y %H:%M') if ultimo_movimiento.fecha_recepcion else ''
        observacion = ultimo_movimiento.observacion
        establecimiento_nombre = activo.establecimiento.nombre if (activo and activo.establecimiento) else (
            establecimiento.nombre if establecimiento else '')

        activo_info = {
            'codigo_barra': activo.codigo_barra if activo else '',
            'tipo': activo.tipo.nombre if (activo and activo.tipo) else '',
            'marca': activo.marca.nombre if (activo and activo.marca) else '',
            'modelo': activo.modelo.nombre if (activo and activo.modelo) else '',
            'serie': activo.serie if activo else '',
            'observacion': activo.observacion if activo else '',
        }

    contexto = {
        'fecha_emision': datetime.now().strftime('%d/%m/%Y'),
        'hora_emision': datetime.now().strftime('%H:%M:%S'),
        'activo': activo,
        'activo_info': activo_info,
        'ultimo_movimiento': ultimo_movimiento,
        'caracteristicas': caracteristicas,
        'accesorios': accesorios,
        'ip_str': ip_str,
        'tipo_movimiento_nombre': tipo_movimiento_nombre,
        'receptor_nombre': receptor_nombre,
        'receptor_depto': receptor_depto,
        'jefe_firmante_info': jefe_firmante_info,
        'fecha_movimiento': fecha_movimiento,
        'fecha_recepcion': fecha_recepcion,
        'observacion_entrega': observacion,
        'es_recepcionado': ultimo_movimiento.recepcionado,
        'requiere_recepcion': ultimo_movimiento.tipo_movimiento.requiere_recepcion if ultimo_movimiento.tipo_movimiento else False,
        'establecimiento_nombre': establecimiento_nombre,
    }

    html_string = render_to_string('gestion_tic/pdfs/activo_acta.html', contexto, request=request)

    # Crear respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    codigo_ref = activo_info.get('codigo_barra') or (activo.codigo_barra if activo else pk)
    response['Content-Disposition'] = f'inline; filename="acta_{codigo_ref}.pdf"'

    # Generar PDF
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    return response


@login_required
def generar_acta_activo_personalizada(request):
    establecimiento = getattr(request.user, 'establecimiento', None)
    contexto = {
        'title': 'Acta de Entrega Personalizada',
        'fecha': datetime.now().strftime('%d/%m/%Y'),
        'hora': datetime.now().strftime('%H:%M'),
        'establecimiento': establecimiento,
    }
    return render(request, 'gestion_tic/pdfs/acta_personalizada.html', contexto)
