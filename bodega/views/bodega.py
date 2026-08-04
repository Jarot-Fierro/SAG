from django.urls import reverse_lazy

from bodega.forms.forms import FormBodega
from bodega.models.bodega import Bodega
from core.standard.views import StandardListView, StandardCreateView, StandardUpdateView

MODULE_NAME = 'Bodega'


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
        return super().get_queryset()


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
