from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from core.models.establecimientos import Establecimiento
from soporte.forms.forms_tickets import FormTicket
from soporte.models import AreaSoporte, TipoSoporte
from soporte.models import Ticket
from core.standard.views import StandardCreateView, StandardUpdateView


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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
            is_active=True
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
