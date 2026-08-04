from django.urls import path

from bodega.views.bodega import BodegaListView, BodegaCreateView, BodegasUpdateView
from bodega.views.producto import ProductoListView, ProductoCreateView, ProductosUpdateView
from bodega.views.stock import StockListView, StockCreateView, StocksUpdateView

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
]
