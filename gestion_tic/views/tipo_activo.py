from django.urls import reverse_lazy, reverse

from .catalogo import CatalogoListView, CatalogoCreateView, CatalogoUpdateView, catalogo_desactivar
from ..forms.tipo_activo import FormTipoActivo
from ..models.tipo_activo import TipoActivo


class TipoActivoListView(CatalogoListView):
    model = TipoActivo
    template_name = "gestion_tic/activos/list_tipo_activo.html"
    title = 'Listado de Tipos de Activos'
    list_url_name = 'gestion_tic:tipo_activo_list'
    update_url_name = 'gestion_tic:tipo_activo_update'
    delete_url_name = 'gestion_tic:tipo_activo_delete'

    def get_create_url(self):
        return reverse_lazy('gestion_tic:tipo_activo_create')


class TipoActivoCreateView(CatalogoCreateView):
    model = TipoActivo
    form_class = FormTipoActivo
    template_name = "gestion_tic/activos/form_tipo_activo.html"
    title = 'Crear Tipo de Activo'

    # success_url = reverse_lazy('gestion_tic:tipo_activo_list')

    def get_success_url(self):
        return (
                reverse('gestion_tic:campos_tipo_activos')
                + f'?tipo={self.object.id}'
        )

    def get_list_url(self):
        return reverse_lazy('gestion_tic:tipo_activo_list')


class TipoActivoUpdateView(CatalogoUpdateView):
    model = TipoActivo
    form_class = FormTipoActivo
    template_name = "gestion_tic/activos/form_tipo_activo.html"
    title = 'Editar Tipo de Activo'
    success_url = reverse_lazy('gestion_tic:tipo_activo_list')

    def get_list_url(self):
        return reverse_lazy('gestion_tic:tipo_activo_list')


def tipo_activo_desactivar(request, pk):
    return catalogo_desactivar(request, pk, TipoActivo, 'gestion_tic:tipo_activo_list')
