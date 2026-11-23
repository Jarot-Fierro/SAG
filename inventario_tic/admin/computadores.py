from django.contrib import admin

from core.standard.admin import StandardAdmin
from ..models.computadores import Computador


@admin.register(Computador)
class ComputadorAdmin(StandardAdmin):
    list_display = (
        'id', 'codigo_inventario', 'numero_serie', 'marca', 'modelo', 'formato',
        'procesador', 'memoria_ram_gb', 'almacenamiento', 'tarjeta_grafica',
        'establecimiento_mantenedor', 'responsable', 'jefe_entrega',
        'asignado', 'establecimiento',
    )
    search_fields = (
        'codigo_inventario', 'numero_serie', 'marca__nombre', 'modelo__nombre',
        'procesador', 'almacenamiento', 'tarjeta_grafica',
        'establecimiento_mantenedor__nombre', 'responsable__nombre',
        'jefe_entrega__nombre', 'observacion',
    )
    list_filter = (
        'marca', 'modelo', 'formato', 'asignado', 'establecimiento_mantenedor',
        'jefe_entrega', 'establecimiento', 'is_active',
    )
    list_display_links = ('codigo_inventario',)
    ordering = ('-id',)
    readonly_fields = StandardAdmin.readonly_fields + ('codigo_inventario',)
    autocomplete_fields = (
        'marca', 'modelo', 'establecimiento_mantenedor', 'responsable', 'jefe_entrega',
    )
    list_select_related = (
        'marca', 'modelo', 'establecimiento_mantenedor', 'responsable',
        'jefe_entrega', 'establecimiento',
    )
