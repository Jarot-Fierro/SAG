from django.contrib import admin

from core.standard.admin import StandardAdmin
from ..models.celulares import Celular


@admin.register(Celular)
class CelularAdmin(StandardAdmin):
    list_display = (
        'id', 'imei', 'numero_telefono', 'marca', 'modelo', 'propietario',
        'minsal', 'establecimiento_mantenedor', 'responsable', 'jefe_entrega',
        'numero_chip', 'minutos', 'establecimiento',
    )
    search_fields = (
        'imei', 'numero_telefono', 'marca__nombre', 'modelo__nombre',
        'propietario__nombre', 'establecimiento_mantenedor__nombre',
        'responsable__nombre', 'jefe_entrega__nombre', 'numero_chip', 'observacion',
    )
    list_filter = (
        'marca', 'modelo', 'propietario', 'minsal',
        'establecimiento_mantenedor', 'jefe_entrega', 'establecimiento', 'is_active',
    )
    list_display_links = ('imei',)
    ordering = ('-id',)
    autocomplete_fields = (
        'marca', 'modelo', 'propietario', 'establecimiento_mantenedor', 'jefe_entrega',
    )
    list_select_related = (
        'marca', 'modelo', 'propietario', 'establecimiento_mantenedor',
        'jefe_entrega', 'establecimiento',
    )
