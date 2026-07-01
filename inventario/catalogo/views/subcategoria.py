from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.views.generic import TemplateView

from catalogo.forms.subcategoria import FormSubCategoria
from catalogo.models import SubCategoria
from core.history import GenericHistoryListView
from core.mixin import DataTableMixin
from core.utils import IncludeUserFormCreate, IncludeUserFormUpdate

MODULE_NAME = 'SubCategorias'


class SubCategoriaListView(LoginRequiredMixin, DataTableMixin, TemplateView):
    template_name = 'subcategoria/list.html'
    model = SubCategoria
    datatable_columns = ['ID', 'Nombre', 'Categoria']
    datatable_order_fields = ['id', None, 'nombre', 'categoria__nombre']
    datatable_search_fields = ['nombre__icontains', 'categoria__nombre__icontains']

    url_detail = 'detail_subcategorias'

    # url_update = 'update_subcategorias'

    def get_url_update(self):
        user = self.request.user
        if getattr(user, 'rol', None) and user.rol.mantenedores == 2:
            return 'update_subcategorias'
        return None

    def render_row(self, obj):
        return {
            'ID': obj.id,
            'Nombre': obj.nombre.upper(),
            'Categoria': obj.categoria.nombre.upper(),
        }

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('datatable'):
            return self.get_datatable_response(request)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Listado de SubCategorias',
            'list_url': reverse_lazy('list_subcategorias'),
            'create_url': reverse_lazy('create_subcategorias'),
            'datatable_enabled': True,
            'datatable_order': [[0, 'asc']],
            'datatable_page_length': 100,
            'columns': self.datatable_columns,
        })
        return context


class SubCategoriaDetailView(LoginRequiredMixin, DetailView):
    model = SubCategoria
    template_name = 'subcategoria/detail.html'

    def render_to_response(self, context, **response_kwargs):
        # Si es una solicitud AJAX, devolvemos solo el fragmento HTML
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            html = render_to_string(self.template_name, context=context, request=self.request)
            return HttpResponse(html)
        return super().render_to_response(context, **response_kwargs)


class SubCategoriaCreateView(LoginRequiredMixin, IncludeUserFormCreate, CreateView):
    template_name = 'subcategoria/form.html'
    model = SubCategoria
    form_class = FormSubCategoria
    success_url = reverse_lazy('list_subcategorias')

    def form_valid(self, form):
        messages.success(self.request, 'SubCategoria creada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo SubCategoria'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        context['module_name'] = MODULE_NAME
        return context


class SubCategoriaUpdateView(LoginRequiredMixin, IncludeUserFormUpdate, UpdateView):
    template_name = 'subcategoria/form.html'
    model = SubCategoria
    form_class = FormSubCategoria
    success_url = reverse_lazy('list_subcategorias')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'SubCategoria creada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar SubCategoria'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        context['module_name'] = MODULE_NAME
        return context


class SubCategoriaHistoryListView(LoginRequiredMixin, GenericHistoryListView):
    base_model = SubCategoria
    template_name = 'history/list.html'
