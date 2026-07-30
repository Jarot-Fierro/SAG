from core.forms.establecimientos import EstablecimientoForm
from core.models.establecimientos import Establecimiento
from core.standard.views import *


class EstablecimientoListView(StandardListView):
    model = Establecimiento
    title = 'Listado de Establecimientos'
    list_url_name = 'core:establecimiento_list'
    create_url_name = 'core:establecimiento_create'
    update_url_name = 'core:establecimiento_update'
    delete_url_name = 'core:establecimiento_delete'
    search_fields = ['nombre', 'alias']

    def get_queryset(self):
        return super().get_queryset().filter(nombre=self.request.user.establecimiento.nombre)


class EstablecimientoCreateView(StandardCreateView):
    model = Establecimiento
    form_class = EstablecimientoForm
    title = 'Crear Establecimiento'
    success_url = reverse_lazy('core:establecimiento_list')

    def get_list_url(self):
        return reverse_lazy('core:establecimiento_list')


class EstablecimientoUpdateView(StandardUpdateView):
    model = Establecimiento
    form_class = EstablecimientoForm
    title = 'Editar Establecimiento'
    success_url = reverse_lazy('core:establecimiento_list')

    def get_list_url(self):
        return reverse_lazy('core:establecimiento_list')


@require_POST
def establecimiento_desactivar(request, pk):
    return catalogo_desactivar(request, pk, Establecimiento, 'core:establecimiento_list')
