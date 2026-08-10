from django.contrib import admin

from bodega.models.bodega import Bodega
from bodega.models.mantenedores import CategoriaProducto, Marca, UnidadMedida, Responsable
from bodega.models.movimientos import MovimientoInventario
from bodega.models.perfil import PerfilBodega
from bodega.models.producto import Producto
from bodega.models.stock import Stock
from core.standard.admin import StandardAdmin


@admin.register(Bodega)
class BodegaAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento',)
    search_fields = ('nombre',)
    list_filter = ('is_active', 'establecimiento',)
    list_display_links = ('nombre',)

    filter_horizontal = ('categorias',)

    @admin.display(description="Categorías")
    def display_categoria(self, obj):
        return ", ".join(
            obj.categorias.values_list("nombre", flat=True)
        )

    display_categoria.short_description = 'Categorias de Soporte'


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(StandardAdmin):
    list_display = ('id', 'nombre',)
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)


@admin.register(Marca)
class MarcaAdmin(StandardAdmin):
    list_display = ('id', 'nombre',)
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)


@admin.register(UnidadMedida)
class UnidadMedidaAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'abreviatura',)
    search_fields = ('nombre', 'abreviatura',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)


@admin.register(Responsable)
class ResponsableAdmin(StandardAdmin):
    list_display = ('id', 'nombre',)
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(StandardAdmin):
    list_display = ('id', 'codigo', 'nombre', 'categoria', 'marca', 'unidad_medida', 'activo',)
    search_fields = ('codigo', 'nombre',)
    list_filter = ('categoria', 'marca', 'activo', 'is_active',)
    list_display_links = ('nombre',)


@admin.register(Stock)
class StockAdmin(StandardAdmin):
    list_display = ('id', 'bodega', 'producto', 'stock_actual', 'status_stock',)
    search_fields = ('producto__nombre', 'bodega__nombre', 'ubicacion',)
    list_filter = ('bodega', 'status_stock', 'is_active',)
    list_display_links = ('producto',)


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(StandardAdmin):
    list_display = ('id', 'inventario', 'tipo', 'cantidad', 'usuario', 'fecha', 'establecimiento',)
    search_fields = ('inventario__producto__nombre', 'observacion',)
    list_filter = ('tipo', 'fecha', 'establecimiento', 'is_active',)
    list_display_links = ('inventario',)
    autocomplete_fields = ('usuario',)


@admin.register(PerfilBodega)
class PerfilBodegaAdmin(StandardAdmin):
    list_display = ('id', 'usuario',)
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name',)
    list_filter = ('is_active',)
    list_display_links = ('usuario',)

    filter_horizontal = ('bodegas',)
    autocomplete_fields = ('usuario',)

    @admin.display(description="Bodegas")
    def display_bodegas(self, obj):
        return ", ".join(
            obj.bodegas.values_list("nombre", flat=True)
        )

    display_bodegas.short_description = 'Bodegas'
