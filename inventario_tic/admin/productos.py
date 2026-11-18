from django.contrib import admin

from core.standard.admin import StandardAdmin
from ..models.productos import Producto


@admin.register(Producto)
class ProductoAdmin(StandardAdmin):
    list_display = (
        'id', 'nombre', 'tipo_producto', 'marca', 'modelo',
        'stock_total', 'stock_disponible', 'stock_minimo', 'establecimiento',
    )
    search_fields = (
        'nombre', 'tipo_producto__nombre', 'marca__nombre', 'modelo__nombre', 'descripcion',
    )
    list_filter = ('tipo_producto', 'marca', 'modelo', 'establecimiento', 'is_active')
    list_display_links = ('nombre',)
    ordering = ('nombre',)
    autocomplete_fields = ('tipo_producto', 'marca', 'modelo')
    list_select_related = ('tipo_producto', 'marca', 'modelo', 'establecimiento')
