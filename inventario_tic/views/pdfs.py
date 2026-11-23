import base64
from pathlib import Path

from django.contrib.staticfiles import finders
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from .celulares import puede_generar_acta_celular
from ..models.celulares import Celular
from ..models.monitores import Monitor
from ..models.computadores import Computador
from .computadores import puede_generar_acta_computador
from .monitores import puede_generar_acta_monitor
from ..models.impresoras import Impresora
from .impresoras import puede_generar_acta_impresora


@login_required
def generar_acta_celulares(request, pk):
    queryset = Celular.objects.filter(is_active=True).select_related(
        'marca', 'modelo', 'propietario', 'establecimiento_mantenedor', 'jefe_entrega', 'responsable',
    )
    if not request.user.is_superuser:
        establecimiento_id = getattr(request.user, 'establecimiento_id', None)
        queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
    celular = get_object_or_404(queryset, pk=pk)
    establecimiento_nombre = (
        celular.establecimiento_mantenedor.nombre if celular.establecimiento_mantenedor else ''
    )
    if not puede_generar_acta_celular(celular.responsable.nombre if celular.responsable else '', establecimiento_nombre):
        return HttpResponseBadRequest('El celular debe tener establecimiento y responsable para generar el acta.')

    fecha_emision = timezone.now()
    if timezone.is_aware(fecha_emision):
        fecha_emision = timezone.localtime(fecha_emision)
    contexto = {'celular': celular, 'fecha_emision': fecha_emision}
    html_string = render_to_string('inventario_tic/pdf_acta_celulares.html', contexto, request=request)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="acta_celular_{celular.imei}.pdf"'
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    return response


@login_required
def generar_acta_impresoras(request, pk):
    queryset = Impresora.objects.filter(is_active=True).select_related(
        'marca', 'modelo', 'establecimiento', 'departamento',
    )
    if not request.user.is_superuser:
        establecimiento_id = getattr(request.user, 'establecimiento_id', None)
        queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
    impresora = get_object_or_404(queryset, pk=pk)
    establecimiento_nombre = (
        impresora.establecimiento.nombre if impresora.establecimiento else ''
    )
    if not puede_generar_acta_impresora(
        impresora.departamento.nombre if impresora.departamento else '', establecimiento_nombre,
    ):
        return HttpResponseBadRequest('La impresora debe tener establecimiento y departamento para generar el acta.')

    fecha_emision = timezone.now()
    if timezone.is_aware(fecha_emision):
        fecha_emision = timezone.localtime(fecha_emision)
    contexto = {'impresora': impresora, 'fecha_emision': fecha_emision}
    html_string = render_to_string('inventario_tic/pdf_acta_impresora.html', contexto, request=request)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="acta_impresora_{impresora.numero_serie}.pdf"'
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    return response


@login_required
def generar_acta_monitores(request, pk):
    queryset = Monitor.objects.filter(is_active=True).select_related(
        'marca', 'modelo', 'establecimiento_mantenedor', 'jefe_entrega', 'responsable',
    )
    if not request.user.is_superuser:
        establecimiento_id = getattr(request.user, 'establecimiento_id', None)
        queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
    monitor = get_object_or_404(queryset, pk=pk)
    establecimiento_nombre = (
        monitor.establecimiento_mantenedor.nombre if monitor.establecimiento_mantenedor else ''
    )
    if not puede_generar_acta_monitor(monitor.responsable.nombre if monitor.responsable else '', establecimiento_nombre):
        return HttpResponseBadRequest('El monitor debe tener establecimiento y responsable para generar el acta.')

    fecha_emision = timezone.now()
    if timezone.is_aware(fecha_emision):
        fecha_emision = timezone.localtime(fecha_emision)
    contexto = {'monitor': monitor, 'fecha_emision': fecha_emision}
    logo_path = finders.find('core/media/logo_ssa.png')
    if logo_path:
        contexto['logo_servicio'] = 'data:image/png;base64,' + base64.b64encode(Path(logo_path).read_bytes()).decode('ascii')
    html_string = render_to_string('inventario_tic/pdf_acta_monitores.html', contexto, request=request)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="acta_monitor_{monitor.codigo_inventario}.pdf"'
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    return response




@login_required
def generar_acta_computadores(request, pk):
    queryset = Computador.objects.filter(is_active=True).select_related(
        'marca', 'modelo', 'establecimiento_mantenedor', 'jefe_entrega', 'responsable',
    )
    if not request.user.is_superuser:
        establecimiento_id = getattr(request.user, 'establecimiento_id', None)
        queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
    computador = get_object_or_404(queryset, pk=pk)
    establecimiento_nombre = (
        computador.establecimiento_mantenedor.nombre if computador.establecimiento_mantenedor else ''
    )
    if not puede_generar_acta_computador(computador.responsable.nombre if computador.responsable else '', establecimiento_nombre):
        return HttpResponseBadRequest('El computador debe tener establecimiento y responsable para generar el acta.')

    fecha_emision = timezone.now()
    if timezone.is_aware(fecha_emision):
        fecha_emision = timezone.localtime(fecha_emision)
    contexto = {'computador': computador, 'fecha_emision': fecha_emision}
    logo_path = finders.find('core/media/logo_ssa.png')
    if logo_path:
        contexto['logo_servicio'] = 'data:image/png;base64,' + base64.b64encode(Path(logo_path).read_bytes()).decode('ascii')
    html_string = render_to_string('inventario_tic/pdf_acta_computadores.html', contexto, request=request)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="acta_computador_{computador.codigo_inventario}.pdf"'
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    return response
