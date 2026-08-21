from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy, NoReverseMatch
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DetailView


class StandardBaseView(LoginRequiredMixin):
    template_name = 'mantenedores/form.html'
    success_url = None
    module_name = 'Mantenedor'
    title = 'Mantenedor'
    list_url_name = None
    create_url_name = None
    update_url_name = None
    delete_url_name = None
    detail_url_name = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def get_queryset(self):
        queryset = self.model.objects.all()

        if (hasattr(self.model, "establecimiento") and not self.request.user.is_superuser):
            queryset = queryset.filter(
                establecimiento=self.request.user.establecimiento
            )
        if hasattr(self.model, "is_active"):
            queryset = queryset.filter(is_active=True)
        elif hasattr(self.model, "activo"):
            queryset = queryset.filter(activo=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['module_name'] = getattr(self, 'module_name', self.title)
        context['list_url_name'] = getattr(self, 'list_url_name', None)
        context['create_url_name'] = getattr(self, 'create_url_name', None)
        context['update_url_name'] = getattr(self, 'update_url_name', None)
        context['delete_url_name'] = getattr(self, 'delete_url_name', None)
        context['detail_url_name'] = getattr(self, 'detail_url_name', None)
        context['list_url'] = self.get_list_url()
        context['create_url'] = self.get_create_url()
        context['update_url'] = self.get_update_url()
        context['delete_url'] = self.get_delete_url()
        context['detail_url'] = self.get_detail_url()
        return context

    def get_list_url(self):
        url_name = getattr(self, 'list_url_name', None)
        if url_name:
            try:
                return reverse(url_name)
            except (NoReverseMatch, Exception):
                return '#'
        return '#'

    def get_create_url(self):
        url_name = getattr(self, 'create_url_name', None)
        if url_name:
            try:
                return reverse(url_name)
            except (NoReverseMatch, Exception):
                return '#'
        return '#'

    def get_update_url(self, obj=None):
        url_name = getattr(self, 'update_url_name', None)
        if url_name:
            try:
                if obj is not None:
                    pk = getattr(obj, 'pk', obj)
                    return reverse(url_name, args=[pk])
                return reverse(url_name)
            except (NoReverseMatch, Exception):
                return '#'
        return '#'

    def get_delete_url(self, obj=None):
        url_name = getattr(self, 'delete_url_name', None)
        if url_name:
            try:
                if obj is not None:
                    pk = getattr(obj, 'pk', obj)
                    return reverse(url_name, args=[pk])
                return reverse(url_name)
            except (NoReverseMatch, Exception):
                return '#'
        return '#'

    def get_detail_url(self, obj=None):
        url_name = getattr(self, 'detail_url_name', None)
        if url_name:
            try:
                if obj is not None:
                    pk = getattr(obj, 'pk', obj)
                    return reverse(url_name, args=[pk])
                return reverse(url_name)
            except (NoReverseMatch, Exception):
                return '#'
        return '#'


class StandardListView(StandardBaseView, ListView):
    template_name = 'mantenedores/list.html'
    context_object_name = 'objetos'
    paginate_by = 10
    search_fields = ['nombre']
    filter_form_class = None

    def get_filter_form_kwargs(self):
        kwargs = {
            'data': self.request.GET or None,
        }
        return kwargs

    def get_filter_form(self):
        if self.filter_form_class:
            return self.filter_form_class(**self.get_filter_form_kwargs())
        return None

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filter_form = self.get_filter_form()

        # Búsqueda simple por 'q'
        query = self.request.GET.get('q')
        if query:
            search_query = Q()
            for field in self.search_fields:
                search_query |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = getattr(self, 'filter_form', self.get_filter_form())
        context['list_url_name'] = getattr(self, 'list_url_name', None)
        context['create_url_name'] = getattr(self, 'create_url_name', None)
        context['update_url_name'] = getattr(self, 'update_url_name', None)
        context['delete_url_name'] = getattr(self, 'delete_url_name', None)
        context['detail_url_name'] = getattr(self, 'detail_url_name', None)
        context['list_url'] = self.get_list_url()
        context['create_url'] = self.get_create_url()
        context['update_url'] = self.get_update_url()
        context['delete_url'] = self.get_delete_url()
        context['detail_url'] = self.get_detail_url()
        context['q'] = self.request.GET.get('q', '')
        return context


class StandardCreateView(StandardBaseView, CreateView):
    def form_valid(self, form):
        if hasattr(form.instance, 'establecimiento') and not form.instance.establecimiento:
            form.instance.establecimiento = self.request.user.establecimiento

        if hasattr(form.instance, 'created_by'):
            form.instance.created_by = self.request.user

        messages.success(self.request, f'{self.model._meta.verbose_name} creado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'add'
        context['module_name'] = getattr(self, 'module_name', self.title)
        return context


class StandardUpdateView(StandardBaseView, UpdateView):
    def form_valid(self, form):
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user

        messages.success(self.request, f'{self.model._meta.verbose_name} actualizado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'edit'
        context['module_name'] = getattr(self, 'module_name', self.title)
        return context


class StandardDetailView(StandardBaseView, DetailView):
    """
    Vista genérica para visualizar el detalle de un registro en un modal.
    Extrae automáticamente los campos del modelo para su visualización.
    """
    template_name = 'mantenedores/detail_modal.html'
    context_object_name = 'object'
    title = ''
    module_name = ''
    exclude_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'history']

    def get_detail_fields(self):
        """
        Genera automáticamente la lista de campos a mostrar basándose en la metadata del modelo.
        """
        obj = self.get_object()
        fields_data = []
        exclude = getattr(self, 'exclude_fields', [])

        for field in obj._meta.fields:
            if field.name in exclude:
                continue

            label = field.verbose_name
            # Manejo de ChoiceField para mostrar el valor legible
            if field.choices:
                value = getattr(obj, f'get_{field.name}_display')()
            else:
                value = getattr(obj, field.name)

            fields_data.append({
                'label': label,
                'value': value,
                'name': field.name,
                'type': field.get_internal_type()
            })
        return fields_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_name'] = self.module_name
        context['detail_fields'] = self.get_detail_fields()
        return context


@require_POST
def catalogo_desactivar(request, pk, model, redirect_url_name):
    # Intentamos filtrar por establecimiento si el modelo lo tiene
    filter_kwargs = {'pk': pk}
    if hasattr(model, 'establecimiento'):
        filter_kwargs['establecimiento'] = request.user.establecimiento

    obj = get_object_or_404(model, **filter_kwargs)

    if hasattr(obj, 'is_active'):
        obj.is_active = False
    elif hasattr(obj, 'activo'):
        obj.activo = False

    obj.save()
    messages.success(request, f'{obj} desactivado correctamente.')
    return redirect(redirect_url_name)
