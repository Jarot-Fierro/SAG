from core.forms.profesiones import ProfesionForm
from core.models.profesion import Profesion
from core.standard.views import *


class ProfesionListView(StandardListView):
    model = Profesion
    title = 'Listado de Profesiones'
    list_url_name = 'core:profesion_list'
    create_url_name = 'core:profesion_create'
    update_url_name = 'core:profesion_update'
    delete_url_name = 'core:profesion_delete'
    search_fields = ['nombre']


class ProfesionCreateView(StandardCreateView):
    model = Profesion
    form_class = ProfesionForm
    title = 'Crear Profesión'
    success_url = reverse_lazy('core:profesion_list')

    def get_list_url(self):
        return reverse_lazy('core:profesion_list')


class ProfesionUpdateView(StandardUpdateView):
    model = Profesion
    form_class = ProfesionForm
    title = 'Editar Profesión'
    success_url = reverse_lazy('core:profesion_list')

    def get_list_url(self):
        return reverse_lazy('core:profesion_list')


@require_POST
def profesion_desactivar(request, pk):
    return catalogo_desactivar(request, pk, Profesion, 'core:profesion_list')
