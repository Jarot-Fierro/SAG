from django.urls import path

from bodega.views.bodega import *
from bodega.views.movimientos import *
from bodega.views.producto import *
from bodega.views.stock import *

app_name = 'bodega'

urlpatterns = [
    # Bodega
    path('bodega/', BodegaListView.as_view(), name='bodega_list'),
    path('bodega/nuevo/', BodegaCreateView.as_view(), name='bodega_create'),
    path('bodega/<int:pk>/editar/', BodegasUpdateView.as_view(), name='bodega_update'),

    # Producto
    path('producto/', ProductoListView.as_view(), name='producto_list'),
    path('producto/nuevo/', ProductoCreateView.as_view(), name='producto_create'),
    path('producto/<int:pk>/editar/', ProductosUpdateView.as_view(), name='producto_update'),

    # Stock
    path('stock/', StockListView.as_view(), name='stock_list'),
    path('stock/nuevo/', StockCreateView.as_view(), name='stock_create'),
    path('stock/<int:pk>/editar/', StocksUpdateView.as_view(), name='stock_update'),
    path('movimientos/', MovimientoListView.as_view(), name='movimiento_list'),

    # Operaciones de Stock
    path('stock/<int:pk>/entrada/', stock_entrada, name='stock_entrada'),
    path('stock/<int:pk>/salida/', stock_salida, name='stock_salida'),
    path('stock/<int:pk>/ajuste/', stock_ajuste, name='stock_ajuste'),
    path('stock/<int:pk>/transferencia/', stock_transferencia, name='stock_transferencia'),
    path('api/stock/<int:pk>/bodegas-destino/', api_get_bodegas_destino, name='api_get_bodegas_destino'),
]
