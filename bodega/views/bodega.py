from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from bodega.decorators import perfil_bodega_required
from bodega.forms.forms import FormBodega
from bodega.models.bodega import Bodega
from core.standard.views import StandardListView, StandardCreateView, StandardUpdateView

MODULE_NAME = 'Bodega'


@method_decorator(perfil_bodega_required, name="dispatch")
class BodegaListView(StandardListView):
    model = Bodega
    template_name = "bodega/list_bodega.html"
    title = "Bodegas"
    search_fields = ['nombre', 'descripcion']
    list_url_name = "bodega:bodega_list"
    create_url_name = "bodega:bodega_create"
    update_url_name = "bodega:bodega_update"
    delete_url_name = "bodega:bodega_delete"

    def get_queryset(self):
        return self.request.perfil_bodega.bodegas.all()


class BodegaCreateView(StandardCreateView):
    model = Bodega
    form_class = FormBodega
    template_name = 'bodega/form_bodega.html'
    success_url = reverse_lazy('bodega:bodega_list')
    title = 'Nueva Bodega'
    module_name = MODULE_NAME


class BodegasUpdateView(StandardUpdateView):
    model = Bodega
    form_class = FormBodega
    template_name = 'bodega/form_bodega.html'
    success_url = reverse_lazy('bodega:bodega_list')
    title = 'Editar Bodega'
    module_name = MODULE_NAME
