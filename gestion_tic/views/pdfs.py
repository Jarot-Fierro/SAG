from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from weasyprint import HTML

from gestion_tic.models import JefeTic, MovimientoActivo


@login_required
def generar_acta_activo(request, pk):
    # Obtener el movimiento específico
    # Esto asegura que el acta sea exactamente lo que se entregó en ese momento
    ultimo_movimiento = get_object_or_404(
        MovimientoActivo.objects.select_related(
            'activo', 'activo__tipo', 'activo__marca', 'activo__modelo', 'activo__establecimiento',
            'funcionario', 'ip', 'tipo_movimiento'
        ),
        id=pk
    )

    activo = ultimo_movimiento.activo

    # Características del activo
    caracteristicas = activo.caracteristicas.select_related('campo').all().order_by('campo__orden')

    # Jefe TIC del establecimiento
    jefe_tic = JefeTic.objects.filter(establecimiento=activo.establecimiento, is_active=True).first()

    contexto = {
        'fecha': datetime.now().strftime('%d/%m/%Y'),
        'hora': datetime.now().strftime('%H:%M:%S'),
        'activo': activo,
        'ultimo_movimiento': ultimo_movimiento,
        'caracteristicas': caracteristicas,
        'jefe_tic': jefe_tic,
    }

    html_string = render_to_string('gestion_tic/pdfs/activo_acta.html', contexto, request=request)

    # Crear respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="acta_{activo.codigo_barra}.pdf"'

    # Generar PDF
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    return response
