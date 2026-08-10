from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator

from bodega.decorators import perfil_bodega_required
from bodega.forms.forms import FormProducto
from bodega.models import Bodega
from bodega.models.producto import Producto
from core.standard.views import StandardListView, StandardCreateView, StandardUpdateView

MODULE_NAME = 'Producto'


@method_decorator(perfil_bodega_required, name="dispatch")
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
        queryset = (
            super()
            .get_queryset()
            .select_related(
                "categoria",
                "marca",
                "unidad_medida",
            )
        )

        bodega_id = self.request.GET.get("bodega")

        if bodega_id:
            bodega = get_object_or_404(Bodega, pk=bodega_id)

            queryset = queryset.filter(
                categoria__in=bodega.categorias.all()
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bodega_id = self.request.GET.get("bodega")
        if bodega_id:
            context['instance_bodega'] = Bodega.objects.filter(pk=bodega_id).first()
        return context


class ProductoCreateView(StandardCreateView):
    model = Producto
    form_class = FormProducto
    template_name = 'bodega/form_producto.html'
    title = 'Nuevo Producto'
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['bodega'] = self.request.GET.get('bodega')
        return kwargs

    def get_success_url(self):
        bodega_id = self.request.GET.get('bodega')
        return f"{reverse('bodega:producto_list')}?bodega={bodega_id}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        bodega_id = self.request.GET.get('bodega')

        if bodega_id:
            context['instance_bodega'] = Bodega.objects.filter(
                pk=bodega_id
            ).first()

        return context


class ProductosUpdateView(StandardUpdateView):
    model = Producto
    form_class = FormProducto
    template_name = 'bodega/form_producto.html'
    title = 'Editar Producto'
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['bodega'] = self.request.GET.get('bodega')
        return kwargs

    def get_success_url(self):
        bodega_id = self.request.GET.get('bodega')
        return f"{reverse('bodega:producto_list')}?bodega={bodega_id}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        bodega_id = self.request.GET.get('bodega')

        if bodega_id:
            context['instance_bodega'] = Bodega.objects.filter(
                pk=bodega_id
            ).first()

        return context
