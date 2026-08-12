from bodega.models import Bodega
from bodega.models.movimientos import MovimientoInventario
from core.standard.views import StandardListView

MODULE_NAME = 'Movimientos'


class MovimientoListView(StandardListView):
    model = MovimientoInventario
    template_name = "bodega/list_movimientos.html"
    title = "Movimientos de Stock"
    search_fields = ['inventario__producto__nombre', 'tipo', 'usuario__username', 'observacion']
    list_url_name = "bodega:movimiento_list"
    update_url_name = None
    delete_url_name = None

    def get_queryset(self):
        queryset = super().get_queryset().select_related('inventario__producto', 'inventario__bodega', 'usuario')
        bodega_id = self.request.GET.get("bodega")
        if bodega_id:
            queryset = queryset.filter(inventario__bodega_id=bodega_id)
        return queryset.order_by('-fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bodega_id = self.request.GET.get("bodega")
        if bodega_id:
            context['instance_bodega'] = Bodega.objects.filter(pk=bodega_id).first()
        return context
