from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

from ..forms.catalogo import (
    FormMarca, FormContrato, FormIps, FormJefeTic, FormModelo, FormPropietario
)
from ..models.catalogo import (
    Marca, Contrato, Ips, JefeTic,
    Modelo, Propietario,
)


class CatalogoBaseView(LoginRequiredMixin):
    template_name = 'gestion_tic/catalogo/form.html'
    success_url = None
    module_name = 'Catálogo'
    title = 'Mantenedor'

    def get_queryset(self):
        return self.model.objects.filter(
            establecimiento=self.request.user.establecimiento,
            is_active=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['list_url'] = self.get_list_url()
        context['create_url'] = self.get_create_url()
        return context

    def get_list_url(self):
        url_name = getattr(self, 'list_url_name', None)
        if url_name:
            return reverse_lazy(url_name)
        return ''

    def get_create_url(self):
        return ''


class CatalogoListView(CatalogoBaseView, ListView):
    template_name = 'gestion_tic/catalogo/list.html'
    context_object_name = 'objetos'
    paginate_by = 10
    search_fields = ['nombre']

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            search_query = Q()
            for field in self.search_fields:
                search_query |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update_url_name'] = self.update_url_name
        context['delete_url_name'] = self.delete_url_name
        context['q'] = self.request.GET.get('q', '')
        return context


class CatalogoCreateView(CatalogoBaseView, CreateView):
    def form_valid(self, form):
        form.instance.establecimiento = self.request.user.establecimiento
        messages.success(self.request, f'{self.model._meta.verbose_name} creado correctamente.')
        return super().form_valid(form)


class CatalogoUpdateView(CatalogoBaseView, UpdateView):
    def form_valid(self, form):
        messages.success(self.request, f'{self.model._meta.verbose_name} actualizado correctamente.')
        return super().form_valid(form)


def catalogo_desactivar(request, pk, model, redirect_url_name):
    obj = get_object_or_404(model, pk=pk, establecimiento=request.user.establecimiento)
    obj.is_active = False
    obj.save()
    messages.success(request, f'{obj} desactivado correctamente.')
    return redirect(redirect_url_name)


# --- Implementación para Marca ---

class MarcaListView(CatalogoListView):
    model = Marca
    title = 'Listado de Marcas'
    list_url_name = 'gestion_tic:marca_list'
    update_url_name = 'gestion_tic:marca_update'
    delete_url_name = 'gestion_tic:marca_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:marca_create')

    def get_queryset(self):
        return super().get_queryset().all()


class MarcaCreateView(CatalogoCreateView):
    model = Marca
    form_class = FormMarca
    title = 'Crear Marca'
    success_url = reverse_lazy('gestion_tic:marca_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:marca_list')


class MarcaUpdateView(CatalogoUpdateView):
    model = Marca
    form_class = FormMarca
    title = 'Editar Marca'
    success_url = reverse_lazy('gestion_tic:marca_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:marca_list')


def marca_desactivar(request, pk):
    return catalogo_desactivar(request, pk, Marca, 'gestion_tic:marca_list')


# --- Implementación para Ips ---

class IpsListView(CatalogoListView):
    model = Ips
    title = 'Listado de Direcciones IP'
    list_url_name = 'gestion_tic:ips_list'
    update_url_name = 'gestion_tic:ips_update'
    delete_url_name = 'gestion_tic:ips_delete'
    search_fields = ['ip']

    def get_create_url(self):
        return reverse_lazy('gestion_tic:ips_create')


class IpsCreateView(CatalogoCreateView):
    model = Ips
    form_class = FormIps
    title = 'Crear Dirección IP'
    success_url = reverse_lazy('gestion_tic:ips_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:ips_list')


class IpsUpdateView(CatalogoUpdateView):
    model = Ips
    form_class = FormIps
    title = 'Editar Dirección IP'
    success_url = reverse_lazy('gestion_tic:ips_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:ips_list')


def ips_desactivar(request, pk):
    return catalogo_desactivar(request, pk, Ips, 'gestion_tic:ips_list')


# --- Implementación para JefeTic ---

class JefeTicListView(CatalogoListView):
    model = JefeTic
    title = 'Listado de Jefes TIC'
    list_url_name = 'gestion_tic:jefetic_list'
    update_url_name = 'gestion_tic:jefetic_update'
    delete_url_name = 'gestion_tic:jefetic_delete'
    search_fields = ['nombre']

    def get_create_url(self):
        return reverse_lazy('gestion_tic:jefetic_create')


class JefeTicCreateView(CatalogoCreateView):
    model = JefeTic
    form_class = FormJefeTic
    title = 'Crear Jefe TIC'
    success_url = reverse_lazy('gestion_tic:jefetic_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:jefetic_list')


class JefeTicUpdateView(CatalogoUpdateView):
    model = JefeTic
    form_class = FormJefeTic
    title = 'Editar Jefe TIC'
    success_url = reverse_lazy('gestion_tic:jefetic_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:jefetic_list')


def jefetic_desactivar(request, pk):
    return catalogo_desactivar(request, pk, JefeTic, 'gestion_tic:jefetic_list')


# --- Implementación para Modelo ---

class ModeloListView(CatalogoListView):
    model = Modelo
    title = 'Listado de Modelos'
    list_url_name = 'gestion_tic:modelo_list'
    update_url_name = 'gestion_tic:modelo_update'
    delete_url_name = 'gestion_tic:modelo_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:modelo_create')


class ModeloCreateView(CatalogoCreateView):
    model = Modelo
    form_class = FormModelo
    title = 'Crear Modelo'
    success_url = reverse_lazy('gestion_tic:modelo_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:modelo_list')


class ModeloUpdateView(CatalogoUpdateView):
    model = Modelo
    form_class = FormModelo
    title = 'Editar Modelo'
    success_url = reverse_lazy('gestion_tic:modelo_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:modelo_list')


def modelo_desactivar(request, pk):
    return catalogo_desactivar(request, pk, Modelo, 'gestion_tic:modelo_list')


# --- Implementación para Propietario ---

class PropietarioListView(CatalogoListView):
    model = Propietario
    title = 'Listado de Propietarios'
    list_url_name = 'gestion_tic:propietario_list'
    update_url_name = 'gestion_tic:propietario_update'
    delete_url_name = 'gestion_tic:propietario_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:propietario_create')


class PropietarioCreateView(CatalogoCreateView):
    model = Propietario
    form_class = FormPropietario
    title = 'Crear Propietario'
    success_url = reverse_lazy('gestion_tic:propietario_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:propietario_list')


class PropietarioUpdateView(CatalogoUpdateView):
    model = Propietario
    form_class = FormPropietario
    title = 'Editar Propietario'
    success_url = reverse_lazy('gestion_tic:propietario_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:propietario_list')


def propietario_desactivar(request, pk):
    return catalogo_desactivar(request, pk, Propietario, 'gestion_tic:propietario_list')


# --- Implementación para Contrato ---

class ContratoListView(CatalogoListView):
    model = Contrato
    title = 'Listado de Contratos'
    list_url_name = 'gestion_tic:contrato_list'
    update_url_name = 'gestion_tic:contrato_update'
    delete_url_name = 'gestion_tic:contrato_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:contrato_create')


class ContratoCreateView(CatalogoCreateView):
    model = Contrato
    form_class = FormContrato
    title = 'Crear Contrato'
    success_url = reverse_lazy('gestion_tic:contrato_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:contrato_list')


class ContratoUpdateView(CatalogoUpdateView):
    model = Contrato
    form_class = FormContrato
    title = 'Editar Contrato'
    success_url = reverse_lazy('gestion_tic:contrato_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:contrato_list')


def contrato_desactivar(request, pk):
    return catalogo_desactivar(request, pk, Contrato, 'gestion_tic:contrato_list')
