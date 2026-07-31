from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy

from core.models import User
from core.models.funcionario import Funcionario
from core.standard.views import StandardListView, StandardCreateView, StandardUpdateView
from soporte.filters.tickets import FiltroTicket
from soporte.forms.forms_tickets import FormTicket, FormTicketEditor
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


@login_required
def ticket_delete(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    ticket.is_active = False
    ticket.save()
    messages.success(request, 'Ticket desactivado correctamente')
    return redirect('soporte:ticket_list')


class TicketCreateView(StandardCreateView):
    template_name = 'tickets/form.html'
    model = Ticket
    form_class = FormTicket
    success_url = reverse_lazy('soporte:ticket_list')
    title = 'Nuevo Ticket'
    module_name = MODULE_NAME

    def form_valid(self, form):
        get_funcionario = Funcionario.objects.filter(rut=self.request.user.username).first()
        if get_funcionario:
            form.instance.funcionario = User.objects.filter(username=get_funcionario.rut).first()

        return super().form_valid(form)


class TicketsUpdateView(StandardUpdateView):
    template_name = 'tickets/form.html'
    model = Ticket
    form_class = FormTicket
    success_url = reverse_lazy('soporte:ticket_list')
    title = 'Editar Ticket'
    module_name = MODULE_NAME


class TicketEditorUpdateView(StandardUpdateView):
    template_name = 'tickets/form_editor.html'
    model = Ticket
    form_class = FormTicketEditor
    success_url = reverse_lazy('soporte:ticket_list')
    title = 'Editor de Ticket'
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
