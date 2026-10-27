import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, View

from core.models.configuracion_correo import ConfiguracionCorreo
from core.models.funcionario import Funcionario
from core.services.email_service import EmailService
from solicitud_vpn.forms import (
    SolicitudVPNForm,
    BeneficiarioVPNFormSet,
    SolicitudAccesoFormSet,
    GestionTICSolicitudForm,
    FiltroSolicitudVPNForm,
    PerfilVPNForm,
)
from solicitud_vpn.models import SolicitudVPN, AccesoVPN, PerfilVPN
from solicitud_vpn.permissions import user_is_vpn_gestor, VPNRequiredMixin, vpn_required
from solicitud_vpn.utils import obtener_datos_tecnico_solicitante

logger = logging.getLogger(__name__)

MODULE_NAME = 'Solicitudes de Acceso VPN'


def get_estado_badge(estado):
    badges = {
        'BORRADOR': '<span class="badge bg-secondary"><i class="bi bi-pencil me-1"></i>Borrador</span>',
        'PENDIENTE': '<span class="badge bg-warning text-dark"><i class="bi bi-clock me-1"></i>Pendiente</span>',
        'EN_REVISION': '<span class="badge bg-primary"><i class="bi bi-search me-1"></i>En revisión</span>',
        'ENVIADO_ECONECTA': '<span class="badge text-white" style="background-color: #6f42c1;"><i class="bi bi-send me-1"></i>Enviado a eConecta</span>',
        'COMPLETADO': '<span class="badge bg-success"><i class="bi bi-check-all me-1"></i>Completado</span>',
        'RECHAZADO': '<span class="badge bg-danger"><i class="bi bi-x-circle me-1"></i>Rechazado</span>',
    }
    return badges.get(estado, f'<span class="badge bg-secondary">{escape(estado)}</span>')


def get_accion_badge(accion):
    badges = {
        'CREAR': '<span class="badge bg-success">Crear</span>',
        'ACTUALIZAR': '<span class="badge bg-primary text-light">Actualizar</span>',
        'ELIMINAR': '<span class="badge bg-danger">Eliminar</span>',
    }
    return badges.get(accion, f'<span class="badge bg-secondary">{escape(accion)}</span>')


class SolicitudVPNMisSolicitudesListView(LoginRequiredMixin, ListView):
    """
    Bandeja 'Mis solicitudes': Muestra las solicitudes creadas por el usuario autenticado.
    """
    model = SolicitudVPN
    template_name = 'solicitud_vpn/mis_solicitudes.html'
    context_object_name = 'solicitudes'
    paginate_by = 15

    def get_queryset(self):
        queryset = SolicitudVPN.objects.filter(is_active=True).select_related(
            'establecimiento', 'departamento_solicitante', 'usuario_solicitante'
        ).prefetch_related('beneficiarios', 'accesos')

        # Si no es superuser ni gestor VPN, ve sus propias solicitudes
        if not self.request.user.is_superuser:
            queryset = queryset.filter(usuario_solicitante=self.request.user)

        # Filtros
        params = self.request.POST if self.request.method == 'POST' else self.request.GET
        form = FiltroSolicitudVPNForm(params)
        if form.is_valid():
            numero = form.cleaned_data.get('numero_solicitud')
            estado = form.cleaned_data.get('estado')
            accion = form.cleaned_data.get('accion')
            termino = form.cleaned_data.get('beneficiario_busqueda')

            if numero:
                queryset = queryset.filter(numero_solicitud__icontains=numero)
            if estado:
                queryset = queryset.filter(estado=estado)
            if accion:
                queryset = queryset.filter(accion=accion)
            if termino:
                queryset = queryset.filter(
                    Q(beneficiarios__rut__icontains=termino) |
                    Q(beneficiarios__nombres__icontains=termino) |
                    Q(beneficiarios__apellidos__icontains=termino) |
                    Q(beneficiarios__nombre_completo__icontains=termino)
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
                Q(establecimiento__nombre__icontains=search_value) |
                Q(tecnico_establecimiento__icontains=search_value) |
                Q(departamento_nombre__icontains=search_value) |
                Q(grupo_vpn__icontains=search_value) |
                Q(ticket_econecta__icontains=search_value) |
                Q(beneficiarios__rut__icontains=search_value) |
                Q(beneficiarios__nombres__icontains=search_value) |
                Q(beneficiarios__apellidos__icontains=search_value) |
                Q(beneficiarios__nombre_completo__icontains=search_value)
            ).distinct()

        # Filtros por columna
        accion_filter = params.get('columns[3][search][value]', '').strip()
        if accion_filter:
            queryset = queryset.filter(accion=accion_filter)

        estado_filter = params.get('columns[5][search][value]', '').strip()
        if estado_filter:
            queryset = queryset.filter(estado=estado_filter)

        records_filtered = queryset.count()

        order_column = params.get('order[0][column]')
        order_dir = params.get('order[0][dir]', 'desc')

        order_map = {
            0: 'numero_solicitud',
            1: 'fecha_solicitud',
            2: 'establecimiento__nombre',
            3: 'accion',
            5: 'estado',
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
            for code, label in SolicitudVPN.ESTADOS
        ]
        opciones_acciones = [
            {'label': label, 'value': code}
            for code, label in SolicitudVPN.ACCIONES
        ]

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
            'columnControl': {
                'accion': opciones_acciones,
                'estado': opciones_estados,
            }
        })

    def serialize_solicitud(self, sol):
        detalle_url = reverse('solicitud_vpn:detalle', args=[sol.pk])

        folio_str = escape(sol.numero_solicitud or str(sol.id))
        folio_html = f'<a href="{detalle_url}" class="fw-bold text-decoration-none font-monospace text-primary">{folio_str}</a>'
        if sol.grupo_vpn:
            folio_html += f'<small class="d-block text-muted">Grupo: {escape(sol.grupo_vpn)}</small>'

        fecha_html = ""
        if sol.fecha_solicitud:
            fecha_html = f'<div>{sol.fecha_solicitud.strftime("%d/%m/%Y")}</div><small class="text-muted">{sol.fecha_solicitud.strftime("%H:%M")} hrs</small>'

        est_nombre = sol.establecimiento.nombre if sol.establecimiento else (sol.tecnico_establecimiento or '-')
        est_html = f'<span class="fw-semibold">{escape(est_nombre)}</span>'
        if sol.departamento_nombre:
            est_html += f'<small class="d-block text-muted">{escape(sol.departamento_nombre)}</small>'

        ben_html = f'<span class="badge bg-info text-dark"><i class="bi bi-people-fill me-1"></i>{sol.total_beneficiarios} pers.</span>'
        ben_html += f'<small class="text-muted ms-1">({sol.total_accesos} accesos)</small>'

        estado_html = get_estado_badge(sol.estado)
        if sol.ticket_econecta:
            estado_html += f'<small class="d-block text-muted">Ticket: {escape(sol.ticket_econecta)}</small>'

        acciones_html = f'<a href="{detalle_url}" class="btn btn-sm btn-outline-primary" title="Ver Detalle"><i class="bi bi-eye me-1"></i> Ver Detalle</a>'

        return {
            'numero_solicitud': folio_html,
            'fecha_solicitud': fecha_html,
            'establecimiento': est_html,
            'accion': get_accion_badge(sol.accion),
            'beneficiarios': ben_html,
            'estado': estado_html,
            'acciones': acciones_html,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mis Solicitudes de Acceso VPN'
        context['module_name'] = MODULE_NAME
        context['filter_form'] = FiltroSolicitudVPNForm(self.request.GET)
        context['es_gestor_vpn'] = user_is_vpn_gestor(self.request.user)

        # Contadores rápidos del usuario
        qs_user = SolicitudVPN.objects.filter(is_active=True)
        if not self.request.user.is_superuser:
            qs_user = qs_user.filter(usuario_solicitante=self.request.user)

        context['total_solicitudes'] = qs_user.count()
        context['total_pendientes'] = qs_user.filter(estado='PENDIENTE').count()
        context['total_en_revision'] = qs_user.filter(estado='EN_REVISION').count()
        context['total_enviadas_econecta'] = qs_user.filter(estado='ENVIADO_ECONECTA').count()
        context['total_completadas'] = qs_user.filter(estado='COMPLETADO').count()
        context['total_rechazadas'] = qs_user.filter(estado='RECHAZADO').count()
        return context


class SolicitudVPNCreateView(LoginRequiredMixin, View):
    """
    Creación de una nueva solicitud de VPN con FormSets de Beneficiarios y Accesos.
    Maneja conjuntamente:
      - form
      - beneficiarios_formset
      - accesos_formset
    Validando los tres antes de guardar de manera atómica.
    """
    template_name = 'solicitud_vpn/form_solicitud.html'

    def get_funcionarios_disponibles(self, request):
        func_qs = Funcionario.objects.filter(is_active=True).order_by('nombres', 'apellidos')
        if hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            func_qs = func_qs.filter(establecimiento=request.user.establecimiento)
        return func_qs

    def get_context_data(self, request, form=None, beneficiarios_formset=None, accesos_formset=None):
        if form is None:
            form = SolicitudVPNForm(request=request)
        if beneficiarios_formset is None:
            beneficiarios_formset = BeneficiarioVPNFormSet(prefix='beneficiarios')
        if accesos_formset is None:
            accesos_formset = SolicitudAccesoFormSet(prefix='accesos')

        return {
            'form': form,
            'beneficiarios_formset': beneficiarios_formset,
            'accesos_formset': accesos_formset,
            'title': 'Generar Requerimiento de Acceso VPN',
            'module_name': MODULE_NAME,
            'es_gestor_vpn': user_is_vpn_gestor(request.user),
            'funcionarios_disponibles': self.get_funcionarios_disponibles(request),
            'accesos_disponibles': AccesoVPN.objects.filter(is_active=True).order_by('plataforma', 'ip'),
            'establecimiento_usuario': getattr(request.user, 'establecimiento', None),
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = SolicitudVPNForm(request.POST, request=request)
        beneficiarios_formset = BeneficiarioVPNFormSet(request.POST, prefix='beneficiarios')
        accesos_formset = SolicitudAccesoFormSet(request.POST, prefix='accesos')

        es_borrador = request.POST.get('guardar_borrador') == '1'

        is_form_valid = form.is_valid()
        is_ben_valid = beneficiarios_formset.is_valid()
        is_acc_valid = accesos_formset.is_valid()

        if is_form_valid and is_ben_valid and is_acc_valid:
            nuevo_estado = 'BORRADOR' if es_borrador else 'PENDIENTE'

            with transaction.atomic():
                solicitud = form.save(commit=False)
                solicitud.usuario_solicitante = request.user
                solicitud.created_by = request.user
                solicitud.establecimiento = getattr(request.user, 'establecimiento', None)
                solicitud.estado = nuevo_estado
                solicitud.fecha_solicitud = timezone.now()
                solicitud.save()

                # Guardar beneficiarios
                beneficiarios_formset.instance = solicitud
                beneficiarios = beneficiarios_formset.save(commit=False)
                for ben in beneficiarios:
                    ben.solicitud = solicitud
                    ben.created_by = request.user
                    if not ben.establecimiento and solicitud.establecimiento:
                        ben.establecimiento = solicitud.establecimiento.nombre
                    ben.save()

                for del_obj in beneficiarios_formset.deleted_objects:
                    del_obj.delete()

                # Guardar accesos seleccionados (ManyToMany)
                accesos_seleccionados = []
                for acc_form in accesos_formset:
                    if acc_form.cleaned_data and not acc_form.cleaned_data.get('DELETE', False):
                        acc = acc_form.cleaned_data.get('acceso')
                        if acc:
                            accesos_seleccionados.append(acc)

                solicitud.accesos.set(accesos_seleccionados)

            if es_borrador:
                messages.info(request, f"Solicitud {solicitud.numero_solicitud} guardada en estado Borrador.")
            else:
                messages.success(
                    request,
                    f"Solicitud {solicitud.numero_solicitud} generada con éxito y enviada a la Bandeja TIC."
                )

            return redirect('solicitud_vpn:mis_solicitudes')

        messages.error(request, "Por favor corrija los errores en el formulario antes de enviar.")
        context = self.get_context_data(
            request,
            form=form,
            beneficiarios_formset=beneficiarios_formset,
            accesos_formset=accesos_formset
        )
        return render(request, self.template_name, context)


class SolicitudVPNBandejaTICListView(VPNRequiredMixin, ListView):
    """
    Bandeja TIC: Muestra las solicitudes de acceso VPN de todos los establecimientos
    del Servicio de Salud Arauco para su revisión y preparación de requerimiento en eConecta.
    """
    model = SolicitudVPN
    template_name = 'solicitud_vpn/bandeja_tic.html'
    context_object_name = 'solicitudes'
    paginate_by = 20

    def get_queryset(self):
        queryset = SolicitudVPN.objects.filter(is_active=True).select_related(
            'establecimiento', 'departamento_solicitante', 'usuario_solicitante', 'usuario_revision'
        ).prefetch_related('beneficiarios', 'accesos')

        params = self.request.POST if self.request.method == 'POST' else self.request.GET
        form = FiltroSolicitudVPNForm(params)
        if form.is_valid():
            numero = form.cleaned_data.get('numero_solicitud')
            estado = form.cleaned_data.get('estado')
            establecimiento = form.cleaned_data.get('establecimiento')
            accion = form.cleaned_data.get('accion')
            termino = form.cleaned_data.get('beneficiario_busqueda')

            if numero:
                queryset = queryset.filter(numero_solicitud__icontains=numero)
            if estado:
                queryset = queryset.filter(estado=estado)
            if establecimiento:
                queryset = queryset.filter(establecimiento=establecimiento)
            if accion:
                queryset = queryset.filter(accion=accion)
            if termino:
                queryset = queryset.filter(
                    Q(beneficiarios__rut__icontains=termino) |
                    Q(beneficiarios__nombres__icontains=termino) |
                    Q(beneficiarios__apellidos__icontains=termino) |
                    Q(beneficiarios__nombre_completo__icontains=termino)
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
                Q(establecimiento__nombre__icontains=search_value) |
                Q(tecnico_establecimiento__icontains=search_value) |
                Q(departamento_nombre__icontains=search_value) |
                Q(tecnico_nombre__icontains=search_value) |
                Q(usuario_solicitante__first_name__icontains=search_value) |
                Q(usuario_solicitante__last_name__icontains=search_value) |
                Q(usuario_solicitante__username__icontains=search_value) |
                Q(grupo_vpn__icontains=search_value) |
                Q(ticket_econecta__icontains=search_value) |
                Q(beneficiarios__rut__icontains=search_value) |
                Q(beneficiarios__nombres__icontains=search_value) |
                Q(beneficiarios__apellidos__icontains=search_value) |
                Q(beneficiarios__nombre_completo__icontains=search_value)
            ).distinct()

        # Filtros por columna
        establecimiento_filter = params.get('columns[2][search][value]', '').strip()
        if establecimiento_filter:
            queryset = queryset.filter(
                Q(establecimiento__nombre__icontains=establecimiento_filter) |
                Q(tecnico_establecimiento__icontains=establecimiento_filter)
            )

        accion_filter = params.get('columns[4][search][value]', '').strip()
        if accion_filter:
            queryset = queryset.filter(accion=accion_filter)

        estado_filter = params.get('columns[6][search][value]', '').strip()
        if estado_filter:
            queryset = queryset.filter(estado=estado_filter)

        records_filtered = queryset.count()

        order_column = params.get('order[0][column]')
        order_dir = params.get('order[0][dir]', 'desc')

        order_map = {
            0: 'numero_solicitud',
            1: 'fecha_solicitud',
            2: 'establecimiento__nombre',
            3: 'tecnico_nombre',
            4: 'accion',
            6: 'estado',
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
            for code, label in SolicitudVPN.ESTADOS
        ]
        opciones_acciones = [
            {'label': label, 'value': code}
            for code, label in SolicitudVPN.ACCIONES
        ]

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
            'columnControl': {
                'accion': opciones_acciones,
                'estado': opciones_estados,
            }
        })

    def serialize_solicitud(self, sol):
        detalle_url = reverse('solicitud_vpn:detalle', args=[sol.pk])

        folio_str = escape(sol.numero_solicitud or str(sol.id))
        folio_html = f'<a href="{detalle_url}" class="fw-bold text-decoration-none font-monospace text-primary">{folio_str}</a>'
        if sol.grupo_vpn:
            folio_html += f'<small class="d-block text-muted">Grupo: {escape(sol.grupo_vpn)}</small>'

        fecha_html = ""
        if sol.fecha_solicitud:
            fecha_html = f'<div>{sol.fecha_solicitud.strftime("%d/%m/%Y")}</div><small class="text-muted">{sol.fecha_solicitud.strftime("%H:%M")} hrs</small>'

        est_nombre = sol.establecimiento.nombre if sol.establecimiento else (sol.tecnico_establecimiento or '-')
        est_html = f'<span class="fw-semibold text-primary"><i class="bi bi-hospital me-1"></i>{escape(est_nombre)}</span>'
        if sol.departamento_nombre:
            est_html += f'<small class="d-block text-muted">{escape(sol.departamento_nombre)}</small>'

        solicitante_nombre = escape(
            sol.tecnico_nombre or (sol.usuario_solicitante.get_full_name() if sol.usuario_solicitante else '-'))
        solicitante_cargo = escape(sol.tecnico_cargo or sol.tecnico_rut or (
            sol.usuario_solicitante.username if sol.usuario_solicitante else ''))
        solicitante_html = f'<div class="fw-bold">{solicitante_nombre}</div><small class="text-muted d-block">{solicitante_cargo}'
        if sol.es_proveedor:
            solicitante_html += ' <span class="badge bg-warning text-dark ms-1">Proveedor</span>'
        solicitante_html += '</small>'

        ben_html = f'<span class="badge bg-info text-dark"><i class="bi bi-people-fill me-1"></i>{sol.total_beneficiarios} pers.</span>'
        ben_html += f'<small class="text-muted d-block">{sol.total_accesos} accesos</small>'

        estado_html = get_estado_badge(sol.estado)
        if sol.ticket_econecta:
            estado_html += f'<small class="d-block text-muted">Ticket: {escape(sol.ticket_econecta)}</small>'

        destinatario = escape(
            sol.tecnico_nombre or (sol.usuario_solicitante.get_full_name() if sol.usuario_solicitante else ''))
        email = escape(sol.tecnico_email or (sol.usuario_solicitante.email if sol.usuario_solicitante else ''))
        estado_display = escape(sol.get_estado_display())
        ticket_val = escape(sol.ticket_econecta or '')

        acciones_html = f'''<div class="btn-group btn-group-sm" role="group">
            <a href="{detalle_url}" class="btn btn-outline-primary" data-bs-toggle="tooltip" data-bs-placement="top" title="Ver y revisar detalle de la solicitud"><i class="bi bi-eye"></i></a>
            <button type="button" class="btn btn-outline-purple text-white btn-econecta-modal" style="background-color: #6f42c1; border-color: #6f42c1;" data-bs-toggle="tooltip" data-bs-placement="top" title="Cambiar estado a Enviado a eConecta" data-sol-id="{sol.pk}" data-sol-folio="{folio_str}" data-sol-ticket="{ticket_val}"><i class="bi bi-send"></i></button>
            <button type="button" class="btn btn-outline-success btn-completar-modal" data-bs-toggle="tooltip" data-bs-placement="top" title="Marcar solicitud como Completada" data-sol-id="{sol.pk}" data-sol-folio="{folio_str}"><i class="bi bi-check-lg"></i></button>
            <button type="button" class="btn btn-outline-info btn-notificar-modal" data-bs-toggle="tooltip" data-bs-placement="top" title="Notificar por correo al solicitante / referente TIC" data-sol-id="{sol.pk}" data-sol-folio="{folio_str}" data-sol-destinatario="{destinatario}" data-sol-email="{email}" data-sol-estado="{estado_display}"><i class="bi bi-bell"></i></button>
            <button type="button" class="btn btn-outline-danger btn-eliminar-modal" data-bs-toggle="tooltip" data-bs-placement="top" title="Eliminar solicitud" data-sol-id="{sol.pk}" data-sol-folio="{folio_str}"><i class="bi bi-trash"></i></button>
        </div>'''

        return {
            'numero_solicitud': folio_html,
            'fecha_solicitud': fecha_html,
            'establecimiento': est_html,
            'solicitante': solicitante_html,
            'accion': get_accion_badge(sol.accion),
            'beneficiarios': ben_html,
            'estado': estado_html,
            'acciones': acciones_html,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Bandeja de Gestión VPN - Informática / TIC'
        context['module_name'] = MODULE_NAME
        context['filter_form'] = FiltroSolicitudVPNForm(self.request.GET)
        context['es_gestor_vpn'] = True

        # Contadores / KPIs TIC
        qs_all = SolicitudVPN.objects.filter(is_active=True)
        context['total_pendientes'] = qs_all.filter(estado='PENDIENTE').count()
        context['total_en_revision'] = qs_all.filter(estado='EN_REVISION').count()
        context['total_enviadas_econecta'] = qs_all.filter(estado='ENVIADO_ECONECTA').count()
        context['total_completadas'] = qs_all.filter(estado='COMPLETADO').count()
        context['total_general'] = qs_all.count()
        return context


class SolicitudVPNDetalleView(LoginRequiredMixin, DetailView):
    """
    Vista de detalle y revisión TIC de la solicitud VPN.
    Muestra los datos del solicitante/técnico en texto plano y tablas estructuradas
    de beneficiarios y accesos para facilitar la copia de información a eConecta.
    """
    model = SolicitudVPN
    template_name = 'solicitud_vpn/detalle_solicitud.html'
    context_object_name = 'solicitud'

    def get_queryset(self):
        queryset = SolicitudVPN.objects.all().select_related(
            'establecimiento', 'departamento_solicitante', 'usuario_solicitante', 'usuario_revision'
        ).prefetch_related(
            'beneficiarios', 'beneficiarios__funcionario', 'accesos'
        )

        # Si no es superuser ni gestor VPN, solo puede ver sus propias solicitudes
        if not self.request.user.is_superuser and not user_is_vpn_gestor(self.request.user):
            queryset = queryset.filter(usuario_solicitante=self.request.user)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solicitud = self.object
        context['title'] = f"Detalle de Solicitud VPN {solicitud.numero_solicitud or f'#{solicitud.id}'}"
        context['module_name'] = MODULE_NAME
        context['es_gestor_vpn'] = user_is_vpn_gestor(self.request.user)
        context['gestion_form'] = GestionTICSolicitudForm(initial={
            'estado': solicitud.estado,
            'ticket_econecta': solicitud.ticket_econecta or '',
            'observacion_revision': solicitud.observacion_revision or ''
        })

        # Construir resumen en texto plano formateado para copiar rápidamente a eConecta
        econecta_text_lines = []
        econecta_text_lines.append("=== DATOS DEL SOLICITANTE / REFERENTE INFORMÁTICO ===")
        econecta_text_lines.append(f"Nombre Completo: {solicitud.tecnico_nombre or '-'}")
        econecta_text_lines.append(f"RUT: {solicitud.tecnico_rut or '-'}")
        econecta_text_lines.append(
            f"Establecimiento: {solicitud.tecnico_establecimiento or (solicitud.establecimiento.nombre if solicitud.establecimiento else '-')}")
        econecta_text_lines.append(f"Teléfono: {solicitud.tecnico_telefono or '-'}")
        econecta_text_lines.append(f"Cargo: {solicitud.tecnico_cargo or '-'}")
        econecta_text_lines.append(f"Fecha Requerimiento: {solicitud.tecnico_fecha or timezone.now().date()}")
        econecta_text_lines.append(f"Email: {solicitud.tecnico_email or '-'}")
        econecta_text_lines.append(f"Es Proveedor / Tercero: {'SÍ' if solicitud.es_proveedor else 'NO'}")
        econecta_text_lines.append("")
        econecta_text_lines.append("=== PARÁMETROS VPN ===")
        econecta_text_lines.append(f"Acción Solicitada: {solicitud.get_accion_display()}")
        econecta_text_lines.append(f"Grupo VPN: {solicitud.grupo_vpn or 'N/A'}")
        econecta_text_lines.append(f"Fecha Expiración: {solicitud.fecha_expiracion or 'Indefinida / No especificada'}")
        econecta_text_lines.append(f"Time Out VPN: {solicitud.timeout_vpn or '1 hora'}")
        if solicitud.observacion:
            econecta_text_lines.append(f"Observaciones: {solicitud.observacion}")
        econecta_text_lines.append("")
        econecta_text_lines.append(f"=== BENEFICIARIOS ({solicitud.beneficiarios.count()}) ===")

        for idx, ben in enumerate(solicitud.beneficiarios.all(), 1):
            econecta_text_lines.append(
                f"[{idx}] Nombre: {ben.get_nombre_completo()} | RUT: {ben.rut or '-'} | Cargo: {ben.cargo or '-'} | Establecimiento: {ben.establecimiento or '-'} | Email: {ben.email or '-'} | Teléfono: {ben.telefono or '-'}")

        econecta_text_lines.append("")
        econecta_text_lines.append(f"=== ACCESOS VPN SOLICITADOS ({solicitud.accesos.count()}) ===")
        accesos = solicitud.accesos.all()
        if accesos.exists():
            for a_idx, acc in enumerate(accesos, 1):
                econecta_text_lines.append(
                    f"  [{a_idx}] Sistema: {acc.plataforma} | IP / Dirección: {acc.ip}"
                )
        else:
            econecta_text_lines.append("  (Sin accesos específicos registrados)")

        context['texto_econecta_completo'] = "\n".join(econecta_text_lines)
        return context


class SolicitudVPNCambiarEstadoView(VPNRequiredMixin, View):
    """
    Endpoint para cambiar el estado de la solicitud VPN, registrar el ticket eConecta y observaciones.
    """

    def post(self, request, pk):
        solicitud = get_object_or_404(SolicitudVPN, pk=pk)
        form = GestionTICSolicitudForm(request.POST)

        if form.is_valid():
            nuevo_estado = form.cleaned_data['estado']
            ticket_econecta = form.cleaned_data.get('ticket_econecta', '')
            observacion = form.cleaned_data.get('observacion_revision', '')

            solicitud.estado = nuevo_estado
            solicitud.ticket_econecta = ticket_econecta
            solicitud.observacion_revision = observacion
            solicitud.usuario_revision = request.user
            solicitud.updated_by = request.user

            now = timezone.now()
            if nuevo_estado == 'EN_REVISION' and not solicitud.fecha_revision:
                solicitud.fecha_revision = now
            elif nuevo_estado == 'ENVIADO_ECONECTA':
                if not solicitud.fecha_revision:
                    solicitud.fecha_revision = now
                solicitud.fecha_envio_econecta = now
            elif nuevo_estado in ['COMPLETADO', 'RECHAZADO']:
                if not solicitud.fecha_revision:
                    solicitud.fecha_revision = now
                solicitud.fecha_finalizacion = now

            solicitud.save()

            messages.success(
                request,
                f"Estado de la solicitud {solicitud.numero_solicitud} actualizado a '{solicitud.get_estado_display()}'."
            )
        else:
            messages.error(request, "Error al actualizar el estado de la solicitud. Verifique los datos.")

        return redirect('solicitud_vpn:detalle', pk=solicitud.pk)


class PerfilVPNView(LoginRequiredMixin, View):
    """
    Vista para ver y actualizar el perfil de gestión VPN y datos de técnico referente del usuario conectado.
    """
    template_name = 'solicitud_vpn/perfil_vpn.html'

    def get(self, request):
        perfil, _ = PerfilVPN.objects.get_or_create(usuario=request.user)
        # Si está recién creado o vacío, autocompletar con datos de funcionario/user
        if not perfil.nombre_completo:
            datos = obtener_datos_tecnico_solicitante(request.user)
            perfil.nombre_completo = datos['nombre_completo']
            perfil.rut = datos['rut']
            perfil.establecimiento = datos['establecimiento']
            perfil.telefono = datos['telefono']
            perfil.cargo = datos['cargo']
            perfil.email = datos['email']
            perfil.save()

        form = PerfilVPNForm(instance=perfil)
        return render(request, self.template_name, {
            'form': form,
            'perfil': perfil,
            'title': 'Mi Perfil de Referente VPN',
            'module_name': MODULE_NAME,
            'es_gestor_vpn': user_is_vpn_gestor(request.user),
        })

    def post(self, request):
        perfil, _ = PerfilVPN.objects.get_or_create(usuario=request.user)
        form = PerfilVPNForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "Datos de perfil VPN actualizados con éxito.")
            return redirect('solicitud_vpn:perfil')
        return render(request, self.template_name, {
            'form': form,
            'perfil': perfil,
            'title': 'Mi Perfil de Referente VPN',
            'module_name': MODULE_NAME,
            'es_gestor_vpn': user_is_vpn_gestor(request.user),
        })


class FuncionarioDataAPIView(LoginRequiredMixin, View):
    """
    API JSON que retorna los datos de un Funcionario para autocompletar filas de beneficiarios.
    """

    def get(self, request, pk):
        try:
            f = Funcionario.objects.get(pk=pk, is_active=True)
            telefono = ''
            if hasattr(f, 'anexo') and f.anexo and getattr(f.anexo, 'numero', None):
                telefono = str(f.anexo.numero)

            data = {
                'id': f.id,
                'rut': f.rut or '',
                'nombres': f.nombres or '',
                'apellidos': f.apellidos or '',
                'nombre_completo': f.nombre or f"{f.nombres or ''} {f.apellidos or ''}".strip(),
                'establecimiento': f.establecimiento.nombre if f.establecimiento else '',
                'cargo': f.cargo or '',
                'email': f.email or '',
                'telefono': telefono,
                'fecha': timezone.now().date().strftime('%Y-%m-%d')
            }
            return JsonResponse({'status': 'ok', 'data': data})
        except Funcionario.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Funcionario no encontrado'}, status=404)


# ==============================================================================
# VISTAS BASADAS EN FUNCIONES (ACCIONES TIC)
# ==============================================================================

@vpn_required
@require_POST
def solicitud_marcar_econecta(request, pk):
    """
    Cambia el estado de la solicitud a 'ENVIADO_ECONECTA' (Enviado a eConecta).
    Opcionalmente actualiza el ticket de eConecta si es provisto.
    """
    solicitud = get_object_or_404(SolicitudVPN, pk=pk, is_active=True)
    ticket = request.POST.get('ticket_econecta', '').strip()
    if ticket:
        solicitud.ticket_econecta = ticket

    now = timezone.now()
    if not solicitud.fecha_revision:
        solicitud.fecha_revision = now
    solicitud.fecha_envio_econecta = now
    solicitud.estado = 'ENVIADO_ECONECTA'
    solicitud.usuario_revision = request.user
    solicitud.updated_by = request.user
    solicitud.save()

    messages.success(
        request,
        f"La solicitud {solicitud.numero_solicitud} ha sido cambiada a estado 'Enviado a eConecta'."
    )
    return redirect(request.META.get('HTTP_REFERER') or reverse('solicitud_vpn:bandeja_tic'))


@vpn_required
@require_POST
def solicitud_marcar_completado(request, pk):
    """
    Cambia el estado de la solicitud a 'COMPLETADO'.
    """
    solicitud = get_object_or_404(SolicitudVPN, pk=pk, is_active=True)
    now = timezone.now()
    if not solicitud.fecha_revision:
        solicitud.fecha_revision = now
    solicitud.fecha_finalizacion = now
    solicitud.estado = 'COMPLETADO'
    solicitud.usuario_revision = request.user
    solicitud.updated_by = request.user
    solicitud.save()

    messages.success(
        request,
        f"La solicitud {solicitud.numero_solicitud} ha sido marcada como 'Completado'."
    )
    return redirect(request.META.get('HTTP_REFERER') or reverse('solicitud_vpn:bandeja_tic'))


@vpn_required
@require_POST
def solicitud_eliminar(request, pk):
    """
    Realiza la eliminación lógica de la solicitud de VPN dejando `is_active=False`.
    """
    solicitud = get_object_or_404(SolicitudVPN, pk=pk, is_active=True)
    solicitud.is_active = False
    solicitud.updated_by = request.user
    solicitud.save()

    messages.warning(
        request,
        f"La solicitud {solicitud.numero_solicitud} ha sido eliminada del sistema."
    )
    return redirect('solicitud_vpn:bandeja_tic')


@vpn_required
@require_POST
def solicitud_notificar_solicitante(request, pk):
    """
    Notifica al usuario solicitante / TIC del establecimiento que realizó la solicitud de VPN
    utilizando la configuración de correo activa del establecimiento del usuario conectado.
    """
    solicitud = get_object_or_404(SolicitudVPN, pk=pk, is_active=True)
    mensaje_adicional = request.POST.get('mensaje', '').strip()

    # Determinar el email de destino (técnico solicitante o usuario solicitante)
    email_destinatario = (
            solicitud.tecnico_email or
            (solicitud.usuario_solicitante.email if solicitud.usuario_solicitante else None)
    )

    nombre_destinatario = (
            solicitud.tecnico_nombre or
            (solicitud.usuario_solicitante.get_full_name() if solicitud.usuario_solicitante else 'Referente TIC')
    )

    enviado_email = False
    if email_destinatario:
        # Buscar el establecimiento del usuario logueado (gestor TIC / técnico)
        establecimiento_usuario = getattr(request.user, 'establecimiento', None)
        config = None
        if establecimiento_usuario:
            config = ConfiguracionCorreo.objects.filter(establecimiento=establecimiento_usuario, activo=True).first()

        # Si el usuario logueado no tiene establecimiento o no tiene config activa, buscar por el establecimiento de la solicitud
        if not config and solicitud.establecimiento:
            config = ConfiguracionCorreo.objects.filter(establecimiento=solicitud.establecimiento, activo=True).first()

        # Fallback a cualquier configuración activa si aplica
        if not config:
            config = ConfiguracionCorreo.objects.filter(activo=True).first()

        if config:
            try:
                asunto = f"Actualización de Solicitud VPN {solicitud.numero_solicitud} - Estado: {solicitud.get_estado_display()}"
                contexto_correo = {
                    'solicitud': solicitud,
                    'nombre_destinatario': nombre_destinatario,
                    'email_destinatario': email_destinatario,
                    'observacion': mensaje_adicional,
                    'beneficiarios': list(solicitud.beneficiarios.all()),
                    'establecimiento_remitente': config.establecimiento,
                }

                resultado = EmailService.send_email_with_config(
                    config=config,
                    subject=asunto,
                    recipient_list=[email_destinatario],
                    template_name='solicitud_vpn/emails/notificacion_solicitante.html',
                    context=contexto_correo,
                )
                enviado_email = bool(resultado)
            except Exception as e:
                logger.error(f"Error al enviar correo de notificación a {email_destinatario}: {str(e)}")
        else:
            logger.warning(f"No se encontró una configuración SMTP activa para enviar la notificación.")

    if enviado_email:
        messages.success(
            request,
            f"Se ha notificado exitosamente al referente TIC ({nombre_destinatario}) al correo {email_destinatario}."
        )
    else:
        if email_destinatario:
            messages.info(
                request,
                f"Notificación registrada para {nombre_destinatario} ({email_destinatario}). (No se pudo despachar por correo o no hay servidor configurado)."
            )
        else:
            messages.warning(
                request,
                f"No se encontró un correo electrónico registrado para el referente TIC de la solicitud {solicitud.numero_solicitud}."
            )

    return redirect(request.META.get('HTTP_REFERER') or reverse('solicitud_vpn:bandeja_tic'))
