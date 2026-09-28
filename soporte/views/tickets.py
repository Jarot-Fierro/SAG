import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, DetailView

from core.models.configuracion_correo import ConfiguracionCorreo
from core.services.email_service import EmailService
from core.standard.views import StandardListView, StandardCreateView, StandardUpdateView, StandardDetailView
from soporte.filters.tickets import FiltroTicket
from soporte.forms.forms_tickets import FormTicket, FormTicketEditor
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


def enviar_correo_ticket_creado(ticket, usuario):
    """
    Envía notificación por correo al usuario cuando se crea un ticket correctamente
    utilizando la configuración SMTP del establecimiento.
    """
    try:
        # Para depuración / pruebas manuales con un correo específico:
        # destinatario = ['jarot.fierro.c@redsalud.gob.cl']
        destinatario = [usuario.email] if usuario and usuario.email else []

        if not destinatario:
            logger.warning(
                f"No se pudo enviar correo para el ticket {ticket.numero_ticket}: usuario o email no disponible.")
            return False

        establecimiento = ticket.establecimiento or getattr(usuario, 'establecimiento', None)
        if not establecimiento:
            logger.warning(
                f"No se pudo enviar correo para el ticket {ticket.numero_ticket}: no tiene establecimiento asignado.")
            return False

        config = ConfiguracionCorreo.objects.filter(establecimiento=establecimiento, activo=True).first()
        if not config:
            logger.warning(
                f"No existe configuración de correo activa para el establecimiento {establecimiento.nombre}.")
            return False

        departamento = _obtener_departamento_ticket(ticket, usuario)
        asunto = f"Ticket #{ticket.numero_ticket} recibido exitosamente"
        context = {
            'ticket': ticket,
            'usuario': usuario,
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


class TicketListView(StandardListView):
    model = Ticket
    filter_form_class = FiltroTicket
    template_name = "tickets/list.html"

    title = "Tickets"

    list_url_name = "soporte:ticket_list"
    create_url_name = "soporte:ticket_create"
    update_url_name = "soporte:ticket_update"
    delete_url_name = "soporte:ticket_update"

    def get_queryset(self):
        # Sobrescribimos para mostrar tanto activos como inactivos
        queryset = Ticket.objects.all().select_related(
            "establecimiento", "area_soporte", "funcionario", "asignado_a", "asignado_a__usuario"
        )

        # Aplicamos filtro de establecimiento similar a StandardBaseView
        if not self.request.user.is_superuser:
            queryset = queryset.filter(establecimiento=self.request.user.establecimiento)

        self.filter_form = self.get_filter_form()

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data

            if data.get("numero_ticket"):
                queryset = queryset.filter(numero_ticket__icontains=data["numero_ticket"])

            if data.get("titulo"):
                queryset = queryset.filter(titulo__icontains=data["titulo"])

            if data.get("area_soporte"):
                queryset = queryset.filter(area_soporte=data["area_soporte"])

            if data.get("estado"):
                queryset = queryset.filter(estado=data["estado"])

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_filter_form_kwargs(self):
        kwargs = {
            'data': self.request.GET or None,
        }

        try:
            self.filter_form_class(**kwargs, request=self.request)
            kwargs['request'] = self.request
        except TypeError:
            pass
        return kwargs


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


class TicketsUpdateView(StandardUpdateView):
    template_name = 'tickets/form.html'
    model = Ticket
    form_class = FormTicket
    success_url = reverse_lazy('soporte:ticket_list')
    title = 'Editar Ticket'
    module_name = MODULE_NAME


class TicketEditorListView(StandardListView):
    model = Ticket
    filter_form_class = FiltroTicket
    template_name = "tickets/list_editor.html"

    title = "Tickets"

    list_url_name = "soporte:ticket_list"
    create_url_name = "soporte:ticket_create"
    update_url_name = "soporte:ticket_editor_update"
    delete_url_name = "soporte:ticket_update"

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ["tickets/_table_list_editor.html"]
        return [self.template_name]

    def get_queryset(self):
        try:
            areas_usuario = self.request.user.perfil_soporte.area_soporte.all()
            queryset = super().get_queryset().select_related(
                "establecimiento", "area_soporte", "funcionario", "asignado_a", "asignado_a__usuario"
            ).filter(
                area_soporte__in=areas_usuario
            )
        except AttributeError:
            # Si el usuario no tiene perfil_soporte, no ve ningún ticket
            queryset = super().get_queryset().none()

        if self.filter_form and self.filter_form.is_valid():
            data = self.filter_form.cleaned_data

            if data.get("numero_ticket"):
                queryset = queryset.filter(numero_ticket__icontains=data["numero_ticket"])

            if data.get("titulo"):
                queryset = queryset.filter(titulo__icontains=data["titulo"])

            if data.get("area_soporte"):
                queryset = queryset.filter(area_soporte=data["area_soporte"])

            if data.get("estado"):
                queryset = queryset.filter(estado=data["estado"])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipos_soporte = TipoSoporte.objects.filter(is_active=True)
        if (
                not self.request.user.is_superuser
                and hasattr(self.request.user, "establecimiento")
                and self.request.user.establecimiento
        ):
            tipos_soporte = tipos_soporte.filter(establecimiento=self.request.user.establecimiento)

        try:
            areas_usuario = self.request.user.perfil_soporte.area_soporte.all()
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
                    if record.estado == 'EN_PROCESO':
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
                    if record.estado == 'EN_PROCESO':
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
    ticket = get_object_or_404(Ticket, pk=pk)
    ticket.is_active = False
    ticket.save()
    messages.success(request, 'Ticket desactivado correctamente')
    return redirect('soporte:ticket_editor_list')


@login_required
def ticket_tomar(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if hasattr(request.user, 'perfil_soporte') and request.user.perfil_soporte:
        ticket.asignado_a = request.user.perfil_soporte
        ticket.estado = 'EN_PROCESO'
        ticket.save()
        messages.success(request, 'Ticket asignado correctamente')
    else:
        messages.error(request, 'No tienes un perfil de soporte asociado para tomar tickets')
    return redirect('soporte:ticket_editor_list')


@login_required
def ticket_cerrar(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        solucion = request.POST.get('solucion')
        tipo_soporte_id = request.POST.get('tipo_soporte')
        if tipo_soporte_id:
            try:
                ticket.tipo_soporte = TipoSoporte.objects.get(pk=tipo_soporte_id)
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


class TicketEditorInactivosListView(StandardListView):
    model = Ticket
    filter_form_class = FiltroTicket
    template_name = "tickets/list_inactivos_editor.html"

    title = "Tickets"

    list_url_name = "soporte:ticket_list"
    create_url_name = "soporte:ticket_create"
    update_url_name = "soporte:ticket_update"
    delete_url_name = "soporte:ticket_update"

    def get_queryset(self):
        queryset = self.model.objects.all()

        # Filtrar por establecimiento si no es superusuario
        if (
                hasattr(self.model, "establecimiento")
                and not self.request.user.is_superuser
        ):
            queryset = queryset.filter(
                establecimiento=self.request.user.establecimiento
            )

        # Mostrar únicamente los desactivados
        queryset = queryset.filter(is_active=False)

        try:
            areas_usuario = self.request.user.perfil_soporte.area_soporte.all()
            queryset = queryset.filter(
                area_soporte__in=areas_usuario
            ).select_related(
                "establecimiento",
                "area_soporte",
                "funcionario",
                "asignado_a",
                "asignado_a__usuario"
            )
        except AttributeError:
            return queryset.none()

        self.filter_form = self.get_filter_form()

        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data

            if data.get("numero_ticket"):
                queryset = queryset.filter(
                    numero_ticket__icontains=data["numero_ticket"]
                )

            if data.get("titulo"):
                queryset = queryset.filter(
                    titulo__icontains=data["titulo"]
                )

            if data.get("area_soporte"):
                queryset = queryset.filter(
                    area_soporte=data["area_soporte"]
                )

        return queryset


class TicketsUpdateEditorView(StandardUpdateView):
    template_name = 'tickets/form_editor.html'
    model = Ticket
    form_class = FormTicketEditor
    success_url = reverse_lazy('soporte:ticket_editor_list')
    title = 'Editar Ticket'
    module_name = MODULE_NAME

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

        # Áreas del usuario
        try:
            perfil = user.perfil_soporte
            areas_usuario = perfil.area_soporte.all()
        except AttributeError:
            areas_usuario = AreaSoporte.objects.none()

        # Widgets del establecimiento
        stats_est = Ticket.objects.filter(establecimiento=user.establecimiento).values('estado').annotate(
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
            stats = Ticket.objects.filter(area_soporte=area).values('estado').annotate(total=Count('id'))
            area_data = {
                'area': area.nombre,
                'area_establecimiento': area.establecimiento.nombre,
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
        usuarios_soporte = PerfilSoporte.objects.filter(
            usuario__establecimiento=user.establecimiento,
            area_soporte__in=areas_usuario
        ).annotate(
            cerrados_count=Count('tickets_asignados', filter=Q(tickets_asignados__estado='CERRADO')),
            abiertos_count=Count('tickets_asignados', filter=Q(tickets_asignados__estado='ABIERTO'))
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
