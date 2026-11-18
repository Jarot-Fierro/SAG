from django.contrib import admin

from core.standard.admin import StandardAdmin
from ..models.mantenedores import (
    Contrato, Establecimiento, Ips, JefeTic, Marca, Modelo, Propietario,
    TipoProducto, FuncionarioInventario,
)


@admin.register(TipoProducto)
class TipoProductoAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento')
    search_fields = ('nombre',)
    list_filter = ('establecimiento', 'is_active')
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Marca)
class MarcaAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento')
    search_fields = ('nombre',)
    list_filter = ('establecimiento', 'is_active')
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Modelo)
class ModeloAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'marca', 'establecimiento')
    search_fields = ('nombre', 'marca__nombre')
    list_filter = ('marca', 'establecimiento', 'is_active')
    list_display_links = ('nombre',)
    ordering = ('nombre',)
    autocomplete_fields = ('marca',)
    list_select_related = ('marca', 'establecimiento')


@admin.register(Establecimiento)
class EstablecimientoAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento')
    search_fields = ('nombre',)
    list_filter = ('establecimiento', 'is_active')
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Propietario)
class PropietarioAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento')
    search_fields = ('nombre',)
    list_filter = ('establecimiento', 'is_active')
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(JefeTic)
class JefeTicAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'posicion', 'establecimiento')
    search_fields = ('nombre', 'posicion')
    list_filter = ('posicion', 'establecimiento', 'is_active')
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Contrato)
class ContratoAdmin(StandardAdmin):
    list_display = (
        'id', 'nombre', 'fecha_inicio', 'fecha_vencimiento',
        'dias_aviso', 'notificar_vencimiento', 'establecimiento',
    )
    search_fields = ('nombre',)
    list_filter = ('notificar_vencimiento', 'fecha_vencimiento', 'establecimiento', 'is_active')
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Ips)
class IpsAdmin(StandardAdmin):
    list_display = ('id', 'ip', 'mascara', 'gateway', 'vlan', 'asignado', 'establecimiento')
    search_fields = ('ip', 'mascara', 'gateway', 'vlan', 'observacion')
    list_filter = ('asignado', 'vlan', 'establecimiento', 'is_active')
    list_display_links = ('ip',)
    ordering = ('ip',)


@admin.register(FuncionarioInventario)
class FuncionarioInventarioAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('establecimiento', 'is_active')
    ordering = ('nombre',)
