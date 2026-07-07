from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

from core.utils import IncludeUserFormCreate, IncludeUserFormUpdate
from ..forms.catalogo import (
    FormMarca, FormCategoria, FormContrato, FormIps, FormJefeTic, FormLicenciaOs,
    FormMicrosoftOffice, FormModelo, FormPropietario, FormPuestoTrabajo,
    FormSistemaOperativo, FormSubCategoria, FormTipoCelular, FormTipoComputador,
    FormTipoImpresora, FormToner
)
from ..models.catalogo import (
    Marca, Categoria, Contrato, Ips, JefeTic, LicenciaOs, MicrosoftOffice,
    Modelo, Propietario, PuestoTrabajo, SistemaOperativo, SubCategoria,
    TipoCelular, TipoComputador, TipoImpresora, Toner
)


class CatalogoBaseView(LoginRequiredMixin):
    template_name = 'gestion_tic/catalogo/form.html'
    success_url = None
    module_name = 'Catálogo'
    title = 'Mantenedor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_name'] = self.module_name
        context['title'] = self.title
        context['list_url'] = self.get_list_url()
        context['create_url'] = self.get_create_url()
        return context

    def get_list_url(self):
        return None

    def get_create_url(self):
        return None


class CatalogoListView(CatalogoBaseView, ListView):
    template_name = 'gestion_tic/catalogo/list.html'
    context_object_name = 'objetos'
    paginate_by = 10
    search_fields = ['nombre']

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        query = self.request.GET.get('q')
        if query and self.search_fields:
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


class CatalogoCreateView(CatalogoBaseView, IncludeUserFormCreate, CreateView):
    def form_valid(self, form):
        messages.success(self.request, f'{self.model._meta.verbose_name} creado correctamente.')
        return super().form_valid(form)


class CatalogoUpdateView(CatalogoBaseView, IncludeUserFormUpdate, UpdateView):
    def form_valid(self, form):
        messages.success(self.request, f'{self.model._meta.verbose_name} actualizado correctamente.')
        return super().form_valid(form)


def catalogo_desactivar(request, pk, model, redirect_url_name):
    obj = get_object_or_404(model, pk=pk)
    obj.is_active = False
    obj.save()
    messages.success(request, f'{obj} desactivado correctamente.')
    return redirect(redirect_url_name)


# --- Implementación para Marca ---

class MarcaListView(CatalogoListView):
    model = Marca
    title = 'Listado de Marcas'
    update_url_name = 'gestion_tic:marca_update'
    delete_url_name = 'gestion_tic:marca_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:marca_create')


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


# --- Implementación para Categoria ---

class CategoriaListView(CatalogoListView):
    model = Categoria
    title = 'Listado de Categorías'
    update_url_name = 'gestion_tic:categoria_update'
    delete_url_name = 'gestion_tic:categoria_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:categoria_create')


class CategoriaCreateView(CatalogoCreateView):
    model = Categoria
    form_class = FormCategoria
    title = 'Crear Categoría'
    success_url = reverse_lazy('gestion_tic:categoria_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:categoria_list')


class CategoriaUpdateView(CatalogoUpdateView):
    model = Categoria
    form_class = FormCategoria
    title = 'Editar Categoría'
    success_url = reverse_lazy('gestion_tic:categoria_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:categoria_list')


def categoria_desactivar(request, pk):
    return catalogo_desactivar(request, pk, Categoria, 'gestion_tic:categoria_list')


# --- Implementación para Ips ---

class IpsListView(CatalogoListView):
    model = Ips
    title = 'Listado de Direcciones IP'
    update_url_name = 'gestion_tic:ips_update'
    delete_url_name = 'gestion_tic:ips_delete'
    search_fields = ['ip', 'establecimiento__nombre', 'departamento__nombre', 'observacion']

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
    update_url_name = 'gestion_tic:jefetic_update'
    delete_url_name = 'gestion_tic:jefetic_delete'
    search_fields = ['nombre', 'posicion']

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


# --- Implementación para LicenciaOs ---

class LicenciaOsListView(CatalogoListView):
    model = LicenciaOs
    title = 'Listado de Licencias de SO'
    update_url_name = 'gestion_tic:licenciaos_update'
    delete_url_name = 'gestion_tic:licenciaos_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:licenciaos_create')


class LicenciaOsCreateView(CatalogoCreateView):
    model = LicenciaOs
    form_class = FormLicenciaOs
    title = 'Crear Licencia de SO'
    success_url = reverse_lazy('gestion_tic:licenciaos_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:licenciaos_list')


class LicenciaOsUpdateView(CatalogoUpdateView):
    model = LicenciaOs
    form_class = FormLicenciaOs
    title = 'Editar Licencia de SO'
    success_url = reverse_lazy('gestion_tic:licenciaos_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:licenciaos_list')


def licenciaos_desactivar(request, pk):
    return catalogo_desactivar(request, pk, LicenciaOs, 'gestion_tic:licenciaos_list')


# --- Implementación para MicrosoftOffice ---

class MicrosoftOfficeListView(CatalogoListView):
    model = MicrosoftOffice
    title = 'Listado de Licencias Office'
    update_url_name = 'gestion_tic:microsoftoffice_update'
    delete_url_name = 'gestion_tic:microsoftoffice_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:microsoftoffice_create')


class MicrosoftOfficeCreateView(CatalogoCreateView):
    model = MicrosoftOffice
    form_class = FormMicrosoftOffice
    title = 'Crear Licencia Office'
    success_url = reverse_lazy('gestion_tic:microsoftoffice_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:microsoftoffice_list')


class MicrosoftOfficeUpdateView(CatalogoUpdateView):
    model = MicrosoftOffice
    form_class = FormMicrosoftOffice
    title = 'Editar Licencia Office'
    success_url = reverse_lazy('gestion_tic:microsoftoffice_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:microsoftoffice_list')


def microsoftoffice_desactivar(request, pk):
    return catalogo_desactivar(request, pk, MicrosoftOffice, 'gestion_tic:microsoftoffice_list')


# --- Implementación para Modelo ---

class ModeloListView(CatalogoListView):
    model = Modelo
    title = 'Listado de Modelos'
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


# --- Implementación para PuestoTrabajo ---

class PuestoTrabajoListView(CatalogoListView):
    model = PuestoTrabajo
    title = 'Listado de Puestos de Trabajo'
    update_url_name = 'gestion_tic:puestotrabajo_update'
    delete_url_name = 'gestion_tic:puestotrabajo_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:puestotrabajo_create')


class PuestoTrabajoCreateView(CatalogoCreateView):
    model = PuestoTrabajo
    form_class = FormPuestoTrabajo
    title = 'Crear Puesto de Trabajo'
    success_url = reverse_lazy('gestion_tic:puestotrabajo_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:puestotrabajo_list')


class PuestoTrabajoUpdateView(CatalogoUpdateView):
    model = PuestoTrabajo
    form_class = FormPuestoTrabajo
    title = 'Editar Puesto de Trabajo'
    success_url = reverse_lazy('gestion_tic:puestotrabajo_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:puestotrabajo_list')


def puestotrabajo_desactivar(request, pk):
    return catalogo_desactivar(request, pk, PuestoTrabajo, 'gestion_tic:puestotrabajo_list')


# --- Implementación para SistemaOperativo ---

class SistemaOperativoListView(CatalogoListView):
    model = SistemaOperativo
    title = 'Listado de Sistemas Operativos'
    update_url_name = 'gestion_tic:sistemaoperativo_update'
    delete_url_name = 'gestion_tic:sistemaoperativo_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:sistemaoperativo_create')


class SistemaOperativoCreateView(CatalogoCreateView):
    model = SistemaOperativo
    form_class = FormSistemaOperativo
    title = 'Crear Sistema Operativo'
    success_url = reverse_lazy('gestion_tic:sistemaoperativo_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:sistemaoperativo_list')


class SistemaOperativoUpdateView(CatalogoUpdateView):
    model = SistemaOperativo
    form_class = FormSistemaOperativo
    title = 'Editar Sistema Operativo'
    success_url = reverse_lazy('gestion_tic:sistemaoperativo_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:sistemaoperativo_list')


def sistemaoperativo_desactivar(request, pk):
    return catalogo_desactivar(request, pk, SistemaOperativo, 'gestion_tic:sistemaoperativo_list')


# --- Implementación para SubCategoria ---

class SubCategoriaListView(CatalogoListView):
    model = SubCategoria
    title = 'Listado de Subcategorías'
    update_url_name = 'gestion_tic:subcategoria_update'
    delete_url_name = 'gestion_tic:subcategoria_delete'
    search_fields = ['nombre', 'categoria__nombre']

    def get_create_url(self):
        return reverse_lazy('gestion_tic:subcategoria_create')


class SubCategoriaCreateView(CatalogoCreateView):
    model = SubCategoria
    form_class = FormSubCategoria
    title = 'Crear Subcategoría'
    success_url = reverse_lazy('gestion_tic:subcategoria_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:subcategoria_list')


class SubCategoriaUpdateView(CatalogoUpdateView):
    model = SubCategoria
    form_class = FormSubCategoria
    title = 'Editar Subcategoría'
    success_url = reverse_lazy('gestion_tic:subcategoria_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:subcategoria_list')


def subcategoria_desactivar(request, pk):
    return catalogo_desactivar(request, pk, SubCategoria, 'gestion_tic:subcategoria_list')


# --- Implementación para TipoCelular ---

class TipoCelularListView(CatalogoListView):
    model = TipoCelular
    title = 'Listado de Tipos de Celular'
    update_url_name = 'gestion_tic:tipocelular_update'
    delete_url_name = 'gestion_tic:tipocelular_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:tipocelular_create')


class TipoCelularCreateView(CatalogoCreateView):
    model = TipoCelular
    form_class = FormTipoCelular
    title = 'Crear Tipo de Celular'
    success_url = reverse_lazy('gestion_tic:tipocelular_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:tipocelular_list')


class TipoCelularUpdateView(CatalogoUpdateView):
    model = TipoCelular
    form_class = FormTipoCelular
    title = 'Editar Tipo de Celular'
    success_url = reverse_lazy('gestion_tic:tipocelular_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:tipocelular_list')


def tipocelular_desactivar(request, pk):
    return catalogo_desactivar(request, pk, TipoCelular, 'gestion_tic:tipocelular_list')


# --- Implementación para TipoComputador ---

class TipoComputadorListView(CatalogoListView):
    model = TipoComputador
    title = 'Listado de Tipos de Computador'
    update_url_name = 'gestion_tic:tipocomputador_update'
    delete_url_name = 'gestion_tic:tipocomputador_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:tipocomputador_create')


class TipoComputadorCreateView(CatalogoCreateView):
    model = TipoComputador
    form_class = FormTipoComputador
    title = 'Crear Tipo de Computador'
    success_url = reverse_lazy('gestion_tic:tipocomputador_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:tipocomputador_list')


class TipoComputadorUpdateView(CatalogoUpdateView):
    model = TipoComputador
    form_class = FormTipoComputador
    title = 'Editar Tipo de Computador'
    success_url = reverse_lazy('gestion_tic:tipocomputador_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:tipocomputador_list')


def tipocomputador_desactivar(request, pk):
    return catalogo_desactivar(request, pk, TipoComputador, 'gestion_tic:tipocomputador_list')


# --- Implementación para TipoImpresora ---

class TipoImpresoraListView(CatalogoListView):
    model = TipoImpresora
    title = 'Listado de Tipos de Impresora'
    update_url_name = 'gestion_tic:tipoimpresora_update'
    delete_url_name = 'gestion_tic:tipoimpresora_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:tipoimpresora_create')


class TipoImpresoraCreateView(CatalogoCreateView):
    model = TipoImpresora
    form_class = FormTipoImpresora
    title = 'Crear Tipo de Impresora'
    success_url = reverse_lazy('gestion_tic:tipoimpresora_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:tipoimpresora_list')


class TipoImpresoraUpdateView(CatalogoUpdateView):
    model = TipoImpresora
    form_class = FormTipoImpresora
    title = 'Editar Tipo de Impresora'
    success_url = reverse_lazy('gestion_tic:tipoimpresora_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:tipoimpresora_list')


def tipoimpresora_desactivar(request, pk):
    return catalogo_desactivar(request, pk, TipoImpresora, 'gestion_tic:tipoimpresora_list')


# --- Implementación para Toner ---

class TonerListView(CatalogoListView):
    model = Toner
    title = 'Listado de Tintas/Toner'
    update_url_name = 'gestion_tic:toner_update'
    delete_url_name = 'gestion_tic:toner_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:toner_create')


class TonerCreateView(CatalogoCreateView):
    model = Toner
    form_class = FormToner
    title = 'Crear Tinta/Toner'
    success_url = reverse_lazy('gestion_tic:toner_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:toner_list')


class TonerUpdateView(CatalogoUpdateView):
    model = Toner
    form_class = FormToner
    title = 'Editar Tinta/Toner'
    success_url = reverse_lazy('gestion_tic:toner_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:toner_list')


def toner_desactivar(request, pk):
    return catalogo_desactivar(request, pk, Toner, 'gestion_tic:toner_list')


# --- Implementación para Contrato ---

class ContratoListView(CatalogoListView):
    model = Contrato
    title = 'Listado de Contratos'
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
