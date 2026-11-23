from django.contrib import admin

from core.standard.admin import StandardAdmin
from ..models.monitores import Monitor


@admin.register(Monitor)
class MonitorAdmin(StandardAdmin):
    list_display = (
        'id', 'codigo_inventario', 'numero_serie', 'marca', 'modelo',
        'pulgadas', 'resolucion', 'frecuencia_hz',
        'establecimiento_mantenedor', 'responsable', 'jefe_entrega',
        'asignado', 'establecimiento',
    )
    search_fields = (
        'codigo_inventario', 'numero_serie', 'marca__nombre', 'modelo__nombre',
        'resolucion', 'establecimiento_mantenedor__nombre', 'responsable__nombre',
        'jefe_entrega__nombre', 'observacion',
    )
    list_filter = (
        'marca', 'modelo', 'tiene_hdmi', 'tiene_displayport', 'tiene_vga',
        'tiene_dvi', 'tiene_usb_c', 'asignado', 'establecimiento_mantenedor',
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
