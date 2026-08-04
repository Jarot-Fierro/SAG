from django.urls import reverse_lazy

from bodega.forms.forms import FormStock
from bodega.models.stock import Stock
from core.standard.views import StandardListView, StandardCreateView, StandardUpdateView

MODULE_NAME = 'Stock'


class StockListView(StandardListView):
    model = Stock
    template_name = "bodega/list_stock.html"
    title = "Stock"
    search_fields = ['producto__nombre', 'bodega__nombre']
    list_url_name = "bodega:stock_list"
    create_url_name = "bodega:stock_create"
    update_url_name = "bodega:stock_update"
    delete_url_name = "bodega:stock_delete"

    def get_queryset(self):
        return super().get_queryset().select_related('bodega', 'producto')


class StockCreateView(StandardCreateView):
    model = Stock
    form_class = FormStock
    template_name = 'bodega/form_stock.html'
    success_url = reverse_lazy('bodega:stock_list')
    title = 'Nuevo Stock'
    module_name = MODULE_NAME


class StocksUpdateView(StandardUpdateView):
    model = Stock
    form_class = FormStock
    template_name = 'bodega/form_stock.html'
    success_url = reverse_lazy('bodega:stock_list')
    title = 'Editar Stock'
    module_name = MODULE_NAME
