from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.views.generic import TemplateView

from catalogo.forms.marca import FormMarca
from catalogo.models import Marca
from core.history import GenericHistoryListView
from core.mixin import DataTableMixin
from core.utils import IncludeUserFormCreate, IncludeUserFormUpdate

MODULE_NAME = 'Marcas'


class MarcaListView(LoginRequiredMixin, DataTableMixin, TemplateView):
    template_name = 'marca/list.html'
    model = Marca
    datatable_columns = ['ID', 'Nombre']
    datatable_order_fields = ['id', None, 'marca__nombre']
    datatable_search_fields = ['nombre__icontains', 'marca__nombre__icontains']

    url_detail = 'detail_marcas'

    # url_update = 'update_marcas'

    def get_url_update(self):
        user = self.request.user
        if getattr(user, 'rol', None) and user.rol.mantenedores == 2:
            return 'update_marcas'
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
            'title': 'Listado de Marcas',
            'list_url': reverse_lazy('list_marcas'),
            'create_url': reverse_lazy('marca_create'),
            'datatable_enabled': True,
            'datatable_order': [[0, 'asc']],
            'datatable_page_length': 100,
            'columns': self.datatable_columns,
        })
        return context


class MarcaDetailView(LoginRequiredMixin, DetailView):
    model = Marca
    template_name = 'marca/detail.html'

    def render_to_response(self, context, **response_kwargs):
        # Si es una solicitud AJAX, devolvemos solo el fragmento HTML
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            html = render_to_string(self.template_name, context=context, request=self.request)
            return HttpResponse(html)
        return super().render_to_response(context, **response_kwargs)


class MarcaCreateView(LoginRequiredMixin, IncludeUserFormCreate, CreateView):
    template_name = 'marca/form.html'
    model = Marca
    form_class = FormMarca
    success_url = reverse_lazy('list_marcas')

    def form_valid(self, form):
        messages.success(self.request, 'Marca creada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Marca'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        context['module_name'] = MODULE_NAME
        return context


class MarcaUpdateView(LoginRequiredMixin, IncludeUserFormUpdate, UpdateView):
    template_name = 'marca/form.html'
    model = Marca
    form_class = FormMarca
    success_url = reverse_lazy('list_marcas')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Marca creada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Marca'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        context['module_name'] = MODULE_NAME
        return context


class MarcaHistoryListView(LoginRequiredMixin, GenericHistoryListView):
    base_model = Marca
    template_name = 'history/list.html'
