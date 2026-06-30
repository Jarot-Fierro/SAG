from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView

from core.utils import IncludeUserFormUpdate, IncludeUserFormCreate
from soporte.decorators import soporte_required
from soporte.forms.forms_tickets import FormTicket, FormTicketEditor
from soporte.models import Ticket

MODULE_NAME = 'Tickets'


def list_tickets(request):
    # Obtener todos los tickets inicialmente
    tickets = Ticket.objects.filter(is_active=True).order_by('created_at')

    # Obtener parámetros de filtrado
    titulo = request.GET.get('titulo')
    area_soporte = request.GET.get('area_soporte')
    tipo_soporte = request.GET.get('tipo_soporte')
    funcionario = request.GET.get('funcionario')
    estado = request.GET.get('estado')

    # Aplicar filtros de forma acumulativa
    if titulo:
        tickets = tickets.filter(titulo__icontains=titulo, is_active=True)
    if area_soporte:
        tickets = tickets.filter(area_soporte=area_soporte, is_active=True)
    if tipo_soporte:
        tickets = tickets.filter(tipo_soporte_id=tipo_soporte, is_active=True)
    if funcionario:
        tickets = tickets.filter(funcionario__username__icontains=funcionario, is_active=True)
    if estado:
        tickets = tickets.filter(estado=estado, is_active=True)

    # Paginación
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tickets/list.html', {'page_obj': page_obj})


@login_required
@soporte_required
def ticket_delete(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    ticket.is_active = False
    ticket.save()
    messages.success(request, 'Ticket desactivado correctamente')
    return redirect('soporte:ticket_list')


@method_decorator(soporte_required, name='dispatch')
class TicketCreateView(LoginRequiredMixin, CreateView, IncludeUserFormCreate):
    template_name = 'tickets/form.html'
    model = Ticket
    form_class = FormTicket
    success_url = reverse_lazy('soporte:ticket_list')

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


@method_decorator(soporte_required, name='dispatch')
class TicketsUpdateView(LoginRequiredMixin, IncludeUserFormUpdate, UpdateView):
    template_name = 'tickets/form.html'
    model = Ticket
    form_class = FormTicket
    success_url = reverse_lazy('soporte:ticket_list')

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


@method_decorator(soporte_required, name='dispatch')
class TicketEditorUpdateView(LoginRequiredMixin, IncludeUserFormUpdate, UpdateView):
    template_name = 'tickets/form_editor.html'
    model = Ticket
    form_class = FormTicketEditor
    success_url = reverse_lazy('soporte:ticket_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Ticket actualizado correctamente (Editor)')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)
