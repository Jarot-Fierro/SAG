from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.views.generic import TemplateView

from catalogo.forms.ips import FormIps
from catalogo.models import Ips
from core.history import GenericHistoryListView
from core.mixin import DataTableMixin
from core.utils import IncludeUserFormCreate, IncludeUserFormUpdate

MODULE_NAME = 'Ips'


class IpsListView(LoginRequiredMixin, DataTableMixin, TemplateView):
    template_name = 'ips/list.html'
    model = Ips
    datatable_columns = ['ID', 'Ip', 'Asignado']
    datatable_order_fields = ['id', None, 'ip', 'asignacion_ip__activa']
    datatable_search_fields = ['ip__icontains']

    url_detail = 'detail_ips'

    # url_update = 'update_ips'

    def get_url_update(self):
        user = self.request.user
        if getattr(user, 'rol', None) and user.rol.mantenedores == 2:
            return 'update_ips'
        return None

    def get_base_queryset(self):
        return super().get_base_queryset().select_related('asignacion_ip')

    def render_row(self, obj):
        asignada = False
        try:
            if obj.asignacion_ip and obj.asignacion_ip.activa:
                asignada = True
        except Exception:
            pass

        return {
            'ID': obj.id,
            'Ip': obj.ip.upper(),
            'Asignado': (
                '<span class="badge bg-danger p-2">Asignada</span>'
                if asignada
                else '<span class="badge bg-success p-2">Libre</span>'
            ),
        }

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('datatable'):
            return self.get_datatable_response(request)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Listado de Ips',
            'list_url': reverse_lazy('list_ips'),
            'create_url': reverse_lazy('create_ips'),
            'datatable_enabled': True,
            'datatable_order': [[0, 'asc']],
            'datatable_page_length': 100,
            'columns': self.datatable_columns,
        })
        return context


class IpsDetailView(LoginRequiredMixin, DetailView):
    model = Ips
    template_name = 'ips/detail.html'

    def render_to_response(self, context, **response_kwargs):
        # Si es una solicitud AJAX, devolvemos solo el fragmento HTML
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            html = render_to_string(self.template_name, context=context, request=self.request)
            return HttpResponse(html)
        return super().render_to_response(context, **response_kwargs)


class IpsCreateView(LoginRequiredMixin, IncludeUserFormCreate, CreateView):
    template_name = 'ips/form.html'
    model = Ips
    form_class = FormIps
    success_url = reverse_lazy('list_ips')

    def form_valid(self, form):
        messages.success(self.request, 'Ips creada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Ips'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        context['module_name'] = MODULE_NAME
        return context


class IpsUpdateView(LoginRequiredMixin, IncludeUserFormUpdate, UpdateView):
    template_name = 'ips/form.html'
    model = Ips
    form_class = FormIps
    success_url = reverse_lazy('list_ips')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Ips creada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Ips'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        context['module_name'] = MODULE_NAME
        return context


class IpsHistoryListView(LoginRequiredMixin, GenericHistoryListView):
    base_model = Ips
    template_name = 'history/list.html'
