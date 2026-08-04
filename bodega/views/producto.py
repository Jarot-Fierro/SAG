from django.urls import reverse_lazy

from bodega.forms.forms import FormProducto
from bodega.models.producto import Producto
from core.standard.views import StandardListView, StandardCreateView, StandardUpdateView

MODULE_NAME = 'Producto'


class ProductoListView(StandardListView):
    model = Producto
    template_name = "bodega/list_producto.html"
    title = "Productos"
    search_fields = ['nombre', 'codigo', 'categoria__nombre']
    list_url_name = "bodega:producto_list"
    create_url_name = "bodega:producto_create"
    update_url_name = "bodega:producto_update"
    delete_url_name = "bodega:producto_delete"

    def get_queryset(self):
        return super().get_queryset().select_related('categoria', 'marca', 'unidad_medida')


class ProductoCreateView(StandardCreateView):
    model = Producto
    form_class = FormProducto
    template_name = 'bodega/form_producto.html'
    success_url = reverse_lazy('bodega:producto_list')
    title = 'Nuevo Producto'
    module_name = MODULE_NAME


class ProductosUpdateView(StandardUpdateView):
    model = Producto
    form_class = FormProducto
    template_name = 'bodega/form_producto.html'
    success_url = reverse_lazy('bodega:producto_list')
    title = 'Editar Producto'
    module_name = MODULE_NAME
