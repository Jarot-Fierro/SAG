from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy

from core.standard.views import StandardListView, StandardCreateView, StandardUpdateView, StandardDetailView
from soporte.filters.tickets import FiltroTicket
from soporte.forms.forms_tickets import FormTicket
from soporte.models import Ticket

MODULE_NAME = 'Tickets'


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
        queryset = super().get_queryset().select_related("establecimiento", "area_soporte", "funcionario")

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

    def form_valid(self, form):
        form.instance.funcionario = self.request.user

        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


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
    update_url_name = "soporte:ticket_update"
    delete_url_name = "soporte:ticket_update"

    def get_queryset(self):
        try:
            areas_usuario = self.request.user.perfil_soporte.area_soporte.all()
            queryset = super().get_queryset().select_related("establecimiento", "area_soporte", "funcionario").filter(
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


class TicketDetailView(StandardDetailView):
    model = Ticket

    title = "Detalle del Ticket"
    module_name = MODULE_NAME
    back_url_name = "soporte:ticket_list"


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
    ticket.asignado_a = request.user
    ticket.save()
    messages.success(request, 'Ticket asignado correctamente')
    return redirect('soporte:ticket_editor_list')


@login_required
def ticket_cerrar(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    ticket.estado = 'CERRADO'
    ticket.is_active = False
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
                "funcionario"
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

            if data.get("estado"):
                queryset = queryset.filter(
                    estado=data["estado"]
                )

        return queryset
