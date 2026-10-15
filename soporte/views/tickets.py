import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.text import Truncator
from django.views.generic import TemplateView, DetailView, ListView

from core.models.configuracion_correo import ConfiguracionCorreo
from core.services.email_service import EmailService
from core.standard.views import StandardCreateView, StandardUpdateView, StandardDetailView
from soporte.forms.forms_tickets import FormTicket, FormTicketEditor, FormTicketParaFuncionario
from soporte.models import Ticket, AreaSoporte, PerfilSoporte, TipoSoporte

logger = logging.getLogger(__name__)

MODULE_NAME = 'Tickets'


def _obtener_departamento_ticket(ticket, usuario=None):
    """
    Obtiene el departamento asociado al ticket o al usuario/funcionario solicitante si existe.
    """
    if hasattr(ticket, 'departamento') and ticket.departamento:
        return ticket.departamento

    user = usuario or ticket.funcionario
    if user:
        if hasattr(user, 'departamento') and user.departamento:
            return user.departamento
        if hasattr(user, 'funcionario') and user.funcionario:
            if hasattr(user.funcionario, 'unidad_organizacional') and user.funcionario.unidad_organizacional:
                uo = user.funcionario.unidad_organizacional
                if hasattr(uo, 'get_departamento'):
                    dep = uo.get_departamento()
                    if dep:
                        return dep
                return uo
            if hasattr(user.funcionario, 'departamento') and user.funcionario.departamento:
                return user.funcionario.departamento
    return None


def enviar_correo_ticket_creado(ticket, usuario=None, correo_destinatario=None):
    """
    Envía notificación por correo al usuario cuando se crea un ticket correctamente
    utilizando la configuración SMTP del establecimiento.
    """
    try:
        # Para depuración / pruebas manuales con un correo específico:
        # destinatario = ['jarot.fierro.c@redsalud.gob.cl']
        if correo_destinatario:
            destinatario = [correo_destinatario]
        elif usuario and getattr(usuario, 'email', None):
            destinatario = [usuario.email]
        elif getattr(ticket, 'correo', None):
            destinatario = [ticket.correo]
        else:
            destinatario = []
        print(destinatario)

        if not destinatario:
            logger.warning(
                f"No se pudo enviar correo para el ticket {ticket.numero_ticket}: usuario o email no disponible.")
            return False

        establecimiento = ticket.establecimiento or getattr(usuario, 'establecimiento', None)
        print(establecimiento)
        if not establecimiento:
            logger.warning(
                f"No se pudo enviar correo para el ticket {ticket.numero_ticket}: no tiene establecimiento asignado.")
            return False

        config = ConfiguracionCorreo.objects.filter(establecimiento=establecimiento, activo=True).first()
        print(config)
        if not config:
            logger.warning(
                f"No existe configuración de correo activa para el establecimiento {establecimiento.nombre}.")
            return False

        departamento = _obtener_departamento_ticket(ticket, usuario)
        asunto = f"Ticket #{ticket.numero_ticket} recibido exitosamente"
        print(asunto, departamento)

        nombre_destinatario = None
        nombres = getattr(ticket, 'nombres', None)
        apellidos = getattr(ticket, 'apellidos', None)
        if nombres or apellidos:
            nombre_destinatario = f"{nombres or ''} {apellidos or ''}".strip()
        elif usuario:
            nombre_destinatario = usuario.get_full_name() if hasattr(usuario,
                                                                     'get_full_name') and usuario.get_full_name() else getattr(
                usuario, 'username', str(usuario))

        context = {
            'ticket': ticket,
            'usuario': usuario or (type('Obj', (object,), {'get_full_name': lambda self: nombre_destinatario,
                                                           'username': nombre_destinatario})() if nombre_destinatario else None),
            'nombre_destinatario': nombre_destinatario,
            'departamento': departamento,
        }

        return EmailService.send_email_with_config(
            config=config,
            subject=asunto,
            recipient_list=destinatario,
            template_name='tickets/emails/ticket_creado.html',
            context=context
        )
    except Exception as e:
        logger.error(
            f"Error inesperado al intentar enviar correo de ticket {ticket.numero_ticket or ticket.id}: {str(e)}",
            exc_info=True)
        return False


def serialize_ticket(ticket):
    """
    Serializa una instancia de Ticket a un diccionario JSON simple para DataTables.
    """
    solicitante_nombre = None
    if ticket.nombres:
        solicitante_nombre = ticket.nombres
    elif ticket.funcionario:
        full_name = ticket.funcionario.get_full_name()
        solicitante_nombre = full_name if full_name else ticket.funcionario.username

    return {
        "id": ticket.pk,
        "numero_ticket": ticket.numero_ticket or f"TCK-{ticket.pk}",
        "titulo": Truncator(ticket.titulo).chars(30) if ticket.titulo else "",
        "titulo_completo": ticket.titulo or "",
        "nombres": solicitante_nombre or "",
        "funcionario": solicitante_nombre or "",
        "estado": ticket.estado,
        "estado_display": ticket.get_estado_display() if hasattr(ticket, 'get_estado_display') else ticket.estado,
        "area_soporte": str(ticket.area_soporte.nombre) if ticket.area_soporte else None,
        "area_soporte_id": ticket.area_soporte_id,
        "tipo_soporte": str(ticket.tipo_soporte.nombre) if ticket.tipo_soporte else None,
        "tipo_soporte_id": ticket.tipo_soporte_id,
        "asignado_a": str(ticket.asignado_a) if ticket.asignado_a else None,
        "asignado_a_id": ticket.asignado_a_id,
        "fecha_cierre": ticket.fecha_cierre.isoformat() if ticket.fecha_cierre else None,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "duracion_cierre": ticket.duracion_cierre or None,
        "is_active": ticket.is_active,
    }


class DataTableListViewMixin:
    """
    Mixin reutilizable para vistas de listado con DataTables y server-side processing.
    """
    columns = []
    searchable_columns = []
    serializer_function = staticmethod(serialize_ticket)

    def get(self, request, *args, **kwargs):
        if (
            request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.GET.get("format") == "json"
            or "draw" in request.GET
        ):
            return self.datatables_response(request)
        return super().get(request, *args, **kwargs)

    def datatables_response(self, request):
        queryset = self.get_queryset()

        draw = int(request.GET.get("draw", 1))
        start = max(int(request.GET.get("start", 0)), 0)
        length = int(request.GET.get("length", 10))

        records_total = queryset.count()

        # Búsqueda global
        search_value = request.GET.get("search[value]", "").strip()
        if search_value and self.searchable_columns:
            search_query = Q()
            for column in self.searchable_columns:
                search_query |= Q(**{f"{column}__icontains": search_value})
            queryset = queryset.filter(search_query)

        # Búsqueda por columna individual si aplica
        for i, col_name in enumerate(self.columns):
            col_search = request.GET.get(f"columns[{i}][search][value]", "").strip()
            if col_search and col_name:
                queryset = queryset.filter(**{f"{col_name}__icontains": col_search})

        records_filtered = queryset.count()

        # Ordenamiento
        order_column = request.GET.get("order[0][column]")
        order_dir = request.GET.get("order[0][dir]", "asc")

        if order_column is not None:
            try:
                col_idx = int(order_column)
                if 0 <= col_idx < len(self.columns):
                    field = self.columns[col_idx]
                    if field:
                        if order_dir == "desc":
                            field = f"-{field}"
                        queryset = queryset.order_by(field)
            except (ValueError, TypeError):
                pass

        if length != -1:
            queryset = queryset[start:start + min(length, 500)]

        data = [
            self.serializer_function(item)
            for item in queryset
        ]

        return JsonResponse({
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data,
        })


class TicketListView(LoginRequiredMixin, DataTableListViewMixin, ListView):
    model = Ticket
    template_name = "tickets/list.html"
    context_object_name = "tickets"

    view_title = "Mis Tickets"
    title = "Mis Tickets"
    view_type = "CBV"

    columns = [
        "numero_ticket",
        "titulo",
        "nombres",
        "estado",
        "area_soporte__nombre",
        "asignado_a__usuario__username",
        "created_at",
        "fecha_cierre",
    ]

    searchable_columns = [
        "numero_ticket",
        "titulo",
        "nombres",
        "funcionario__first_name",
        "funcionario__last_name",
        "funcionario__username",
        "estado",
        "area_soporte__nombre",
        "asignado_a__usuario__first_name",
        "asignado_a__usuario__last_name",
        "asignado_a__usuario__username",
    ]

    def get_queryset(self):
        queryset = self.model.objects.filter(is_active=True).select_related(
            "establecimiento", "area_soporte", "funcionario", "asignado_a", "asignado_a__usuario"
        )
        if (
            hasattr(self.request.user, "establecimiento")
            and self.request.user.establecimiento
            and not self.request.user.is_superuser
        ):
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = self.view_title
        context["title"] = self.title
        context["view_type"] = self.view_type
        return context


class TicketCreateView(StandardCreateView):
    template_name = 'tickets/form.html'
    model = Ticket
    form_class = FormTicket
    success_url = reverse_lazy('soporte:ticket_list')
    title = 'Nuevo Ticket'
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.funcionario = self.request.user
        form.instance.establecimiento = self.request.user.establecimiento
        response = super().form_valid(form)
        # El ticket ya fue creado y persistido con su ID y correlativo
        try:
            enviar_correo_ticket_creado(self.object, self.request.user)
        except Exception as e:
            logger.error(f"Error al intentar enviar el correo de confirmación de ticket: {str(e)}", exc_info=True)
        return response


class TicketParaFuncionarioCreateView(StandardCreateView):
    template_name = 'tickets/form_para_funcionario.html'
    model = Ticket
    form_class = FormTicketParaFuncionario
    success_url = reverse_lazy('soporte:ticket_list')
    title = 'Nuevo Ticket Para Funcionario'
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.establecimiento = self.request.user.establecimiento
        response = super().form_valid(form)
        # El ticket ya fue creado y persistido con su ID y correlativo
        try:
            enviar_correo_ticket_creado(self.object, correo_destinatario=self.object.correo)
        except Exception as e:
            logger.error(f"Error al intentar enviar el correo de confirmación de ticket: {str(e)}", exc_info=True)
        return response

class TicketsParaFuncionarioUpdateView(StandardUpdateView):
    template_name = 'tickets/form_para_funcionario.html'
    model = Ticket
    form_class = FormTicketParaFuncionario
    success_url = reverse_lazy('soporte:ticket_list')
    title = 'Editar Ticket'
    module_name = MODULE_NAME

    def get_queryset(self):
        queryset = super().get_queryset()
        if (
                not self.request.user.is_superuser
                and hasattr(self.request.user, 'establecimiento')
                and self.request.user.establecimiento
        ):
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)
        return queryset


class TicketsUpdateView(StandardUpdateView):
    template_name = 'tickets/form.html'
    model = Ticket
    form_class = FormTicket
    success_url = reverse_lazy('soporte:ticket_list')
    title = 'Editar Ticket'
    module_name = MODULE_NAME

    def get_queryset(self):
        queryset = super().get_queryset()
        if (
                not self.request.user.is_superuser
                and hasattr(self.request.user, 'establecimiento')
                and self.request.user.establecimiento
        ):
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)
        return queryset


class TicketEditorListView(LoginRequiredMixin, DataTableListViewMixin, ListView):
    model = Ticket
    template_name = "tickets/list_editor.html"
    context_object_name = "tickets"

    view_title = "Gestión de Tickets"
    title = "Gestión de Tickets"
    view_type = "CBV"

    columns = [
        "numero_ticket",
        "titulo",
        "estado",
        "nombres",
        "area_soporte__nombre",
        "asignado_a__usuario__username",
        "created_at",
    ]

    searchable_columns = [
        "numero_ticket",
        "titulo",
        "nombres",
        "funcionario__first_name",
        "funcionario__last_name",
        "funcionario__username",
        "estado",
        "area_soporte__nombre",
        "asignado_a__usuario__first_name",
        "asignado_a__usuario__last_name",
        "asignado_a__usuario__username",
    ]

    def get_queryset(self):
        try:
            areas_usuario = self.request.user.perfil_soporte.area_soporte.all()
            if (
                    hasattr(self.request.user, "establecimiento")
                    and self.request.user.establecimiento
                    and not self.request.user.is_superuser
            ):
                areas_usuario = areas_usuario.filter(establecimiento=self.request.user.establecimiento)

            queryset = self.model.objects.select_related(
                "establecimiento", "area_soporte", "funcionario", "asignado_a", "asignado_a__usuario"
            ).filter(
                area_soporte__in=areas_usuario, is_active=True
            )

            if (
                    hasattr(self.request.user, "establecimiento")
                    and self.request.user.establecimiento
                    and not self.request.user.is_superuser
            ):
                queryset = queryset.filter(establecimiento=self.request.user.establecimiento)
        except AttributeError:
            # Si el usuario no tiene perfil_soporte, no ve ningún ticket
            queryset = self.model.objects.none()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = self.view_title
        context["title"] = self.title
        context["view_type"] = self.view_type

        tipos_soporte = TipoSoporte.objects.filter(is_active=True)
        if (
                not self.request.user.is_superuser
                and hasattr(self.request.user, "establecimiento")
                and self.request.user.establecimiento
        ):
            tipos_soporte = tipos_soporte.filter(establecimiento=self.request.user.establecimiento)

        try:
            areas_usuario = self.request.user.perfil_soporte.area_soporte.all()
            if (
                    not self.request.user.is_superuser
                    and hasattr(self.request.user, "establecimiento")
                    and self.request.user.establecimiento
            ):
                areas_usuario = areas_usuario.filter(establecimiento=self.request.user.establecimiento)
            tipos_soporte = tipos_soporte.filter(area_soporte__in=areas_usuario).distinct()
        except AttributeError:
            tipos_soporte = tipos_soporte.none()

        context["tipos_soporte"] = tipos_soporte
        return context


class TicketDetailView(StandardDetailView):
    model = Ticket

    title = "Detalle del Ticket"
    module_name = MODULE_NAME
    back_url_name = "soporte:ticket_list"

    def get_queryset(self):
        queryset = super().get_queryset()
        if (
                not self.request.user.is_superuser
                and hasattr(self.request.user, 'establecimiento')
                and self.request.user.establecimiento
        ):
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)
        return queryset


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


@login_required
def ticket_delete(request, pk):
    ticket_qs = Ticket.objects.all()
    if not request.user.is_superuser and hasattr(request.user, 'establecimiento') and request.user.establecimiento:
        ticket_qs = ticket_qs.filter(establecimiento=request.user.establecimiento)
    ticket = get_object_or_404(ticket_qs, pk=pk)
    ticket.is_active = False
    ticket.estado = 'CANCELADO'
    ticket.solucion = "YO COMO USUARIO AUTORIZO CANCELAR ESTE TICKET"
    ticket.save()
    messages.success(request, 'Ticket desactivado correctamente')
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    if hasattr(request.user, 'perfil_soporte') and request.user.perfil_soporte:
        return redirect('soporte:ticket_editor_list')
    return redirect('soporte:ticket_list')


@login_required
def ticket_tomar(request, pk):
    ticket_qs = Ticket.objects.all()
    if not request.user.is_superuser and hasattr(request.user, 'establecimiento') and request.user.establecimiento:
        ticket_qs = ticket_qs.filter(establecimiento=request.user.establecimiento)
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
def ticket_cerrar(request, pk):
    ticket_qs = Ticket.objects.all()
    if not request.user.is_superuser and hasattr(request.user, 'establecimiento') and request.user.establecimiento:
        ticket_qs = ticket_qs.filter(establecimiento=request.user.establecimiento)
    ticket = get_object_or_404(ticket_qs, pk=pk)
    if request.method == 'POST':
        solucion = request.POST.get('solucion')
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


class TicketEditorInactivosListView(LoginRequiredMixin, DataTableListViewMixin, ListView):
    model = Ticket
    template_name = "tickets/list_inactivos_editor.html"
    context_object_name = "tickets"

    view_title = "Tickets Cerrados"
    title = "Tickets Cerrados"
    view_type = "CBV"

    columns = [
        "numero_ticket",
        "titulo",
        "estado",
        "nombres",
        "area_soporte__nombre",
        "asignado_a__usuario__username",
        "created_at",
        "fecha_cierre",
    ]

    searchable_columns = [
        "numero_ticket",
        "titulo",
        "nombres",
        "funcionario__first_name",
        "funcionario__last_name",
        "funcionario__username",
        "estado",
        "area_soporte__nombre",
        "asignado_a__usuario__first_name",
        "asignado_a__usuario__last_name",
        "asignado_a__usuario__username",
    ]

    def get_queryset(self):
        try:
            areas_usuario = self.request.user.perfil_soporte.area_soporte.all()
            if (
                    not self.request.user.is_superuser
                    and hasattr(self.request.user, "establecimiento")
                    and self.request.user.establecimiento
            ):
                areas_usuario = areas_usuario.filter(establecimiento=self.request.user.establecimiento)

            queryset = self.model.objects.filter(
                is_active=False,
                area_soporte__in=areas_usuario
            ).select_related(
                "establecimiento",
                "area_soporte",
                "funcionario",
                "asignado_a",
                "asignado_a__usuario"
            )

            if (
                    hasattr(self.request.user, "establecimiento")
                    and self.request.user.establecimiento
                    and not self.request.user.is_superuser
            ):
                queryset = queryset.filter(establecimiento=self.request.user.establecimiento)
        except AttributeError:
            queryset = self.model.objects.none()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["view_title"] = self.view_title
        context["title"] = self.title
        context["view_type"] = self.view_type
        return context


class TicketsUpdateEditorView(StandardUpdateView):
    template_name = 'tickets/form_editor.html'
    model = Ticket
    form_class = FormTicketEditor
    success_url = reverse_lazy('soporte:ticket_editor_list')
    title = 'Editar Ticket'
    module_name = MODULE_NAME

    def get_queryset(self):
        queryset = super().get_queryset()
        if (
                not self.request.user.is_superuser
                and hasattr(self.request.user, 'establecimiento')
                and self.request.user.establecimiento
        ):
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)
        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['instance_funcionario'] = self.object.funcionario
        return context


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


class SoporteListCBV(TicketListView):
    template_name = "tickets/list_v2.html"
    context_object_name = "anexos"

    view_title = "Soporte V2"
    title = "Soporte V2"
    view_type = "CBV"

    @staticmethod
    def serialize_ticket(ticket):
        return serialize_ticket(ticket)
