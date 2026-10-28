import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, DetailView

from core.models.establecimientos import Establecimiento
from core.standard.views import StandardCreateView, StandardUpdateView
from soporte.forms.forms_tickets import FormTicket
from soporte.models import AreaSoporte, TipoSoporte, PerfilSoporte
from soporte.models import Ticket


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class TicketDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'tickets/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Áreas del usuario filtradas por el establecimiento del usuario
        try:
            perfil = user.perfil_soporte
            areas_usuario = perfil.area_soporte.all()
            if hasattr(user, 'establecimiento') and user.establecimiento and not user.is_superuser:
                areas_usuario = areas_usuario.filter(establecimiento=user.establecimiento)
        except AttributeError:
            areas_usuario = AreaSoporte.objects.none()

        # Base queryset de tickets según establecimiento
        tickets_base = Ticket.objects.all()
        if hasattr(user, 'establecimiento') and user.establecimiento and not user.is_superuser:
            tickets_base = tickets_base.filter(establecimiento=user.establecimiento)
        elif hasattr(user, 'establecimiento') and user.establecimiento:
            tickets_base = tickets_base.filter(establecimiento=user.establecimiento)

        # Widgets del establecimiento
        stats_est = tickets_base.values('estado').annotate(
            total=Count('id'))
        est_data = {
            'ABIERTO': 0,
            'EN_PROCESO': 0,
            'CERRADO': 0,
            'RECHAZADO': 0
        }
        for s in stats_est:
            if s['estado'] in est_data:
                est_data[s['estado']] = s['total']
        context['stats_establecimiento'] = est_data

        # Widgets por área
        stats_areas = []
        for area in areas_usuario:
            stats = tickets_base.filter(area_soporte=area).values('estado').annotate(total=Count('id'))
            area_data = {
                'area': area.nombre,
                'area_establecimiento': area.establecimiento.nombre if area.establecimiento else '',
                'ABIERTO': 0,
                'EN_PROCESO': 0,
                'CERRADO': 0,
                'RECHAZADO': 0
            }
            for s in stats:
                if s['estado'] in area_data:
                    area_data[s['estado']] = s['total']
            stats_areas.append(area_data)

        context['stats_areas'] = stats_areas

        # Gráfico de columnas: Usuarios con perfil de soporte y sus tickets por estado
        usuarios_soporte_qs = PerfilSoporte.objects.all()
        if hasattr(user, 'establecimiento') and user.establecimiento and not user.is_superuser:
            usuarios_soporte_qs = usuarios_soporte_qs.filter(usuario__establecimiento=user.establecimiento)
        elif hasattr(user, 'establecimiento') and user.establecimiento:
            usuarios_soporte_qs = usuarios_soporte_qs.filter(usuario__establecimiento=user.establecimiento)

        filter_tickets_cerrados = Q(tickets_asignados__estado='CERRADO')
        filter_tickets_abiertos = Q(tickets_asignados__estado='ABIERTO')
        if hasattr(user, 'establecimiento') and user.establecimiento and not user.is_superuser:
            filter_tickets_cerrados &= Q(tickets_asignados__establecimiento=user.establecimiento)
            filter_tickets_abiertos &= Q(tickets_asignados__establecimiento=user.establecimiento)
        elif hasattr(user, 'establecimiento') and user.establecimiento:
            filter_tickets_cerrados &= Q(tickets_asignados__establecimiento=user.establecimiento)
            filter_tickets_abiertos &= Q(tickets_asignados__establecimiento=user.establecimiento)

        usuarios_soporte = usuarios_soporte_qs.filter(
            area_soporte__in=areas_usuario
        ).annotate(
            cerrados_count=Count('tickets_asignados', filter=filter_tickets_cerrados),
            abiertos_count=Count('tickets_asignados', filter=filter_tickets_abiertos)
        ).distinct()

        bar_chart_data = [
            {
                'usuario': str(p.usuario) if p.usuario else f"Perfil #{p.id}",
                'cerrados': p.cerrados_count,
                'abiertos': p.abiertos_count
            } for p in usuarios_soporte
        ]

        context['bar_chart_data'] = bar_chart_data
        context['bar_chart_data_json'] = json.dumps(bar_chart_data)

        return context


class TicketListView(LoginRequiredMixin, TemplateView):
    template_name = 'tickets/ticket_list.html'
    title = 'Mis Tickets'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse(
                {'error': 'Acción no válida'},
                status=400
            )

        draw = max(0, _as_int(request.POST.get('draw'), 1))
        start = max(0, _as_int(request.POST.get('start'), 0))
        length = _as_int(request.POST.get('length'), 25)

        if length < -1:
            length = 25

        establecimiento_id = getattr(
            request.user, 'establecimiento_id', None
        )

        queryset = Ticket.objects.filter(
            is_active=True,
            created_by=request.user,
        ).select_related(
            'area_soporte',
            'funcionario',
            'asignado_a__usuario',
        )

        if establecimiento_id and not request.user.is_superuser:
            queryset = queryset.filter(
                establecimiento_id=establecimiento_id
            )

        # Total sin filtros de búsqueda
        records_total = queryset.count()

        # Búsqueda global
        search = request.POST.get('search[value]', '').strip()

        if search:
            queryset = queryset.filter(
                Q(numero_ticket__icontains=search) |
                Q(titulo__icontains=search) |
                Q(descripcion__icontains=search) |
                Q(nombres__icontains=search) |
                Q(correo__icontains=search) |
                Q(departamento__icontains=search) |
                Q(estado__icontains=search) |
                Q(area_soporte__nombre__icontains=search) |
                Q(funcionario__first_name__icontains=search) |
                Q(funcionario__last_name__icontains=search) |
                Q(funcionario__username__icontains=search) |
                Q(asignado_a__usuario__first_name__icontains=search) |
                Q(asignado_a__usuario__last_name__icontains=search) |
                Q(asignado_a__usuario__username__icontains=search)
            )

        # Filtro por estado: columna 3
        prefijo_estado = 'columns[3][columnControl][list]'
        estados = []

        for key, values in request.POST.lists():
            if (
                    key == prefijo_estado
                    or key.startswith(prefijo_estado + '[')
            ):
                estados.extend(values)

        if estados:
            queryset = queryset.filter(estado__in=estados)

        # Filtro por área de soporte: columna 4
        prefijo_area = 'columns[4][columnControl][list]'
        areas = []

        for key, values in request.POST.lists():
            if key == prefijo_area or key.startswith(prefijo_area + '['):
                areas.extend(values)

        if areas:
            queryset = queryset.filter(
                area_soporte__nombre__in=areas
            )

        # Ordenamiento: mismo orden que en ticket_datatable.js
        columnas = {
            0: 'numero_ticket',
            1: 'titulo',
            2: 'nombres',
            3: 'estado',
            4: 'area_soporte__nombre',
            5: 'asignado_a__usuario__username',
            6: 'created_at',
            7: 'departamento',
        }

        order_index = _as_int(
            request.POST.get('order[0][column]'), 6
        )
        order_dir = request.POST.get('order[0][dir]', 'desc')

        campo = columnas.get(order_index, 'created_at')

        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.order_by(campo, '-pk')

        # Total después de filtrar
        records_filtered = queryset.count()

        # Paginación
        if length != -1:
            queryset = queryset[start:start + length]

        # Datos con las claves que espera ticket_datatable.js
        data = []

        for ticket in queryset:
            funcionario = ticket.funcionario
            usuario_asignado = (
                ticket.asignado_a.usuario
                if ticket.asignado_a
                else None
            )

            nombres = ticket.nombres or ''

            if not nombres and funcionario:
                nombres = (
                        funcionario.get_full_name()
                        or funcionario.username
                )

            asignado_a = ''

            if usuario_asignado:
                asignado_a = (
                        usuario_asignado.get_full_name()
                        or usuario_asignado.username
                )

            data.append({
                'id': ticket.pk,
                'numero_ticket': ticket.numero_ticket,
                'titulo': ticket.titulo,
                'nombres': nombres,
                'estado': ticket.estado,
                'area_soporte': (
                    ticket.area_soporte.nombre
                    if ticket.area_soporte
                    else ''
                ),
                'asignado_a': asignado_a,
                'created_at': ticket.created_at,
                'departamento': ticket.departamento or '',
            })

        # Opciones del filtro por área
        areas_queryset = AreaSoporte.objects.filter(is_active=True)

        if establecimiento_id and not request.user.is_superuser:
            areas_queryset = areas_queryset.filter(
                establecimiento_id=establecimiento_id
            )

        opciones_areas = [
            {
                'label': nombre,
                'value': nombre,
            }
            for nombre in areas_queryset.order_by('nombre')
            .values_list('nombre', flat=True)
            .distinct()
        ]

        # Opciones del filtro por estado
        opciones_estados = [
            {
                'label': label,
                'value': value,
            }
            for value, label in Ticket.ESTADOS
        ]

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
            'columnControl': {
                'area_soporte': opciones_areas,
                'estado': opciones_estados,
            },
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title

        establecimiento = getattr(
            self.request.user, 'establecimiento', None
        )

        if self.request.user.is_superuser:
            establecimiento_id = _as_int(
                self.request.GET.get('establecimiento'),
                establecimiento.pk if establecimiento else 1,
            )

            establecimiento = (
                    Establecimiento.objects.filter(
                        pk=establecimiento_id
                    ).first()
                    or establecimiento
            )

        if establecimiento is None:
            establecimiento = Establecimiento.objects.filter(
                pk=1
            ).first()

        context['establecimiento'] = establecimiento
        return context


class TicketInactiveListView(LoginRequiredMixin, TemplateView):
    template_name = 'tickets/ticket_list_inactivos.html'
    title = 'Mis Tickets Inactivos'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse(
                {'error': 'Acción no válida'},
                status=400
            )

        draw = max(0, _as_int(request.POST.get('draw'), 1))
        start = max(0, _as_int(request.POST.get('start'), 0))
        length = _as_int(request.POST.get('length'), 25)

        if length < -1:
            length = 25

        establecimiento_id = getattr(
            request.user, 'establecimiento_id', None
        )

        queryset = Ticket.objects.filter(
            is_active=False,
            created_by=request.user,
        ).select_related(
            'area_soporte',
            'funcionario',
            'asignado_a__usuario',
        )

        if establecimiento_id and not request.user.is_superuser:
            queryset = queryset.filter(
                establecimiento_id=establecimiento_id
            )

        # Total sin filtros de búsqueda
        records_total = queryset.count()

        # Búsqueda global
        search = request.POST.get('search[value]', '').strip()

        if search:
            queryset = queryset.filter(
                Q(numero_ticket__icontains=search) |
                Q(titulo__icontains=search) |
                Q(descripcion__icontains=search) |
                Q(nombres__icontains=search) |
                Q(correo__icontains=search) |
                Q(departamento__icontains=search) |
                Q(estado__icontains=search) |
                Q(area_soporte__nombre__icontains=search) |
                Q(funcionario__first_name__icontains=search) |
                Q(funcionario__last_name__icontains=search) |
                Q(funcionario__username__icontains=search) |
                Q(asignado_a__usuario__first_name__icontains=search) |
                Q(asignado_a__usuario__last_name__icontains=search) |
                Q(asignado_a__usuario__username__icontains=search)
            )

        # Filtro por estado: columna 3
        prefijo_estado = 'columns[3][columnControl][list]'
        estados = []

        for key, values in request.POST.lists():
            if (
                    key == prefijo_estado
                    or key.startswith(prefijo_estado + '[')
            ):
                estados.extend(values)

        if estados:
            queryset = queryset.filter(estado__in=estados)

        # Filtro por área de soporte: columna 4
        prefijo_area = 'columns[4][columnControl][list]'
        areas = []

        for key, values in request.POST.lists():
            if key == prefijo_area or key.startswith(prefijo_area + '['):
                areas.extend(values)

        if areas:
            queryset = queryset.filter(
                area_soporte__nombre__in=areas
            )

        # Ordenamiento: mismo orden que en ticket_datatable.js
        columnas = {
            0: 'numero_ticket',
            1: 'titulo',
            2: 'nombres',
            3: 'estado',
            4: 'area_soporte__nombre',
            5: 'asignado_a__usuario__username',
            6: 'created_at',
            7: 'departamento',
            8: 'fecha_cierre',
        }

        order_index = _as_int(
            request.POST.get('order[0][column]'), 6
        )
        order_dir = request.POST.get('order[0][dir]', 'desc')

        campo = columnas.get(order_index, 'created_at')

        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.order_by(campo, '-pk')

        # Total después de filtrar
        records_filtered = queryset.count()

        # Paginación
        if length != -1:
            queryset = queryset[start:start + length]

        # Datos con las claves que espera ticket_datatable.js
        data = []

        for ticket in queryset:
            funcionario = ticket.funcionario
            usuario_asignado = (
                ticket.asignado_a.usuario
                if ticket.asignado_a
                else None
            )

            nombres = ticket.nombres or ''

            if not nombres and funcionario:
                nombres = (
                        funcionario.get_full_name()
                        or funcionario.username
                )

            asignado_a = ''

            if usuario_asignado:
                asignado_a = (
                        usuario_asignado.get_full_name()
                        or usuario_asignado.username
                )

            data.append({
                'id': ticket.pk,
                'numero_ticket': ticket.numero_ticket,
                'titulo': ticket.titulo,
                'nombres': nombres,
                'estado': ticket.estado,
                'area_soporte': (
                    ticket.area_soporte.nombre
                    if ticket.area_soporte
                    else ''
                ),
                'asignado_a': asignado_a,
                'created_at': ticket.created_at,
                'departamento': ticket.departamento or '',
                'fecha_cierre': ticket.fecha_cierre,
            })

        # Opciones del filtro por área
        areas_queryset = AreaSoporte.objects.filter(is_active=True)

        if establecimiento_id and not request.user.is_superuser:
            areas_queryset = areas_queryset.filter(
                establecimiento_id=establecimiento_id
            )

        opciones_areas = [
            {
                'label': nombre,
                'value': nombre,
            }
            for nombre in areas_queryset.order_by('nombre')
            .values_list('nombre', flat=True)
            .distinct()
        ]

        # Opciones del filtro por estado
        opciones_estados = [
            {
                'label': label,
                'value': value,
            }
            for value, label in Ticket.ESTADOS
        ]

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
            'columnControl': {
                'area_soporte': opciones_areas,
                'estado': opciones_estados,
            },
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title

        establecimiento = getattr(
            self.request.user, 'establecimiento', None
        )

        if self.request.user.is_superuser:
            establecimiento_id = _as_int(
                self.request.GET.get('establecimiento'),
                establecimiento.pk if establecimiento else 1,
            )

            establecimiento = (
                    Establecimiento.objects.filter(
                        pk=establecimiento_id
                    ).first()
                    or establecimiento
            )

        if establecimiento is None:
            establecimiento = Establecimiento.objects.filter(
                pk=1
            ).first()

        context['establecimiento'] = establecimiento
        return context


class TicketCreateView(StandardCreateView):
    template_name = 'tickets/ticket_form.html'
    model = Ticket
    form_class = FormTicket
    title = 'Nuevo Ticket'
    success_url = reverse_lazy('soporte:list_soportes')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_list_url(self):
        return reverse_lazy('soporte:list_soportes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


class TicketUpdateView(StandardUpdateView):
    template_name = 'tickets/ticket_form.html'
    model = Ticket
    form_class = FormTicket
    title = 'Actualizar Ticket'
    success_url = reverse_lazy('soporte:ticket_editor_list')

    def get_queryset(self):
        queryset = Ticket.objects.filter(is_active=True)
        if not self.request.user.is_superuser:
            queryset = queryset.filter(establecimiento_id=self.request.user.establecimiento_id)
        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not form.is_bound and self.object.departamento:
            departamento = form.fields['departamento'].queryset.filter(
                nombre=self.object.departamento
            ).first()
            if departamento:
                form.initial['departamento'] = departamento.pk
        return form

    def get_list_url(self):
        return reverse_lazy('soporte:ticket_editor_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


class ListEditTicketView(LoginRequiredMixin, TemplateView):
    template_name = 'tickets/ticket_editor_list.html'
    title = 'Gestión de Tickets'

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') != 'search':
            return JsonResponse(
                {'error': 'Acción no válida'},
                status=400
            )

        draw = max(0, _as_int(request.POST.get('draw'), 1))
        start = max(0, _as_int(request.POST.get('start'), 0))
        length = _as_int(request.POST.get('length'), 25)

        if length < -1:
            length = 25

        establecimiento_id = getattr(
            request.user, 'establecimiento_id', None
        )

        queryset = Ticket.objects.filter(
            is_active=True
        ).select_related(
            'area_soporte',
            'funcionario',
            'asignado_a__usuario',
        )

        if not request.user.is_superuser:
            queryset = queryset.filter(
                establecimiento_id=establecimiento_id
            )

        # Total sin filtros de búsqueda
        records_total = queryset.count()

        # Búsqueda global
        search = request.POST.get('search[value]', '').strip()

        if search:
            queryset = queryset.filter(
                Q(numero_ticket__icontains=search) |
                Q(titulo__icontains=search) |
                Q(descripcion__icontains=search) |
                Q(nombres__icontains=search) |
                Q(correo__icontains=search) |
                Q(departamento__icontains=search) |
                Q(estado__icontains=search) |
                Q(area_soporte__nombre__icontains=search) |
                Q(funcionario__first_name__icontains=search) |
                Q(funcionario__last_name__icontains=search) |
                Q(funcionario__username__icontains=search) |
                Q(asignado_a__usuario__first_name__icontains=search) |
                Q(asignado_a__usuario__last_name__icontains=search) |
                Q(asignado_a__usuario__username__icontains=search)
            )

        # Filtro por estado: columna 3
        prefijo_estado = 'columns[3][columnControl][list]'
        estados = []

        for key, values in request.POST.lists():
            if (
                    key == prefijo_estado
                    or key.startswith(prefijo_estado + '[')
            ):
                estados.extend(values)

        if estados:
            queryset = queryset.filter(estado__in=estados)

        # Filtro por área de soporte: columna 4
        prefijo_area = 'columns[4][columnControl][list]'
        areas = []

        for key, values in request.POST.lists():
            if key == prefijo_area or key.startswith(prefijo_area + '['):
                areas.extend(values)

        if areas:
            queryset = queryset.filter(
                area_soporte__nombre__in=areas
            )

        # Ordenamiento: mismo orden que en ticket_datatable.js
        columnas = {
            0: 'numero_ticket',
            1: 'titulo',
            2: 'nombres',
            3: 'estado',
            4: 'area_soporte__nombre',
            5: 'asignado_a__usuario__username',
            6: 'created_at',
            7: 'fecha_cierre',
        }

        order_index = _as_int(
            request.POST.get('order[0][column]'), 6
        )
        order_dir = request.POST.get('order[0][dir]', 'desc')

        campo = columnas.get(order_index, 'created_at')

        if order_dir == 'desc':
            campo = f'-{campo}'

        queryset = queryset.order_by(campo, '-pk')

        # Total después de filtrar
        records_filtered = queryset.count()

        # Paginación
        if length != -1:
            queryset = queryset[start:start + length]

        # Datos con las claves que espera ticket_datatable.js
        data = []

        for ticket in queryset:
            funcionario = ticket.funcionario
            usuario_asignado = (
                ticket.asignado_a.usuario
                if ticket.asignado_a
                else None
            )

            nombres = ticket.nombres or ''

            if not nombres and funcionario:
                nombres = (
                        funcionario.get_full_name()
                        or funcionario.username
                )

            asignado_a = ''

            if usuario_asignado:
                asignado_a = (
                        usuario_asignado.get_full_name()
                        or usuario_asignado.username
                )

            data.append({
                'id': ticket.pk,
                'numero_ticket': ticket.numero_ticket,
                'titulo': ticket.titulo,
                'nombres': nombres,
                'estado': ticket.estado,
                'area_soporte': (
                    ticket.area_soporte.nombre
                    if ticket.area_soporte
                    else ''
                ),
                'asignado_a': asignado_a,
                'created_at': ticket.created_at,
                'fecha_cierre': ticket.fecha_cierre,
            })

        # Opciones del filtro por área
        areas_queryset = AreaSoporte.objects.filter(is_active=True)

        if not request.user.is_superuser:
            areas_queryset = areas_queryset.filter(
                establecimiento_id=establecimiento_id
            )

        opciones_areas = [
            {
                'label': nombre,
                'value': nombre,
            }
            for nombre in areas_queryset.order_by('nombre')
            .values_list('nombre', flat=True)
            .distinct()
        ]

        # Opciones del filtro por estado
        opciones_estados = [
            {
                'label': label,
                'value': value,
            }
            for value, label in Ticket.ESTADOS
        ]

        return JsonResponse({
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
            'columnControl': {
                'area_soporte': opciones_areas,
                'estado': opciones_estados,
            },
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title

        establecimiento = getattr(
            self.request.user, 'establecimiento', None
        )

        if self.request.user.is_superuser:
            establecimiento_id = _as_int(
                self.request.GET.get('establecimiento'),
                establecimiento.pk if establecimiento else 1,
            )

            establecimiento = (
                    Establecimiento.objects.filter(
                        pk=establecimiento_id
                    ).first()
                    or establecimiento
            )

        if establecimiento is None:
            establecimiento = Establecimiento.objects.filter(
                pk=1
            ).first()

        tipos = TipoSoporte.objects.filter(is_active=True)
        if not self.request.user.is_superuser:
            tipos = tipos.filter(establecimiento_id=self.request.user.establecimiento_id)
        context['tipos_soporte'] = tipos.order_by('nombre')
        context['establecimiento'] = establecimiento
        return context


@login_required
@require_POST
def tickets_eliminar(request, pk):
    queryset = Ticket.objects.all()

    if not request.user.is_superuser:
        queryset = queryset.filter(
            establecimiento_id=request.user.establecimiento_id
        )

    ticket = get_object_or_404(queryset, pk=pk)
    nombre = ticket.numero_ticket or ticket.titulo or f'Ticket #{ticket.pk}'

    try:
        ticket.is_active = False

        if hasattr(ticket, 'updated_by'):
            ticket.estado = 'CANCELADO'
            ticket.updated_by = request.user

        ticket.save()

        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': (
                f'El ticket "{nombre}" (ID: {pk}) '
                'fue eliminado correctamente.'
            ),
        })
    except Exception:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'Ocurrió un error al intentar eliminar el ticket.',
        }, status=400)


@login_required
@require_POST
def ticket_tomar(request, pk):
    ticket_qs = Ticket.objects.all()
    if not request.user.is_superuser:
        ticket_qs = ticket_qs.filter(establecimiento_id=request.user.establecimiento_id)
    ticket = get_object_or_404(ticket_qs, pk=pk)
    if hasattr(request.user, 'perfil_soporte') and request.user.perfil_soporte:
        ticket.asignado_a = request.user.perfil_soporte
        ticket.estado = 'EN PROCESO'
        ticket.save()
        messages.success(request, 'Ticket asignado correctamente')
    else:
        messages.error(request, 'No tienes un perfil de soporte asociado para tomar tickets')
    return redirect('soporte:ticket_editor_list')


@login_required
@require_POST
def ticket_cerrar(request, pk):
    ticket_qs = Ticket.objects.all()
    if not request.user.is_superuser:
        ticket_qs = ticket_qs.filter(establecimiento_id=request.user.establecimiento_id)
    ticket = get_object_or_404(ticket_qs, pk=pk)
    if request.method == 'POST':
        solucion = request.POST.get('solucion', '').strip()
        if not solucion:
            messages.error(request, 'Debe ingresar una solucion para cerrar el ticket.')
            return redirect('soporte:ticket_editor_list')
        tipo_soporte_id = request.POST.get('tipo_soporte')
        if tipo_soporte_id:
            try:
                tipo_qs = TipoSoporte.objects.all()
                if not request.user.is_superuser and hasattr(request.user,
                                                             'establecimiento') and request.user.establecimiento:
                    tipo_qs = tipo_qs.filter(establecimiento=request.user.establecimiento)
                ticket.tipo_soporte = tipo_qs.get(pk=tipo_soporte_id)
            except TipoSoporte.DoesNotExist:
                ticket.tipo_soporte = None
        ticket.solucion = solucion
        ticket.estado = 'CERRADO'
        if hasattr(request.user, 'perfil_soporte') and request.user.perfil_soporte:
            ticket.asignado_a = request.user.perfil_soporte
        ticket.is_active = False
        ticket.fecha_cierre = timezone.now()
        ticket.save()
        messages.success(request, 'Ticket cerrado correctamente')
    return redirect('soporte:ticket_editor_list')


# def enviar_correo_ticket_creado(ticket, usuario=None, correo_destinatario=None):
#     """
#     Envía notificación por correo al usuario cuando se crea un ticket correctamente
#     utilizando la configuración SMTP del establecimiento.
#     """
#     try:
#         # Para depuración / pruebas manuales con un correo específico:
#         # destinatario = ['jarot.fierro.c@redsalud.gob.cl']
#         if correo_destinatario:
#             destinatario = [correo_destinatario]
#         elif usuario and getattr(usuario, 'email', None):
#             destinatario = [usuario.email]
#         elif getattr(ticket, 'correo', None):
#             destinatario = [ticket.correo]
#         else:
#             destinatario = []
#         print(destinatario)
#
#         if not destinatario:
#             logger.warning(
#                 f"No se pudo enviar correo para el ticket {ticket.numero_ticket}: usuario o email no disponible.")
#             return False
#
#         establecimiento = ticket.establecimiento or getattr(usuario, 'establecimiento', None)
#         print(establecimiento)
#         if not establecimiento:
#             logger.warning(
#                 f"No se pudo enviar correo para el ticket {ticket.numero_ticket}: no tiene establecimiento asignado.")
#             return False
#
#         config = ConfiguracionCorreo.objects.filter(establecimiento=establecimiento, activo=True).first()
#         print(config)
#         if not config:
#             logger.warning(
#                 f"No existe configuración de correo activa para el establecimiento {establecimiento.nombre}.")
#             return False
#
#         departamento = _obtener_departamento_ticket(ticket, usuario)
#         asunto = f"Ticket #{ticket.numero_ticket} recibido exitosamente"
#         print(asunto, departamento)
#
#         nombre_destinatario = None
#         nombres = getattr(ticket, 'nombres', None)
#         apellidos = getattr(ticket, 'apellidos', None)
#         if nombres or apellidos:
#             nombre_destinatario = f"{nombres or ''} {apellidos or ''}".strip()
#         elif usuario:
#             nombre_destinatario = usuario.get_full_name() if hasattr(usuario,
#                                                                      'get_full_name') and usuario.get_full_name() else getattr(
#                 usuario, 'username', str(usuario))
#
#         context = {
#             'ticket': ticket,
#             'usuario': usuario or (type('Obj', (object,), {'get_full_name': lambda self: nombre_destinatario,
#                                                            'username': nombre_destinatario})() if nombre_destinatario else None),
#             'nombre_destinatario': nombre_destinatario,
#             'departamento': departamento,
#         }
#
#         return EmailService.send_email_with_config(
#             config=config,
#             subject=asunto,
#             recipient_list=destinatario,
#             template_name='tickets/emails/ticket_creado.html',
#             context=context
#         )
#     except Exception as e:
#         logger.error(
#             f"Error inesperado al intentar enviar correo de ticket {ticket.numero_ticket or ticket.id}: {str(e)}",
#             exc_info=True)
#         return False

class TicketHistorialView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = "tickets/historial_modal.html"
    context_object_name = "ticket"

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser and hasattr(self.request.user,
                                                          'establecimiento') and self.request.user.establecimiento:
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['eventos'] = self.get_historial_eventos(self.object)
        return context

    def get_historial_eventos(self, ticket):
        records = list(ticket.history.all().order_by('history_date', 'history_id'))
        eventos = []
        prev_record = None

        for record in records:
            if prev_record is None:
                # 1. Creación del ticket
                eventos.append({
                    'titulo': 'Ticket creado',
                    'fecha': record.history_date,
                    'detalle': 'Solicitud ingresada',
                    'icono': 'bi bi-plus-circle-fill',
                    'badge_bg': 'bg-primary',
                    'icon_bg': 'bg-primary text-white',
                    'usuario': record.history_user,
                })

                if record.asignado_a:
                    eventos.append({
                        'titulo': 'Ticket asignado',
                        'fecha': record.history_date,
                        'detalle': f'Asignado a {record.asignado_a}',
                        'icono': 'bi bi-person-check-fill',
                        'badge_bg': 'bg-info text-white',
                        'icon_bg': 'bg-info text-white',
                        'usuario': record.history_user,
                    })

                if record.estado != 'ABIERTO':
                    if record.estado in ('EN_PROCESO', 'EN PROCESO'):
                        eventos.append({
                            'titulo': 'En proceso',
                            'fecha': record.history_date,
                            'detalle': 'Técnico comenzó la atención',
                            'icono': 'bi bi-play-circle-fill',
                            'badge_bg': 'bg-warning text-dark',
                            'icon_bg': 'bg-warning text-dark',
                            'usuario': record.history_user,
                        })
                    elif record.estado == 'ESPERA':
                        eventos.append({
                            'titulo': 'En espera',
                            'fecha': record.history_date,
                            'detalle': 'Esperando información del usuario',
                            'icono': 'bi bi-pause-circle-fill',
                            'badge_bg': 'bg-info text-dark',
                            'icon_bg': 'bg-info text-white',
                            'usuario': record.history_user,
                        })
                    elif record.estado == 'CERRADO':
                        detalle = record.solucion.strip() if (
                                record.solucion and record.solucion.strip()) else 'Problema solucionado'
                        eventos.append({
                            'titulo': 'Cerrado',
                            'fecha': record.history_date,
                            'detalle': detalle,
                            'icono': 'bi bi-check-circle-fill',
                            'badge_bg': 'bg-danger text-white',
                            'icon_bg': 'bg-danger text-white',
                            'usuario': record.history_user,
                        })
                    elif record.estado == 'RECHAZADO':
                        detalle = record.solucion.strip() if (
                                record.solucion and record.solucion.strip()) else 'Ticket rechazado'
                        eventos.append({
                            'titulo': 'Rechazado',
                            'fecha': record.history_date,
                            'detalle': detalle,
                            'icono': 'bi bi-x-circle-fill',
                            'badge_bg': 'bg-danger text-white',
                            'icon_bg': 'bg-danger text-white',
                            'usuario': record.history_user,
                        })
            else:
                hubo_evento = False

                # 2. Asignación / cambio de técnico
                if prev_record.asignado_a_id != record.asignado_a_id:
                    hubo_evento = True
                    if not prev_record.asignado_a_id and record.asignado_a:
                        eventos.append({
                            'titulo': 'Ticket asignado',
                            'fecha': record.history_date,
                            'detalle': f'Asignado a {record.asignado_a}',
                            'icono': 'bi bi-person-check-fill',
                            'badge_bg': 'bg-info text-white',
                            'icon_bg': 'bg-info text-white',
                            'usuario': record.history_user,
                        })
                    elif record.asignado_a:
                        eventos.append({
                            'titulo': 'Ticket reasignado',
                            'fecha': record.history_date,
                            'detalle': f'Reasignado a {record.asignado_a}',
                            'icono': 'bi bi-arrow-left-right',
                            'badge_bg': 'bg-info text-white',
                            'icon_bg': 'bg-info text-white',
                            'usuario': record.history_user,
                        })
                    else:
                        eventos.append({
                            'titulo': 'Asignación removida',
                            'fecha': record.history_date,
                            'detalle': 'Se retiró la asignación del técnico',
                            'icono': 'bi bi-person-x-fill',
                            'badge_bg': 'bg-secondary text-white',
                            'icon_bg': 'bg-secondary text-white',
                            'usuario': record.history_user,
                        })

                # 3. Cambio de estado
                if prev_record.estado != record.estado:
                    hubo_evento = True
                    if record.estado in ('EN_PROCESO', 'EN PROCESO'):
                        detalle = 'Atención retomada' if prev_record.estado == 'ESPERA' else 'Técnico comenzó la atención'
                        eventos.append({
                            'titulo': 'En proceso',
                            'fecha': record.history_date,
                            'detalle': detalle,
                            'icono': 'bi bi-play-circle-fill',
                            'badge_bg': 'bg-warning text-dark',
                            'icon_bg': 'bg-warning text-dark',
                            'usuario': record.history_user,
                        })
                    elif record.estado == 'ESPERA':
                        eventos.append({
                            'titulo': 'En espera',
                            'fecha': record.history_date,
                            'detalle': 'Esperando información del usuario',
                            'icono': 'bi bi-pause-circle-fill',
                            'badge_bg': 'bg-info text-dark',
                            'icon_bg': 'bg-info text-white',
                            'usuario': record.history_user,
                        })
                    elif record.estado == 'CERRADO':
                        detalle = record.solucion.strip() if (
                                record.solucion and record.solucion.strip()) else 'Problema solucionado'
                        eventos.append({
                            'titulo': 'Cerrado',
                            'fecha': record.history_date,
                            'detalle': detalle,
                            'icono': 'bi bi-check-circle-fill',
                            'badge_bg': 'bg-danger text-white',
                            'icon_bg': 'bg-danger text-white',
                            'usuario': record.history_user,
                        })
                    elif record.estado == 'RECHAZADO':
                        detalle = record.solucion.strip() if (
                                record.solucion and record.solucion.strip()) else 'Ticket rechazado'
                        eventos.append({
                            'titulo': 'Rechazado',
                            'fecha': record.history_date,
                            'detalle': detalle,
                            'icono': 'bi bi-x-circle-fill',
                            'badge_bg': 'bg-danger text-white',
                            'icon_bg': 'bg-danger text-white',
                            'usuario': record.history_user,
                        })
                    elif record.estado == 'ABIERTO':
                        eventos.append({
                            'titulo': 'Abierto',
                            'fecha': record.history_date,
                            'detalle': 'Ticket reabierto' if prev_record.estado in ['CERRADO',
                                                                                    'RECHAZADO'] else 'Ticket en estado abierto',
                            'icono': 'bi bi-folder2-open',
                            'badge_bg': 'bg-primary text-white',
                            'icon_bg': 'bg-primary text-white',
                            'usuario': record.history_user,
                        })
                else:
                    # Si el estado sigue siendo CERRADO pero se cerró con fecha o solución actualizada
                    if record.estado == 'CERRADO' and (record.fecha_cierre and not prev_record.fecha_cierre or (
                            record.solucion and not prev_record.solucion)):
                        hubo_evento = True
                        detalle = record.solucion.strip() if (
                                record.solucion and record.solucion.strip()) else 'Problema solucionado'
                        eventos.append({
                            'titulo': 'Cerrado',
                            'fecha': record.history_date,
                            'detalle': detalle,
                            'icono': 'bi bi-check-circle-fill',
                            'badge_bg': 'bg-danger text-white',
                            'icon_bg': 'bg-danger text-white',
                            'usuario': record.history_user,
                        })

                # Si no hubo cambio de asignación ni de estado pero hubo cambios en otros campos
                if not hubo_evento and record.history_type == '~':
                    cambios = []
                    if prev_record.titulo != record.titulo:
                        cambios.append("Título modificado")
                    if prev_record.descripcion != record.descripcion:
                        cambios.append("Descripción modificada")
                    if prev_record.solucion != record.solucion and record.solucion:
                        cambios.append(f"Solución: {record.solucion.strip()}")
                    if prev_record.area_soporte_id != record.area_soporte_id:
                        cambios.append(f"Área: {record.area_soporte.nombre if record.area_soporte else '-'}")
                    if prev_record.tipo_soporte_id != record.tipo_soporte_id:
                        cambios.append(f"Tipo: {record.tipo_soporte.nombre if record.tipo_soporte else '-'}")

                    detalle = ", ".join(cambios) if cambios else "Ticket actualizado"
                    eventos.append({
                        'titulo': 'Ticket actualizado',
                        'fecha': record.history_date,
                        'detalle': detalle,
                        'icono': 'bi bi-pencil-fill',
                        'badge_bg': 'bg-secondary text-white',
                        'icon_bg': 'bg-secondary text-white',
                        'usuario': record.history_user,
                    })

            prev_record = record

        return eventos
