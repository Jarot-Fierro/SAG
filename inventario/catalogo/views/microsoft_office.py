from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.views.generic import TemplateView

from catalogo.forms.microsoft_office import FormMicrosoftOffice
from catalogo.models import MicrosoftOffice
from core.history import GenericHistoryListView
from core.mixin import DataTableMixin
from core.utils import IncludeUserFormCreate, IncludeUserFormUpdate

MODULE_NAME = 'MicrosoftOffices'


class MicrosoftOfficeListView(LoginRequiredMixin, DataTableMixin, TemplateView):
    template_name = 'microsoft_office/list.html'
    model = MicrosoftOffice
    datatable_columns = ['ID', 'Nombre']
    datatable_order_fields = ['id', None, 'microsoft_office__nombre']
    datatable_search_fields = ['nombre__icontains', 'microsoft_office__nombre__icontains']

    url_detail = 'detail_microsoft_office'

    # url_update = 'update_microsoft_office'

    def get_url_update(self):
        user = self.request.user
        if getattr(user, 'rol', None) and user.rol.mantenedores == 2:
            return 'update_microsoft_office'
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
            'title': 'Listado de Microsoft Offices',
            'list_url': reverse_lazy('list_microsoft_office'),
            'create_url': reverse_lazy('microsoft_office_create'),
            'datatable_enabled': True,
            'datatable_order': [[0, 'asc']],
            'datatable_page_length': 100,
            'columns': self.datatable_columns,
        })
        return context


class MicrosoftOfficeDetailView(LoginRequiredMixin, DetailView):
    model = MicrosoftOffice
    template_name = 'microsoft_office/detail.html'

    def render_to_response(self, context, **response_kwargs):
        # Si es una solicitud AJAX, devolvemos solo el fragmento HTML
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            html = render_to_string(self.template_name, context=context, request=self.request)
            return HttpResponse(html)
        return super().render_to_response(context, **response_kwargs)


class MicrosoftOfficeCreateView(LoginRequiredMixin, IncludeUserFormCreate, CreateView):
    template_name = 'microsoft_office/form.html'
    model = MicrosoftOffice
    form_class = FormMicrosoftOffice
    success_url = reverse_lazy('list_microsoft_office')

    def form_valid(self, form):
        messages.success(self.request, 'MicrosoftOffice creada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Microsoft Office'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        context['module_name'] = MODULE_NAME
        return context


class MicrosoftOfficeUpdateView(LoginRequiredMixin, IncludeUserFormUpdate, UpdateView):
    template_name = 'microsoft_office/form.html'
    model = MicrosoftOffice
    form_class = FormMicrosoftOffice
    success_url = reverse_lazy('list_microsoft_office')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'MicrosoftOffice creada correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hay errores en el formulario')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Microsoft Office'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        context['module_name'] = MODULE_NAME
        return context


class MicrosoftOfficeHistoryListView(LoginRequiredMixin, GenericHistoryListView):
    base_model = MicrosoftOffice
    template_name = 'history/list.html'
