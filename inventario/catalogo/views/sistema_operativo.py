from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.views.generic import TemplateView

from catalogo.forms.sistema_operativo import FormSistemaOperativo
from catalogo.models import SistemaOperativo
from core.history import GenericHistoryListView
from core.mixin import DataTableMixin
from core.utils import IncludeUserFormCreate, IncludeUserFormUpdate

MODULE_NAME = 'SistemaOperativos'


class SistemaOperativoListView(LoginRequiredMixin, DataTableMixin, TemplateView):
    template_name = 'sistema_operativo/list.html'
    model = SistemaOperativo
    datatable_columns = ['ID', 'Nombre']
    datatable_order_fields = ['id', None, 'sistema_operativo__nombre']
    datatable_search_fields = ['nombre__icontains', 'sistema_operativo__nombre__icontains']

    url_detail = 'detail_sistemas_operativos'

    # url_update = 'update_sistemas_operativos'

    def get_url_update(self):
        user = self.request.user
        if getattr(user, 'rol', None) and user.rol.mantenedores == 2:
            return 'update_sistemas_operativos'
        return None

    def render_row(self, obj):
        return {
            'ID': obj.id,
            'Nombre': obj.nombre.upper(),
        }

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('datatable'):
            return self.get_datatable_response(request)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Listado de Sistema Operativos',
            'list_url': reverse_lazy('list_sistemas_operativos'),
            'create_url': reverse_lazy('create_sistemas_operativos'),
            'datatable_enabled': True,
            'datatable_order': [[0, 'asc']],
            'datatable_page_length': 100,
            'columns': self.datatable_columns,
        })
        return context


class SistemaOperativoDetailView(LoginRequiredMixin, DetailView):
    model = SistemaOperativo
    template_name = 'sistema_operativo/detail.html'

    def render_to_response(self, context, **response_kwargs):
        # Si es una solicitud AJAX, devolvemos solo el fragmento HTML
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            html = render_to_string(self.template_name, context=context, request=self.request)
            return HttpResponse(html)
        return super().render_to_response(context, **response_kwargs)


class SistemaOperativoCreateView(LoginRequiredMixin, IncludeUserFormCreate, CreateView):
    template_name = 'sistema_operativo/form.html'
    model = SistemaOperativo
    form_class = FormSistemaOperativo
    success_url = reverse_lazy('list_sistemas_operativos')

    def form_valid(self, form):
        messages.success(self.request, 'SistemaOperativo creada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Sistema Operativo'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        context['module_name'] = MODULE_NAME
        return context


class SistemaOperativoUpdateView(LoginRequiredMixin, IncludeUserFormUpdate, UpdateView):
    template_name = 'sistema_operativo/form.html'
    model = SistemaOperativo
    form_class = FormSistemaOperativo
    success_url = reverse_lazy('list_sistemas_operativos')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'SistemaOperativo creada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Sistema Operativo'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        context['module_name'] = MODULE_NAME
        return context


class SistemaOperativoHistoryListView(LoginRequiredMixin, GenericHistoryListView):
    base_model = SistemaOperativo
    template_name = 'history/list.html'
