import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, DetailView

from core.models.configuracion_correo import ConfiguracionCorreo
from core.models.funcionario import Funcionario
from core.services.email_service import EmailService
from solicitud_correo.forms import (
    SolicitudCorreoForm,
    RevisionDetalleRRHHForm,
    ProcesamientoDetalleTICForm,
    NotificacionFuncionarioForm,
    FiltroSolicitudForm
)
from solicitud_correo.models import SolicitudCorreo, SolicitudCorreoDetalle
from solicitud_correo.permissions import (
    user_is_rrhh,
    user_is_tic,
    user_can_notify,
    RRHHRequiredMixin,
    TICRequiredMixin,
    rrhh_required,
    tic_required
)

logger = logging.getLogger(__name__)

MODULE_NAME = 'Solicitudes de Correo'


def get_estado_badge(estado):
    badges = {
        'BORRADOR': '<span class="badge bg-secondary">Borrador</span>',
        'PENDIENTE_RRHH': '<span class="badge bg-warning text-dark"><i class="bi bi-hourglass-split me-1"></i>Pendiente RR.HH.</span>',
        'EN_REVISION_RRHH': '<span class="badge bg-warning text-dark"><i class="bi bi-person-check me-1"></i>En Revisión RR.HH.</span>',
        'EN_TIC': '<span class="badge bg-info text-dark"><i class="bi bi-send me-1"></i>Enviada a TIC</span>',
        'EN_PROCESO_TIC': '<span class="badge bg-primary"><i class="bi bi-gear-wide-connected me-1"></i>En Proceso TIC</span>',
        'FINALIZADA': '<span class="badge bg-success"><i class="bi bi-check2-all me-1"></i>Finalizada</span>',
        'CANCELADA': '<span class="badge bg-danger"><i class="bi bi-x-circle me-1"></i>Cancelada</span>',
    }
    return badges.get(estado, f'<span class="badge bg-secondary">{escape(estado)}</span>')


class SolicitudMisSolicitudesListView(LoginRequiredMixin, ListView):
    """
    Bandeja de 'Mis Solicitudes': muestra las solicitudes creadas por el usuario conectado.
    """
    model = SolicitudCorreo
    template_name = 'solicitud_correo/mis_solicitudes.html'
    context_object_name = 'solicitudes'
    paginate_by = 15

    def get_queryset(self):
        queryset = SolicitudCorreo.objects.filter(is_active=True).select_related(
            'establecimiento', 'departamento_solicitante', 'usuario_solicitante'
        ).prefetch_related('detalles')

        # Siempre filtrar por establecimiento si el usuario lo tiene y no es superuser
        if hasattr(self.request.user,
                   'establecimiento') and self.request.user.establecimiento and not self.request.user.is_superuser:
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)

        # Si no es superuser ni RR.HH./TIC, solo ve sus propias solicitudes
        if not self.request.user.is_superuser:
            queryset = queryset.filter(usuario_solicitante=self.request.user)

        # Filtros
        form = FiltroSolicitudForm(self.request.GET)
        if form.is_valid():
            numero = form.cleaned_data.get('numero_solicitud')
            estado = form.cleaned_data.get('estado')
            termino = form.cleaned_data.get('funcionario_busqueda')

            if numero:
                queryset = queryset.filter(numero_solicitud__icontains=numero)
            if estado:
                queryset = queryset.filter(estado=estado)
            if termino:
                queryset = queryset.filter(
                    Q(detalles__rut__icontains=termino) |
                    Q(detalles__nombres__icontains=termino) |
                    Q(detalles__apellidos__icontains=termino)
                ).distinct()

        return queryset.order_by('-id')

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('draw'):
            return self.datatables_response(request)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'search' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self.datatables_response(request)
        return JsonResponse({'error': 'Acción no válida'}, status=400)

    def datatables_response(self, request):
        queryset = self.get_queryset()
        params = request.POST if request.method == 'POST' else request.GET

        draw = int(params.get('draw', 1))
        start = max(int(params.get('start', 0)), 0)
        length = int(params.get('length', 10))

        records_total = queryset.count()

        search_value = params.get('search[value]', '').strip()
        if search_value:
            queryset = queryset.filter(
                Q(numero_solicitud__icontains=search_value) |
                Q(departamento_nombre__icontains=search_value) |
                Q(departamento_solicitante__nombre__icontains=search_value) |
                Q(establecimiento__nombre__icontains=search_value) |
                Q(detalles__rut__icontains=search_value) |
                Q(detalles__nombres__icontains=search_value) |
                Q(detalles__apellidos__icontains=search_value)
            ).distinct()

        # Filtros de columna
        depto_filter = params.get('columns[1][search][value]', '').strip()
        if depto_filter:
            queryset = queryset.filter(
                Q(departamento_nombre__icontains=depto_filter) |
                Q(departamento_solicitante__nombre__icontains=depto_filter)
            )

        estado_filter = params.get('columns[3][search][value]', '').strip()
        if estado_filter:
            queryset = queryset.filter(estado=estado_filter)

        records_filtered = queryset.count()

        order_column = params.get('order[0][column]')
        order_dir = params.get('order[0][dir]', 'desc')

        order_map = {
            0: 'numero_solicitud',
            1: 'departamento_nombre',
            3: 'estado',
            4: 'fecha_solicitud',
        }

        if order_column is not None:
            try:
                col_idx = int(order_column)
                field = order_map.get(col_idx)
                if field:
                    if order_dir == 'desc':
                        field = f'-{field}'
                    queryset = queryset.order_by(field)
            except (ValueError, TypeError):
                queryset = queryset.order_by('-id')
        else:
            queryset = queryset.order_by('-id')

        if length != -1:
            queryset = queryset[start:start + min(length, 500)]

        data = [
            self.serialize_solicitud(sol)
            for sol in queryset
        ]

        opciones_estados = [
            {'label': label, 'value': code}
            for code, label in SolicitudCorreo.ESTADOS
        ]

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
            'columnControl': {
                'estado': opciones_estados
            }
        })

    def serialize_solicitud(self, sol):
        detalle_url = reverse('solicitud_correo:detalle', args=[sol.pk])
        historial_url = reverse('solicitud_correo:historial', args=[sol.pk])
        cancelar_url = reverse('solicitud_correo:cancelar', args=[sol.pk])

        badge_func = '<div class="d-flex align-items-center gap-1 flex-wrap">'
        badge_func += f'<span class="badge bg-secondary" title="Total Funcionarios"><i class="bi bi-people me-1"></i>{sol.total_funcionarios}</span>'
        if sol.total_creados > 0:
            badge_func += f'<span class="badge bg-success" title="Cuentas Creadas"><i class="bi bi-check-lg me-1"></i>{sol.total_creados} Creados</span>'
        if sol.total_rechazados > 0:
            badge_func += f'<span class="badge bg-danger" title="Rechazados por RR.HH."><i class="bi bi-x-lg me-1"></i>{sol.total_rechazados} Rechazados</span>'
        badge_func += '</div>'

        acciones = '<div class="btn-group btn-group-sm" role="group">'
        acciones += f'<a href="{detalle_url}" class="btn btn-outline-primary" title="Ver Detalle" data-bs-toggle="tooltip"><i class="bi bi-eye"></i></a>'
        acciones += f'<button type="button" class="btn btn-outline-info" hx-get="{historial_url}" hx-target="#genericModalContent" data-bs-toggle="modal" data-bs-target="#genericModal" title="Historial"><i class="bi bi-clock-history"></i></button>'
        if sol.estado in ['PENDIENTE_RRHH', 'BORRADOR']:
            acciones += f'<form method="post" action="{cancelar_url}" class="d-inline form-cancelar-solicitud" onsubmit="return confirm(\'¿Está seguro de que desea cancelar esta solicitud?\');">'
            acciones += '<button type="submit" class="btn btn-outline-danger" title="Cancelar Solicitud" data-bs-toggle="tooltip"><i class="bi bi-x-circle"></i></button></form>'
        acciones += '</div>'

        depto_texto = escape(sol.departamento_nombre or (
            sol.departamento_solicitante.nombre if sol.departamento_solicitante else "Sin departamento"))
        est_texto = escape(sol.establecimiento.alias or sol.establecimiento.nombre if sol.establecimiento else "")

        folio_str = escape(sol.numero_solicitud or str(sol.id))
        folio_html = f'<a href="{detalle_url}" class="fw-bold text-decoration-none font-monospace text-primary">{folio_str}</a>'

        fecha_html = ""
        if sol.fecha_solicitud:
            fecha_html = f'<div>{sol.fecha_solicitud.strftime("%d/%m/%Y")}</div><small class="text-muted">{sol.fecha_solicitud.strftime("%H:%M")} hrs</small>'

        return {
            'numero_solicitud': folio_html,
            'departamento_solicitante': f'<div>{depto_texto}</div><small class="text-muted">{est_texto}</small>',
            'funcionarios': badge_func,
            'estado': get_estado_badge(sol.estado),
            'fecha_solicitud': fecha_html,
            'acciones': acciones,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mis Solicitudes de Correo'
        context['module_name'] = MODULE_NAME
        context['filter_form'] = FiltroSolicitudForm(self.request.GET)
        context['es_rrhh'] = user_is_rrhh(self.request.user)
        context['es_tic'] = user_is_tic(self.request.user)

        # Contadores rápidos
        user_solicitudes = SolicitudCorreo.objects.filter(is_active=True, usuario_solicitante=self.request.user)
        if hasattr(self.request.user,
                   'establecimiento') and self.request.user.establecimiento and not self.request.user.is_superuser:
            user_solicitudes = user_solicitudes.filter(establecimiento=self.request.user.establecimiento)
        context['total_pendientes'] = user_solicitudes.filter(estado__in=['PENDIENTE_RRHH', 'EN_REVISION_RRHH']).count()
        context['total_en_tic'] = user_solicitudes.filter(estado__in=['EN_TIC', 'EN_PROCESO_TIC']).count()
        context['total_finalizadas'] = user_solicitudes.filter(estado='FINALIZADA').count()
        return context


class SolicitudCorreoCreateView(LoginRequiredMixin, CreateView):
    """
    Creación de una nueva solicitud de correos, permitiendo agregar múltiples funcionarios.
    """
    model = SolicitudCorreo
    form_class = SolicitudCorreoForm
    template_name = 'solicitud_correo/form_solicitud.html'
    success_url = reverse_lazy('solicitud_correo:mis_solicitudes')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nueva Solicitud de Correos Electrónicos'
        context['module_name'] = MODULE_NAME
        context['es_rrhh'] = user_is_rrhh(self.request.user)
        context['es_tic'] = user_is_tic(self.request.user)

        func_qs = Funcionario.objects.filter(is_active=True).order_by('nombres', 'apellidos')
        if hasattr(self.request.user, 'establecimiento') and self.request.user.establecimiento:
            func_qs = func_qs.filter(establecimiento=self.request.user.establecimiento)
        context['funcionarios_disponibles'] = func_qs
        return context

    def form_valid(self, form):
        ruts = self.request.POST.getlist('det_rut[]')
        nombres = self.request.POST.getlist('det_nombres[]')
        apellidos = self.request.POST.getlist('det_apellidos[]')
        deptos = self.request.POST.getlist('det_departamento[]')
        cargos = self.request.POST.getlist('det_cargo[]')
        func_ids = self.request.POST.getlist('det_funcionario_id[]')

        # Validar que al menos haya un funcionario
        detalles_data = []
        for i in range(len(ruts)):
            rut_val = ruts[i].strip() if i < len(ruts) else ''
            nom_val = nombres[i].strip() if i < len(nombres) else ''
            ape_val = apellidos[i].strip() if i < len(apellidos) else ''
            dep_val = deptos[i].strip() if i < len(deptos) else ''
            car_val = cargos[i].strip() if i < len(cargos) else ''
            f_id = func_ids[i].strip() if i < len(func_ids) else ''

            if rut_val or nom_val or ape_val or f_id:
                detalles_data.append({
                    'rut': rut_val,
                    'nombres': nom_val,
                    'apellidos': ape_val,
                    'departamento': dep_val,
                    'cargo': car_val,
                    'funcionario_id': int(f_id) if f_id and f_id.isdigit() else None
                })

        if not detalles_data:
            messages.error(self.request, 'Debe ingresar al menos un funcionario para crear la solicitud.')
            return self.form_invalid(form)

        with transaction.atomic():
            solicitud = form.save(commit=False)
            solicitud.usuario_solicitante = self.request.user
            solicitud.created_by = self.request.user
            solicitud.establecimiento = getattr(self.request.user, 'establecimiento', None)
            solicitud.estado = 'PENDIENTE_RRHH'
            solicitud.fecha_solicitud = timezone.now()
            solicitud.save()

            for item in detalles_data:
                func_obj = None
                if item['funcionario_id']:
                    func_obj = Funcionario.objects.filter(pk=item['funcionario_id']).first()

                detalle = SolicitudCorreoDetalle(
                    solicitud=solicitud,
                    funcionario=func_obj,
                    rut=item['rut'],
                    nombres=item['nombres'],
                    apellidos=item['apellidos'],
                    departamento=item['departamento'] or str(solicitud.departamento_solicitante or ''),
                    cargo=item['cargo'],
                    estado='PENDIENTE_RRHH',
                    created_by=self.request.user
                )
                detalle.save()

            solicitud.actualizar_estado_general()

        messages.success(
            self.request,
            f"Solicitud {solicitud.numero_solicitud} creada con éxito y enviada a revisión de RR.HH."
        )
        return redirect('solicitud_correo:detalle', pk=solicitud.pk)


class SolicitudCorreoDetailView(LoginRequiredMixin, DetailView):
    """
    Vista de detalle de una solicitud de correos con el estado de cada funcionario solicitado,
    trazabilidad y acciones correspondientes según rol.
    """
    model = SolicitudCorreo
    template_name = 'solicitud_correo/detalle_solicitud.html'
    context_object_name = 'solicitud'

    def get_queryset(self):
        queryset = SolicitudCorreo.objects.all().select_related(
            'establecimiento', 'departamento_solicitante', 'usuario_solicitante',
            'usuario_rrhh', 'tecnico_tic'
        ).prefetch_related(
            'detalles', 'detalles__funcionario', 'detalles__usuario_rrhh',
            'detalles__tecnico_responsable', 'detalles__notificado_por'
        )
        if hasattr(self.request.user,
                   'establecimiento') and self.request.user.establecimiento and not self.request.user.is_superuser:
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solicitud = self.object
        context['title'] = f"Detalle de Solicitud {solicitud.numero_solicitud or solicitud.id}"
        context['module_name'] = MODULE_NAME
        context['es_rrhh'] = user_is_rrhh(self.request.user)
        context['es_tic'] = user_is_tic(self.request.user)
        context['puede_notificar'] = user_can_notify(self.request.user)
        context['es_propietario'] = (solicitud.usuario_solicitante == self.request.user)

        # Formularios para modales
        context['form_rrhh'] = RevisionDetalleRRHHForm()
        context['form_tic'] = ProcesamientoDetalleTICForm()
        context['form_notificacion'] = NotificacionFuncionarioForm()
        return context


class SolicitudBandejaRRHHListView(RRHHRequiredMixin, ListView):
    """
    Bandeja de Recursos Humanos: listado y filtrado de solicitudes para revisión.
    """
    model = SolicitudCorreo
    template_name = 'solicitud_correo/bandeja_rrhh.html'
    context_object_name = 'solicitudes'
    paginate_by = 15

    def get_queryset(self):
        queryset = SolicitudCorreo.objects.filter(is_active=True).select_related(
            'establecimiento', 'departamento_solicitante', 'usuario_solicitante', 'usuario_rrhh'
        ).prefetch_related('detalles')

        if hasattr(self.request.user,
                   'establecimiento') and self.request.user.establecimiento and not self.request.user.is_superuser:
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)

        # Filtros
        estado_filtro = self.request.GET.get('filtro_estado') or self.request.POST.get('filtro_estado')
        if estado_filtro:
            if estado_filtro == 'PENDIENTES':
                queryset = queryset.filter(estado__in=['PENDIENTE_RRHH', 'EN_REVISION_RRHH'])
            elif estado_filtro == 'EN_TIC':
                queryset = queryset.filter(estado__in=['EN_TIC', 'EN_PROCESO_TIC'])
            elif estado_filtro == 'FINALIZADAS':
                queryset = queryset.filter(estado='FINALIZADA')

        form = FiltroSolicitudForm(self.request.GET)
        if form.is_valid():
            numero = form.cleaned_data.get('numero_solicitud')
            estado = form.cleaned_data.get('estado')
            termino = form.cleaned_data.get('funcionario_busqueda')

            if numero:
                queryset = queryset.filter(numero_solicitud__icontains=numero)
            if estado:
                queryset = queryset.filter(estado=estado)
            if termino:
                queryset = queryset.filter(
                    Q(detalles__rut__icontains=termino) |
                    Q(detalles__nombres__icontains=termino) |
                    Q(detalles__apellidos__icontains=termino)
                ).distinct()

        return queryset.order_by('-id')

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('draw'):
            return self.datatables_response(request)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'search' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self.datatables_response(request)
        return JsonResponse({'error': 'Acción no válida'}, status=400)

    def datatables_response(self, request):
        queryset = self.get_queryset()
        params = request.POST if request.method == 'POST' else request.GET

        draw = int(params.get('draw', 1))
        start = max(int(params.get('start', 0)), 0)
        length = int(params.get('length', 10))

        records_total = queryset.count()

        search_value = params.get('search[value]', '').strip()
        if search_value:
            queryset = queryset.filter(
                Q(numero_solicitud__icontains=search_value) |
                Q(departamento_nombre__icontains=search_value) |
                Q(departamento_solicitante__nombre__icontains=search_value) |
                Q(establecimiento__nombre__icontains=search_value) |
                Q(usuario_solicitante__first_name__icontains=search_value) |
                Q(usuario_solicitante__last_name__icontains=search_value) |
                Q(usuario_solicitante__username__icontains=search_value) |
                Q(detalles__rut__icontains=search_value) |
                Q(detalles__nombres__icontains=search_value) |
                Q(detalles__apellidos__icontains=search_value)
            ).distinct()

        # Filtros de columna
        depto_filter = params.get('columns[2][search][value]', '').strip()
        if depto_filter:
            queryset = queryset.filter(
                Q(departamento_nombre__icontains=depto_filter) |
                Q(departamento_solicitante__nombre__icontains=depto_filter)
            )

        estado_filter = params.get('columns[4][search][value]', '').strip()
        if estado_filter:
            queryset = queryset.filter(estado=estado_filter)

        records_filtered = queryset.count()

        order_column = params.get('order[0][column]')
        order_dir = params.get('order[0][dir]', 'desc')

        order_map = {
            0: 'numero_solicitud',
            1: 'usuario_solicitante__first_name',
            2: 'departamento_nombre',
            4: 'estado',
            5: 'fecha_solicitud',
        }

        if order_column is not None:
            try:
                col_idx = int(order_column)
                field = order_map.get(col_idx)
                if field:
                    if order_dir == 'desc':
                        field = f'-{field}'
                    queryset = queryset.order_by(field)
            except (ValueError, TypeError):
                queryset = queryset.order_by('-id')
        else:
            queryset = queryset.order_by('-id')

        if length != -1:
            queryset = queryset[start:start + min(length, 500)]

        data = [
            self.serialize_solicitud(sol)
            for sol in queryset
        ]

        opciones_estados = [
            {'label': label, 'value': code}
            for code, label in SolicitudCorreo.ESTADOS
        ]

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
            'columnControl': {
                'estado': opciones_estados
            }
        })

    def serialize_solicitud(self, sol):
        detalle_url = reverse('solicitud_correo:detalle', args=[sol.pk])
        revision_url = reverse('solicitud_correo:revision_rrhh', args=[sol.pk])
        historial_url = reverse('solicitud_correo:historial', args=[sol.pk])

        badge_func = '<div class="d-flex align-items-center gap-1 flex-wrap">'
        badge_func += f'<span class="badge bg-secondary" title="Total Funcionarios"><i class="bi bi-people me-1"></i>{sol.total_funcionarios}</span>'
        if sol.total_pendientes_rrhh > 0:
            badge_func += f'<span class="badge bg-warning text-dark" title="Pendientes RR.HH."><i class="bi bi-clock me-1"></i>{sol.total_pendientes_rrhh} Pend.</span>'
        if sol.total_aprobados > 0:
            badge_func += f'<span class="badge bg-success" title="Aprobados RR.HH."><i class="bi bi-check-lg me-1"></i>{sol.total_aprobados} Aprob.</span>'
        if sol.total_rechazados > 0:
            badge_func += f'<span class="badge bg-danger" title="Rechazados por RR.HH."><i class="bi bi-x-lg me-1"></i>{sol.total_rechazados} Rech.</span>'
        badge_func += '</div>'

        acciones = '<div class="btn-group btn-group-sm" role="group">'
        if sol.total_pendientes_rrhh > 0 or sol.estado in ['PENDIENTE_RRHH', 'EN_REVISION_RRHH']:
            acciones += f'<a href="{revision_url}" class="btn btn-warning" title="Revisar Solicitud"><i class="bi bi-person-check-fill me-1"></i> Revisar</a>'
        acciones += f'<a href="{detalle_url}" class="btn btn-outline-primary" title="Ver Detalle" data-bs-toggle="tooltip"><i class="bi bi-eye"></i></a>'
        acciones += f'<button type="button" class="btn btn-outline-info" hx-get="{historial_url}" hx-target="#genericModalContent" data-bs-toggle="modal" data-bs-target="#genericModal" title="Historial"><i class="bi bi-clock-history"></i></button>'
        acciones += '</div>'

        solicitante_str = escape(sol.usuario_solicitante.get_full_name() or sol.usuario_solicitante.username)
        est_str = escape(sol.establecimiento.nombre if sol.establecimiento else "")
        depto_str = escape(
            sol.departamento_nombre or (sol.departamento_solicitante.nombre if sol.departamento_solicitante else "-"))

        folio_str = escape(sol.numero_solicitud or str(sol.id))
        folio_html = f'<a href="{detalle_url}" class="fw-bold text-decoration-none font-monospace text-primary">{folio_str}</a>'

        fecha_html = ""
        if sol.fecha_solicitud:
            fecha_html = f'<div>{sol.fecha_solicitud.strftime("%d/%m/%Y")}</div><small class="text-muted">{sol.fecha_solicitud.strftime("%H:%M")} hrs</small>'

        return {
            'numero_solicitud': folio_html,
            'usuario_solicitante__nombre': f'<div>{solicitante_str}</div><small class="text-muted">{est_str}</small>',
            'departamento_solicitante': depto_str,
            'funcionarios': badge_func,
            'estado': get_estado_badge(sol.estado),
            'fecha_solicitud': fecha_html,
            'acciones': acciones,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Bandeja de Recursos Humanos'
        context['module_name'] = MODULE_NAME
        context['filter_form'] = FiltroSolicitudForm(self.request.GET)
        context['filtro_estado'] = self.request.GET.get('filtro_estado', '')
        context['es_rrhh'] = True
        context['es_tic'] = user_is_tic(self.request.user)

        # Contadores de la bandeja
        base_qs = SolicitudCorreo.objects.filter(is_active=True)
        if hasattr(self.request.user,
                   'establecimiento') and self.request.user.establecimiento and not self.request.user.is_superuser:
            base_qs = base_qs.filter(establecimiento=self.request.user.establecimiento)

        context['total_pendientes_rrhh'] = base_qs.filter(estado__in=['PENDIENTE_RRHH', 'EN_REVISION_RRHH']).count()
        context['total_en_tic'] = base_qs.filter(estado__in=['EN_TIC', 'EN_PROCESO_TIC']).count()
        context['total_finalizadas'] = base_qs.filter(estado='FINALIZADA').count()
        context['total_solicitudes'] = base_qs.count()
        return context


class SolicitudRevisionRRHHView(RRHHRequiredMixin, DetailView):
    """
    Vista dedicada para que RR.HH. revise individualmente los funcionarios de una solicitud.
    """
    model = SolicitudCorreo
    template_name = 'solicitud_correo/revision_rrhh.html'
    context_object_name = 'solicitud'

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user,
                   'establecimiento') and self.request.user.establecimiento and not self.request.user.is_superuser:
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Revisión RR.HH. - Solicitud {self.object.numero_solicitud}"
        context['module_name'] = MODULE_NAME
        context['form_rrhh'] = RevisionDetalleRRHHForm()
        context['es_rrhh'] = True
        context['es_tic'] = user_is_tic(self.request.user)
        return context


class SolicitudBandejaTICListView(TICRequiredMixin, ListView):
    """
    Bandeja de Informática / TIC: lista solicitudes y funcionarios aprobados por RR.HH. pendientes de creación en MINSAL.
    """
    model = SolicitudCorreo
    template_name = 'solicitud_correo/bandeja_tic.html'
    context_object_name = 'solicitudes'
    paginate_by = 15

    def get_queryset(self):
        queryset = SolicitudCorreo.objects.filter(
            is_active=True,
            estado__in=['EN_TIC', 'EN_PROCESO_TIC', 'FINALIZADA']
        ).select_related(
            'establecimiento', 'departamento_solicitante', 'usuario_solicitante', 'tecnico_tic'
        ).prefetch_related('detalles')

        if hasattr(self.request.user,
                   'establecimiento') and self.request.user.establecimiento and not self.request.user.is_superuser:
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)

        filtro_estado = self.request.GET.get('filtro_estado') or self.request.POST.get('filtro_estado')
        if filtro_estado == 'PENDIENTES':
            queryset = queryset.filter(estado__in=['EN_TIC', 'EN_PROCESO_TIC'])
        elif filtro_estado == 'FINALIZADAS':
            queryset = queryset.filter(estado='FINALIZADA')

        form = FiltroSolicitudForm(self.request.GET)
        if form.is_valid():
            numero = form.cleaned_data.get('numero_solicitud')
            estado = form.cleaned_data.get('estado')
            termino = form.cleaned_data.get('funcionario_busqueda')

            if numero:
                queryset = queryset.filter(numero_solicitud__icontains=numero)
            if estado:
                queryset = queryset.filter(estado=estado)
            if termino:
                queryset = queryset.filter(
                    Q(detalles__rut__icontains=termino) |
                    Q(detalles__nombres__icontains=termino) |
                    Q(detalles__apellidos__icontains=termino)
                ).distinct()

        return queryset.order_by('-id')

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('draw'):
            return self.datatables_response(request)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'search' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self.datatables_response(request)
        return JsonResponse({'error': 'Acción no válida'}, status=400)

    def datatables_response(self, request):
        queryset = self.get_queryset()
        params = request.POST if request.method == 'POST' else request.GET

        draw = int(params.get('draw', 1))
        start = max(int(params.get('start', 0)), 0)
        length = int(params.get('length', 10))

        records_total = queryset.count()

        search_value = params.get('search[value]', '').strip()
        if search_value:
            queryset = queryset.filter(
                Q(numero_solicitud__icontains=search_value) |
                Q(departamento_nombre__icontains=search_value) |
                Q(departamento_solicitante__nombre__icontains=search_value) |
                Q(establecimiento__nombre__icontains=search_value) |
                Q(usuario_solicitante__first_name__icontains=search_value) |
                Q(usuario_solicitante__last_name__icontains=search_value) |
                Q(usuario_solicitante__username__icontains=search_value) |
                Q(detalles__rut__icontains=search_value) |
                Q(detalles__nombres__icontains=search_value) |
                Q(detalles__apellidos__icontains=search_value)
            ).distinct()

        depto_filter = params.get('columns[2][search][value]', '').strip()
        if depto_filter:
            queryset = queryset.filter(
                Q(departamento_nombre__icontains=depto_filter) |
                Q(departamento_solicitante__nombre__icontains=depto_filter)
            )

        estado_filter = params.get('columns[4][search][value]', '').strip()
        if estado_filter:
            queryset = queryset.filter(estado=estado_filter)

        records_filtered = queryset.count()

        order_column = params.get('order[0][column]')
        order_dir = params.get('order[0][dir]', 'desc')

        order_map = {
            0: 'numero_solicitud',
            1: 'usuario_solicitante__first_name',
            2: 'departamento_nombre',
            4: 'estado',
            5: 'fecha_solicitud',
        }

        if order_column is not None:
            try:
                col_idx = int(order_column)
                field = order_map.get(col_idx)
                if field:
                    if order_dir == 'desc':
                        field = f'-{field}'
                    queryset = queryset.order_by(field)
            except (ValueError, TypeError):
                queryset = queryset.order_by('-id')
        else:
            queryset = queryset.order_by('-id')

        if length != -1:
            queryset = queryset[start:start + min(length, 500)]

        data = [
            self.serialize_solicitud(sol)
            for sol in queryset
        ]

        opciones_estados = [
            {'label': label, 'value': code}
            for code, label in SolicitudCorreo.ESTADOS
            if code in ['EN_TIC', 'EN_PROCESO_TIC', 'FINALIZADA']
        ]

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
            'columnControl': {
                'estado': opciones_estados
            }
        })

    def serialize_solicitud(self, sol):
        detalle_url = reverse('solicitud_correo:detalle', args=[sol.pk])
        procesamiento_url = reverse('solicitud_correo:procesamiento_tic', args=[sol.pk])
        historial_url = reverse('solicitud_correo:historial', args=[sol.pk])

        badge_func = '<div class="d-flex align-items-center gap-1 flex-wrap">'
        badge_func += f'<span class="badge bg-secondary" title="Total Funcionarios"><i class="bi bi-people me-1"></i>{sol.total_funcionarios}</span>'
        if sol.total_creados > 0:
            badge_func += f'<span class="badge bg-success" title="Cuentas Creadas"><i class="bi bi-check-lg me-1"></i>{sol.total_creados} Creados</span>'
        if sol.total_pendientes_tic > 0:
            badge_func += f'<span class="badge bg-info text-dark" title="Pendientes TIC"><i class="bi bi-hourglass-split me-1"></i>{sol.total_pendientes_tic} Pend. TIC</span>'
        badge_func += '</div>'

        acciones = '<div class="btn-group btn-group-sm" role="group">'
        if sol.total_pendientes_tic > 0 or sol.estado in ['EN_TIC', 'EN_PROCESO_TIC']:
            acciones += f'<a href="{procesamiento_url}" class="btn btn-primary" title="Procesar Solicitud TIC"><i class="bi bi-gear-fill me-1"></i> Procesar</a>'
        acciones += f'<a href="{detalle_url}" class="btn btn-outline-primary" title="Ver Detalle" data-bs-toggle="tooltip"><i class="bi bi-eye"></i></a>'
        acciones += f'<button type="button" class="btn btn-outline-info" hx-get="{historial_url}" hx-target="#genericModalContent" data-bs-toggle="modal" data-bs-target="#genericModal" title="Historial"><i class="bi bi-clock-history"></i></button>'
        acciones += '</div>'

        solicitante_str = escape(sol.usuario_solicitante.get_full_name() or sol.usuario_solicitante.username)
        est_str = escape(sol.establecimiento.nombre if sol.establecimiento else "")
        depto_str = escape(
            sol.departamento_nombre or (sol.departamento_solicitante.nombre if sol.departamento_solicitante else "-"))

        folio_str = escape(sol.numero_solicitud or str(sol.id))
        folio_html = f'<a href="{detalle_url}" class="fw-bold text-decoration-none font-monospace text-primary">{folio_str}</a>'

        fecha_html = ""
        if sol.fecha_solicitud:
            fecha_html = f'<div>{sol.fecha_solicitud.strftime("%d/%m/%Y")}</div><small class="text-muted">{sol.fecha_solicitud.strftime("%H:%M")} hrs</small>'

        return {
            'numero_solicitud': folio_html,
            'usuario_solicitante__nombre': f'<div>{solicitante_str}</div><small class="text-muted">{est_str}</small>',
            'departamento_solicitante': depto_str,
            'funcionarios': badge_func,
            'estado': get_estado_badge(sol.estado),
            'fecha_solicitud': fecha_html,
            'acciones': acciones,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Bandeja de TIC / Informática'
        context['module_name'] = MODULE_NAME
        context['filter_form'] = FiltroSolicitudForm(self.request.GET)
        context['filtro_estado'] = self.request.GET.get('filtro_estado', '')
        context['es_rrhh'] = user_is_rrhh(self.request.user)
        context['es_tic'] = True

        base_detalles = SolicitudCorreoDetalle.objects.filter(is_active=True)
        if hasattr(self.request.user,
                   'establecimiento') and self.request.user.establecimiento and not self.request.user.is_superuser:
            base_detalles = base_detalles.filter(solicitud__establecimiento=self.request.user.establecimiento)

        context['total_pendientes_tic'] = base_detalles.filter(estado__in=['APROBADO_RRHH', 'EN_PROCESO_TIC']).count()
        context['total_creados_hoy'] = base_detalles.filter(
            estado='CREADO',
            fecha_creacion__date=timezone.now().date()
        ).count()
        context['total_creados_total'] = base_detalles.filter(estado='CREADO').count()
        context['form_tic'] = ProcesamientoDetalleTICForm()

        # Obtener lista de funcionarios pendientes de procesar para pestaña rápida
        context['detalles_pendientes_tic'] = base_detalles.filter(
            estado__in=['APROBADO_RRHH', 'EN_PROCESO_TIC']
        ).select_related('solicitud', 'funcionario', 'solicitud__departamento_solicitante')[:50]
        return context


class SolicitudProcesamientoTICView(TICRequiredMixin, DetailView):
    """
    Vista dedicada para que TIC procese o registre la creación de cuentas de una solicitud.
    """
    model = SolicitudCorreo
    template_name = 'solicitud_correo/procesamiento_tic.html'
    context_object_name = 'solicitud'

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user,
                   'establecimiento') and self.request.user.establecimiento and not self.request.user.is_superuser:
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Procesamiento TIC - Solicitud {self.object.numero_solicitud}"
        context['module_name'] = MODULE_NAME
        context['form_tic'] = ProcesamientoDetalleTICForm()
        context['es_rrhh'] = user_is_rrhh(self.request.user)
        context['es_tic'] = True
        return context


# ==============================================================================
# ACCIONES / CONTROLADORES INDIVIDUALES
# ==============================================================================

@login_required
@rrhh_required
@require_POST
def detalle_revisar_rrhh(request, pk):
    """
    Permite a RR.HH. aprobar o rechazar individualmente a un funcionario.
    """
    detalle_qs = SolicitudCorreoDetalle.objects.select_related('solicitud')
    if hasattr(request.user, 'establecimiento') and request.user.establecimiento and not request.user.is_superuser:
        detalle_qs = detalle_qs.filter(solicitud__establecimiento=request.user.establecimiento)
    detalle = get_object_or_404(detalle_qs, pk=pk)
    solicitud = detalle.solicitud

    accion = request.POST.get('accion')
    motivo_rechazo = request.POST.get('motivo_rechazo', '').strip()

    if accion == 'APROBADO_RRHH':
        detalle.estado = 'APROBADO_RRHH'
        detalle.motivo_rechazo = None
        detalle.usuario_rrhh = request.user
        detalle.fecha_revision_rrhh = timezone.now()
        detalle.updated_by = request.user
        detalle.save()
        messages.success(request, f"Funcionario {detalle.nombre_completo} ha sido APROBADO por RR.HH.")
    elif accion == 'RECHAZADO_RRHH':
        if not motivo_rechazo:
            messages.error(request, "Debe especificar un motivo de rechazo.")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Debe especificar un motivo de rechazo.'}, status=400)
            return redirect(
                request.META.get('HTTP_REFERER') or reverse('solicitud_correo:detalle', args=[solicitud.pk]))

        detalle.estado = 'RECHAZADO_RRHH'
        detalle.motivo_rechazo = motivo_rechazo
        detalle.usuario_rrhh = request.user
        detalle.fecha_revision_rrhh = timezone.now()
        detalle.updated_by = request.user
        detalle.save()
        messages.warning(request, f"Funcionario {detalle.nombre_completo} ha sido RECHAZADO por RR.HH.")
    else:
        messages.error(request, "Acción de revisión no válida.")
        return redirect(request.META.get('HTTP_REFERER') or reverse('solicitud_correo:detalle', args=[solicitud.pk]))

    solicitud.usuario_rrhh = request.user
    solicitud.fecha_revision_rrhh = timezone.now()
    solicitud.actualizar_estado_general()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'estado': detalle.estado,
            'estado_display': detalle.get_estado_display(),
            'solicitud_estado': solicitud.estado,
            'solicitud_estado_display': solicitud.get_estado_display(),
        })

    return redirect(request.META.get('HTTP_REFERER') or reverse('solicitud_correo:detalle', args=[solicitud.pk]))


@login_required
@rrhh_required
@require_POST
def solicitud_aprobar_todos_rrhh(request, pk):
    """
    Permite a RR.HH. aprobar todos los funcionarios pendientes de una solicitud de una sola vez.
    """
    solicitud_qs = SolicitudCorreo.objects.all()
    if hasattr(request.user, 'establecimiento') and request.user.establecimiento and not request.user.is_superuser:
        solicitud_qs = solicitud_qs.filter(establecimiento=request.user.establecimiento)
    solicitud = get_object_or_404(solicitud_qs, pk=pk)
    detalles_pendientes = solicitud.detalles.filter(estado='PENDIENTE_RRHH')

    count = 0
    now = timezone.now()
    with transaction.atomic():
        for d in detalles_pendientes:
            d.estado = 'APROBADO_RRHH'
            d.motivo_rechazo = None
            d.usuario_rrhh = request.user
            d.fecha_revision_rrhh = now
            d.updated_by = request.user
            d.save()
            count += 1

        solicitud.usuario_rrhh = request.user
        solicitud.fecha_revision_rrhh = now
        solicitud.actualizar_estado_general()

    messages.success(request, f"Se han aprobado {count} funcionarios. La solicitud fue enviada a TIC.")
    return redirect(request.META.get('HTTP_REFERER') or reverse('solicitud_correo:detalle', args=[solicitud.pk]))


@login_required
@tic_required
@require_POST
def detalle_procesar_tic(request, pk):
    """
    Permite a un técnico de TIC registrar la creación externa de la cuenta en MINSAL o registrar un error.
    """
    detalle_qs = SolicitudCorreoDetalle.objects.select_related('solicitud')
    if hasattr(request.user, 'establecimiento') and request.user.establecimiento and not request.user.is_superuser:
        detalle_qs = detalle_qs.filter(solicitud__establecimiento=request.user.establecimiento)
    detalle = get_object_or_404(detalle_qs, pk=pk)
    solicitud = detalle.solicitud

    accion = request.POST.get('accion')
    correo_creado = request.POST.get('correo_creado', '').strip()
    referencia_externa = request.POST.get('referencia_externa', '').strip()
    observacion_tic = request.POST.get('observacion_tic', '').strip()
    fecha_creacion_str = request.POST.get('fecha_creacion')

    fecha_creacion = timezone.now()
    if fecha_creacion_str:
        try:
            fecha_creacion = timezone.datetime.fromisoformat(fecha_creacion_str)
        except ValueError:
            pass

    if accion == 'CREADO':
        if not correo_creado:
            messages.error(request, "Debe ingresar el correo electrónico creado.")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Debe ingresar el correo electrónico creado.'},
                                    status=400)
            return redirect(
                request.META.get('HTTP_REFERER') or reverse('solicitud_correo:detalle', args=[solicitud.pk]))

        detalle.estado = 'CREADO'
        detalle.correo_creado = correo_creado.lower()
        detalle.fecha_creacion = fecha_creacion
        detalle.referencia_externa = referencia_externa
        detalle.observacion_tic = observacion_tic
        detalle.tecnico_responsable = request.user
        detalle.fecha_procesamiento_tic = timezone.now()
        detalle.updated_by = request.user
        detalle.save()
        messages.success(request, f"Cuenta creada para {detalle.nombre_completo}: {detalle.correo_creado}")

    elif accion == 'ERROR':
        if not observacion_tic:
            messages.error(request, "Debe ingresar una observación explicando el error.")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Debe ingresar una observación explicando el error.'},
                                    status=400)
            return redirect(
                request.META.get('HTTP_REFERER') or reverse('solicitud_correo:detalle', args=[solicitud.pk]))

        detalle.estado = 'ERROR'
        detalle.observacion_tic = observacion_tic
        detalle.referencia_externa = referencia_externa
        detalle.tecnico_responsable = request.user
        detalle.fecha_procesamiento_tic = timezone.now()
        detalle.updated_by = request.user
        detalle.save()
        messages.warning(request, f"Se ha registrado error en creación para {detalle.nombre_completo}.")
    else:
        messages.error(request, "Acción de procesamiento no válida.")
        return redirect(request.META.get('HTTP_REFERER') or reverse('solicitud_correo:detalle', args=[solicitud.pk]))

    solicitud.tecnico_tic = request.user
    solicitud.fecha_procesamiento_tic = timezone.now()
    solicitud.actualizar_estado_general()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'estado': detalle.estado,
            'estado_display': detalle.get_estado_display(),
            'correo_creado': detalle.correo_creado,
            'solicitud_estado': solicitud.estado,
            'solicitud_estado_display': solicitud.get_estado_display(),
        })

    return redirect(request.META.get('HTTP_REFERER') or reverse('solicitud_correo:detalle', args=[solicitud.pk]))


@login_required
@require_POST
def detalle_notificar_funcionario(request, pk):
    """
    Permite a RR.HH. (o usuarios autorizados) registrar o enviar la notificación de la cuenta creada al funcionario.
    """
    if not user_can_notify(request.user):
        messages.error(request, "No tiene permisos para registrar notificaciones.")
        return redirect('solicitud_correo:mis_solicitudes')

    detalle_qs = SolicitudCorreoDetalle.objects.select_related('solicitud')
    if hasattr(request.user, 'establecimiento') and request.user.establecimiento and not request.user.is_superuser:
        detalle_qs = detalle_qs.filter(solicitud__establecimiento=request.user.establecimiento)
    detalle = get_object_or_404(detalle_qs, pk=pk)
    correo_destinatario = request.POST.get('correo_destinatario', '').strip()
    observacion_notificacion = request.POST.get('observacion_notificacion', '').strip()
    enviar_email = request.POST.get('enviar_email') in ['true', 'True', '1', 'on']

    detalle.notificado = True
    detalle.fecha_notificacion = timezone.now()
    detalle.notificado_por = request.user
    detalle.observacion_notificacion = observacion_notificacion
    detalle.correo_notificacion_enviado_a = correo_destinatario
    detalle.updated_by = request.user
    detalle.save()

    # Si se solicitó enviar correo electrónico
    if enviar_email and correo_destinatario:
        establecimiento = detalle.solicitud.establecimiento or getattr(request.user, 'establecimiento', None)
        if establecimiento:
            config = ConfiguracionCorreo.objects.filter(establecimiento=establecimiento, activo=True).first()
            if config:
                try:
                    EmailService.send_email_with_config(
                        config=config,
                        subject=f"Cuenta de correo institucional creada: {detalle.correo_creado}",
                        recipient_list=[correo_destinatario],
                        template_name='solicitud_correo/emails/cuenta_creada_notificacion.html',
                        context={
                            'detalle': detalle,
                            'solicitud': detalle.solicitud,
                            'establecimiento': establecimiento,
                            'observacion': observacion_notificacion
                        }
                    )
                    messages.info(request, f"Se intentó enviar el correo de notificación a {correo_destinatario}.")
                except Exception as e:
                    logger.error(f"Error al enviar notificación por correo a {correo_destinatario}: {str(e)}")

    messages.success(request, f"Notificación registrada exitosamente para {detalle.nombre_completo}.")
    return redirect(
        request.META.get('HTTP_REFERER') or reverse('solicitud_correo:detalle', args=[detalle.solicitud.pk]))


@login_required
@require_POST
def solicitud_cancelar(request, pk):
    """
    Permite cancelar una solicitud en estado BORRADOR o PENDIENTE_RRHH.
    """
    solicitud_qs = SolicitudCorreo.objects.all()
    if hasattr(request.user, 'establecimiento') and request.user.establecimiento and not request.user.is_superuser:
        solicitud_qs = solicitud_qs.filter(establecimiento=request.user.establecimiento)
    solicitud = get_object_or_404(solicitud_qs, pk=pk)

    # Validar permisos: debe ser el usuario solicitante o RR.HH. o superuser
    if not (request.user.is_superuser or user_is_rrhh(request.user) or solicitud.usuario_solicitante == request.user):
        messages.error(request, "No tiene permisos para cancelar esta solicitud.")
        return redirect('solicitud_correo:mis_solicitudes')

    if solicitud.estado in ['FINALIZADA', 'CANCELADA']:
        messages.warning(request,
                         f"La solicitud {solicitud.numero_solicitud} ya se encuentra {solicitud.get_estado_display()}.")
        return redirect('solicitud_correo:detalle', pk=solicitud.pk)

    solicitud.estado = 'CANCELADA'
    solicitud.updated_by = request.user
    solicitud.save(update_fields=['estado', 'updated_by', 'updated_at'])
    messages.success(request, f"La solicitud {solicitud.numero_solicitud} ha sido cancelada.")
    return redirect('solicitud_correo:mis_solicitudes')


class SolicitudHistorialView(LoginRequiredMixin, DetailView):
    """
    Muestra la trazabilidad y la línea de tiempo de cambios de la solicitud y sus funcionarios mediante simple_history.
    """
    model = SolicitudCorreo
    template_name = 'solicitud_correo/historial_modal.html'
    context_object_name = 'solicitud'

    def get_queryset(self):
        queryset = SolicitudCorreo.objects.all()
        if hasattr(self.request.user,
                   'establecimiento') and self.request.user.establecimiento and not self.request.user.is_superuser:
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)
        if not self.request.user.is_superuser and not user_is_rrhh(self.request.user) and not user_is_tic(
                self.request.user):
            queryset = queryset.filter(usuario_solicitante=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['eventos'] = self.obtener_eventos_historial(self.object)
        return context

    def obtener_eventos_historial(self, solicitud):
        eventos = []

        # 1. Historial de la Solicitud
        records_solicitud = list(solicitud.history.all().order_by('history_date', 'history_id'))
        prev = None
        for rec in records_solicitud:
            if prev is None:
                eventos.append({
                    'fecha': rec.history_date,
                    'titulo': 'Solicitud Creada',
                    'detalle': f"Solicitud ingresada por {rec.history_user or solicitud.usuario_solicitante} con estado '{rec.get_estado_display()}'.",
                    'usuario': rec.history_user,
                    'icono': 'bi bi-plus-circle-fill',
                    'icon_bg': 'bg-primary text-white',
                })
            else:
                if prev.estado != rec.estado:
                    eventos.append({
                        'fecha': rec.history_date,
                        'titulo': f"Cambio de Estado General: {rec.get_estado_display()}",
                        'detalle': f"El estado de la solicitud cambió de '{prev.get_estado_display()}' a '{rec.get_estado_display()}'.",
                        'usuario': rec.history_user,
                        'icono': 'bi bi-arrow-repeat',
                        'icon_bg': 'bg-info text-white',
                    })
            prev = rec

        # 2. Historial de cada Detalle
        for det in solicitud.detalles.all():
            det_records = list(det.history.all().order_by('history_date', 'history_id'))
            prev_d = None
            for drec in det_records:
                nombre_comp = f"{drec.nombres or ''} {drec.apellidos or ''}".strip() or drec.rut or f"Funcionario #{drec.id or ''}"
                if prev_d is None:
                    eventos.append({
                        'fecha': drec.history_date,
                        'titulo': f"Funcionario Agregado: {nombre_comp}",
                        'detalle': f"RUT: {drec.rut or 'S/R'}, Departamento: {drec.departamento or 'S/D'}",
                        'usuario': drec.history_user,
                        'icono': 'bi bi-person-plus-fill',
                        'icon_bg': 'bg-secondary text-white',
                    })
                else:
                    if prev_d.estado != drec.estado:
                        if drec.estado == 'APROBADO_RRHH':
                            eventos.append({
                                'fecha': drec.history_date,
                                'titulo': f"RR.HH. Aprobó: {nombre_comp}",
                                'detalle': f"Aprobado por {drec.history_user or drec.usuario_rrhh}.",
                                'usuario': drec.history_user or drec.usuario_rrhh,
                                'icono': 'bi bi-check-circle-fill',
                                'icon_bg': 'bg-success text-white',
                            })
                        elif drec.estado == 'RECHAZADO_RRHH':
                            eventos.append({
                                'fecha': drec.history_date,
                                'titulo': f"RR.HH. Rechazó: {nombre_comp}",
                                'detalle': f"Motivo: {drec.motivo_rechazo or 'Sin motivo'}",
                                'usuario': drec.history_user or drec.usuario_rrhh,
                                'icono': 'bi bi-x-circle-fill',
                                'icon_bg': 'bg-danger text-white',
                            })
                        elif drec.estado == 'CREADO':
                            eventos.append({
                                'fecha': drec.history_date,
                                'titulo': f"TIC Creó Cuenta: {nombre_comp}",
                                'detalle': f"Correo: {drec.correo_creado} | Ref MINSAL: {drec.referencia_externa or 'S/R'} | Obs: {drec.observacion_tic or 'Ninguna'}",
                                'usuario': drec.history_user or drec.tecnico_responsable,
                                'icono': 'bi bi-envelope-check-fill',
                                'icon_bg': 'bg-primary text-white',
                            })
                        elif drec.estado == 'ERROR':
                            eventos.append({
                                'fecha': drec.history_date,
                                'titulo': f"TIC Registró Error: {nombre_comp}",
                                'detalle': f"Detalle error: {drec.observacion_tic or 'Sin observación'}",
                                'usuario': drec.history_user or drec.tecnico_responsable,
                                'icono': 'bi bi-exclamation-triangle-fill',
                                'icon_bg': 'bg-warning text-dark',
                            })

                    if not prev_d.notificado and drec.notificado:
                        eventos.append({
                            'fecha': drec.fecha_notificacion or drec.history_date,
                            'titulo': f"Notificación Registrada: {nombre_comp}",
                            'detalle': f"Notificado por {drec.notificado_por or drec.history_user}. Obs: {drec.observacion_notificacion or 'Ninguna'}",
                            'usuario': drec.notificado_por or drec.history_user,
                            'icono': 'bi bi-bell-fill',
                            'icon_bg': 'bg-info text-white',
                        })
                prev_d = drec

        # Ordenar cronológicamente todos los eventos
        eventos.sort(key=lambda x: x['fecha'], reverse=True)
        return eventos


@login_required
def api_funcionario_info(request, pk):
    """
    Retorna los datos del funcionario en JSON para autocompletar en el formulario.
    """
    funcionario_qs = Funcionario.objects.all()
    if hasattr(request.user, 'establecimiento') and request.user.establecimiento and not request.user.is_superuser:
        funcionario_qs = funcionario_qs.filter(establecimiento=request.user.establecimiento)
    funcionario = get_object_or_404(funcionario_qs, pk=pk)
    depto = str(funcionario.unidad_organizacional) if funcionario.unidad_organizacional else ''
    return JsonResponse({
        'id': funcionario.id,
        'rut': funcionario.rut or '',
        'nombres': funcionario.nombres or '',
        'apellidos': funcionario.apellidos or '',
        'cargo': funcionario.cargo or '',
        'departamento': depto
    })
