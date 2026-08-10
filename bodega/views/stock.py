from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from bodega.forms.forms import FormStock
from bodega.models import Bodega
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
        queryset = super().get_queryset().select_related('bodega', 'producto')
        bodega_id = self.request.GET.get("bodega")
        if bodega_id:
            queryset = queryset.filter(bodega_id=bodega_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bodega_id = self.request.GET.get("bodega")
        if bodega_id:
            context['instance_bodega'] = Bodega.objects.filter(pk=bodega_id).first()
        return context


class StockCreateView(StandardCreateView):
    model = Stock
    form_class = FormStock
    template_name = 'bodega/form_stock.html'
    title = 'Nuevo Stock'
    module_name = MODULE_NAME

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['bodega'] = self.request.GET.get('bodega')
        return kwargs

    def get_success_url(self):
        bodega_id = self.request.GET.get('bodega')
        return f"{reverse('bodega:stock_list')}?bodega={bodega_id}"

    def form_valid(self, form):
        bodega_id = self.request.GET.get("bodega")
        if bodega_id:
            form.instance.bodega = get_object_or_404(Bodega, pk=bodega_id)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bodega_id = self.request.GET.get("bodega")
        if bodega_id:
            context['instance_bodega'] = Bodega.objects.filter(pk=bodega_id).first()
        return context


class StocksUpdateView(StandardUpdateView):
    model = Stock
    form_class = FormStock
    template_name = 'bodega/form_stock.html'
    title = 'Editar Stock'
    module_name = MODULE_NAME

    def get_success_url(self):
        bodega_id = self.request.GET.get('bodega')
        return f"{reverse('bodega:stock_list')}?bodega={bodega_id}"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['bodega'] = self.request.GET.get('bodega')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bodega_id = self.request.GET.get("bodega")
        if bodega_id:
            context['instance_bodega'] = Bodega.objects.filter(pk=bodega_id).first()
        return context


def add_stock(request):
    if request.method == 'POST':
        stock_id = request.POST.get('stock_id')
        cantidad = request.POST.get('cantidad')
        stock = get_object_or_404(Stock, pk=stock_id)

        print('ID Stock:', stock_id)
        print('Stock:', stock)
        print('ID Stock en busqueda:', stock.id)
        print('Cantidad:', cantidad)

    return redirect('bodega:stock_list')
