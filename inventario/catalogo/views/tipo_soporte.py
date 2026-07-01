from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.views.generic import TemplateView

from catalogo.forms.tipo_soporte import FormTipoSoporte
from catalogo.models import TipoSoporte
from core.history import GenericHistoryListView
from core.mixin import DataTableMixin
from core.utils import IncludeUserFormCreate, IncludeUserFormUpdate

MODULE_NAME = 'Tipo Soporte'


class TipoSoporteListView(LoginRequiredMixin, DataTableMixin, TemplateView):
    template_name = 'tipo_soporte/list.html'
    model = TipoSoporte
    datatable_columns = ['ID', 'Nombre']
    datatable_order_fields = ['id', None, 'tipo_soporte__nombre']
    datatable_search_fields = ['nombre__icontains', 'tipo_soporte__nombre__icontains']

    url_detail = 'detail_tipo_soporte'

    # url_update = 'update_tipo_soporte'

    def get_url_update(self):
        user = self.request.user
        if getattr(user, 'rol', None) and user.rol.mantenedores == 2:
            return 'update_tipo_soporte'
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
            'title': 'Listado de Tipo Soporte',
            'list_url': reverse_lazy('list_tipo_soporte'),
            'create_url': reverse_lazy('create_tipo_soporte'),
            'datatable_enabled': True,
            'datatable_order': [[0, 'asc']],
            'datatable_page_length': 100,
            'columns': self.datatable_columns,
        })
        return context


class TipoSoporteDetailView(LoginRequiredMixin, DetailView):
    model = TipoSoporte
    template_name = 'tipo_soporte/detail.html'

    def render_to_response(self, context, **response_kwargs):
        # Si es una solicitud AJAX, devolvemos solo el fragmento HTML
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            html = render_to_string(self.template_name, context=context, request=self.request)
            return HttpResponse(html)
        return super().render_to_response(context, **response_kwargs)


class TipoSoporteCreateView(LoginRequiredMixin, IncludeUserFormCreate, CreateView):
    template_name = 'tipo_soporte/form.html'
    model = TipoSoporte
    form_class = FormTipoSoporte
    success_url = reverse_lazy('list_tipo_soporte')

    def form_valid(self, form):
        messages.success(self.request, 'TipoSoporte creada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Tipo Soporte'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        context['module_name'] = MODULE_NAME
        return context


class TipoSoporteUpdateView(LoginRequiredMixin, IncludeUserFormUpdate, UpdateView):
    template_name = 'tipo_soporte/form.html'
    model = TipoSoporte
    form_class = FormTipoSoporte
    success_url = reverse_lazy('list_tipo_soporte')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'TipoSoporte creada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Tipo Soporte'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        context['module_name'] = MODULE_NAME
        return context


class TipoSoporteHistoryListView(LoginRequiredMixin, GenericHistoryListView):
    base_model = TipoSoporte
    template_name = 'history/list.html'
