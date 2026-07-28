from core.forms.modulos import ModuloForm
from core.models.modulos import Modulo
from core.standard.views import *


class ModuloListView(StandardListView):
    model = Modulo
    title = 'Listado de Módulos'
    list_url_name = 'core:modulo_list'
    create_url_name = 'core:modulo_create'
    update_url_name = 'core:modulo_update'
    delete_url_name = 'core:modulo_delete'
    search_fields = ['nombre', 'codigo']


class ModuloCreateView(StandardCreateView):
    model = Modulo
    form_class = ModuloForm
    title = 'Crear Módulo'
    success_url = reverse_lazy('core:modulo_list')

    def get_list_url(self):
        return reverse_lazy('core:modulo_list')


class ModuloUpdateView(StandardUpdateView):
    model = Modulo
    form_class = ModuloForm
    title = 'Editar Módulo'
    success_url = reverse_lazy('core:modulo_list')

    def get_list_url(self):
        return reverse_lazy('core:modulo_list')


@require_POST
def modulo_desactivar(request, pk):
    return catalogo_desactivar(request, pk, Modulo, 'core:modulo_list')
