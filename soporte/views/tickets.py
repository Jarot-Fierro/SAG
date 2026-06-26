from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, TemplateView

from core.utils import IncludeUserFormUpdate, IncludeUserFormCreate
from soporte.decorators import soporte_required
from soporte.forms.forms_tickets import FormTicket
from soporte.models import Ticket

MODULE_NAME = 'Tickets'


@method_decorator(soporte_required, name='dispatch')
class TicketListView(LoginRequiredMixin, TemplateView):
    template_name = 'tickets/list.html'

    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.filter(
            establecimiento=user.establecimiento,
            departamento=user.departamento
        )
        return queryset

    def get(self, request, *args, **kwargs):
        if request.GET.get('datatable'):
            return self.get_datatable_data(request)
        return super().get(request, *args, **kwargs)

    def get_datatable_data(self, request):
        queryset = self.get_queryset()

        # Búsqueda
        search_value = request.GET.get('search[value]', '')
        if search_value:
            queryset = queryset.filter(
                Q(numero_ticket__icontains=search_value) |
                Q(titulo__icontains=search_value) |
                Q(estado__icontains=search_value)
            )

        total_count = queryset.count()

        # Orden
        order_column_index = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')
        # El mapeo debe coincidir con las columnas definidas en el template:
        # 0: ID, 1: actions, 2: NRO TICKET, 3: TITULO, 4: ESTADO, 5: FECHA
        columns_mapping = {
            0: 'id',
            1: 'id',
            2: 'numero_ticket',
            3: 'titulo',
            4: 'estado',
            5: 'created_at'
        }

        order_column = columns_mapping.get(order_column_index, 'id')
        if order_dir == 'desc':
            order_column = f'-{order_column}'
        queryset = queryset.order_by(order_column)

        # Paginación
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        queryset = queryset[start:start + length]

        data = []
        for ticket in queryset:
            data.append({
                'ID': ticket.id,
                'actions': f'<a href="{reverse_lazy("soporte:ticket_update", kwargs={"pk": ticket.pk})}" class="btn btn-sm btn-info"><i class="fas fa-edit"></i></a>',
                'NRO TICKET': ticket.numero_ticket,
                'TITULO': ticket.titulo,
                'ESTADO': ticket.get_estado_display(),
                'FECHA': ticket.created_at.strftime('%d/%m/%Y %H:%M') if ticket.created_at else '',
            })

        # Contadores para el resumen (basados en el queryset filtrado por establecimiento/departamento)
        base_qs = self.get_queryset()

        response = {
            'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': total_count,
            'recordsFiltered': total_count,
            'data': data,
            'tickets_abiertos': base_qs.filter(estado='ABIERTO').count(),
            'tickets_proceso': base_qs.filter(estado='EN_PROCESO').count(),
            'tickets_resueltos': base_qs.filter(estado='CERRADO').count(),
            'total_tickets': base_qs.count(),
        }
        return JsonResponse(response)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Tickets'
        context['module_name'] = MODULE_NAME
        context['columns'] = ['NRO TICKET', 'TITULO', 'ESTADO', 'FECHA']
        context['datatable_enabled'] = True

        # Contadores iniciales para el primer renderizado
        base_qs = self.get_queryset()
        context['tickets_abiertos'] = base_qs.filter(estado='ABIERTO').count()
        context['tickets_proceso'] = base_qs.filter(estado='EN_PROCESO').count()
        context['tickets_resueltos'] = base_qs.filter(estado='CERRADO').count()
        context['total_tickets'] = base_qs.count()

        return context


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
