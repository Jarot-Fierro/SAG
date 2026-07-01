from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.views.generic import TemplateView

from catalogo.forms.licencia_os import FormLicenciaOs
from catalogo.models import LicenciaOs
from core.history import GenericHistoryListView
from core.mixin import DataTableMixin
from core.utils import IncludeUserFormCreate, IncludeUserFormUpdate

MODULE_NAME = 'LicenciaOss'


class LicenciaOsListView(LoginRequiredMixin, DataTableMixin, TemplateView):
    template_name = 'licencia_os/list.html'
    model = LicenciaOs
    datatable_columns = ['ID', 'Nombre']
    datatable_order_fields = ['id', None, 'licencia_os__nombre']
    datatable_search_fields = ['nombre__icontains', 'licencia_os__nombre__icontains']

    url_detail = 'detail_licencia_os'

    # url_update = 'update_licencia_os'

    def get_url_update(self):
        user = self.request.user
        if getattr(user, 'rol', None) and user.rol.mantenedores == 2:
            return 'update_licencia_os'
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
            'title': 'Listado de LicenciaOss',
            'list_url': reverse_lazy('list_licencia_os'),
            'create_url': reverse_lazy('licencia_os_create'),
            'datatable_enabled': True,
            'datatable_order': [[0, 'asc']],
            'datatable_page_length': 100,
            'columns': self.datatable_columns,
        })
        return context


class LicenciaOsDetailView(LoginRequiredMixin, DetailView):
    model = LicenciaOs
    template_name = 'licencia_os/detail.html'

    def render_to_response(self, context, **response_kwargs):
        # Si es una solicitud AJAX, devolvemos solo el fragmento HTML
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            html = render_to_string(self.template_name, context=context, request=self.request)
            return HttpResponse(html)
        return super().render_to_response(context, **response_kwargs)


class LicenciaOsCreateView(LoginRequiredMixin, IncludeUserFormCreate, CreateView):
    template_name = 'licencia_os/form.html'
    model = LicenciaOs
    form_class = FormLicenciaOs
    success_url = reverse_lazy('list_licencia_os')

    def form_valid(self, form):
        messages.success(self.request, 'LicenciaOs creada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo LicenciaOs'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        context['module_name'] = MODULE_NAME
        return context


class LicenciaOsUpdateView(LoginRequiredMixin, IncludeUserFormUpdate, UpdateView):
    template_name = 'licencia_os/form.html'
    model = LicenciaOs
    form_class = FormLicenciaOs
    success_url = reverse_lazy('list_licencia_os')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'LicenciaOs creada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar LicenciaOs'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        context['module_name'] = MODULE_NAME
        return context


class LicenciaOsHistoryListView(LoginRequiredMixin, GenericHistoryListView):
    base_model = LicenciaOs
    template_name = 'history/list.html'
