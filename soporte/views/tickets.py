from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from core.utils import IncludeUserFormUpdate, IncludeUserFormCreate
from soporte.forms.forms_tickets import FormTicket
from soporte.models import Ticket

MODULE_NAME = 'Tickets'


class TicketCreateView(LoginRequiredMixin, CreateView, IncludeUserFormCreate):
    template_name = 'tickets/form.html'
    model = Ticket
    form_class = FormTicket
    success_url = reverse_lazy('ticket_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Ticket Generado correctamente')
        form.instance.departamento = self.request.user.departamento
        form.instance.establecimiento = self.request.user.establecimiento
        form.instance.created_by = self.request.user

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Ticket'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        context['module_name'] = MODULE_NAME
        return context


class TicketsUpdateView(LoginRequiredMixin, IncludeUserFormUpdate, UpdateView):
    template_name = 'tickets/form.html'
    model = Ticket
    form_class = FormTicket
    success_url = reverse_lazy('ticket_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Ticket actualizado correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)
