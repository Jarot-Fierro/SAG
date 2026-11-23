from django.contrib import admin

from core.standard.admin import StandardAdmin
from ..models.impresoras import Impresora


@admin.register(Impresora)
class ImpresoraAdmin(StandardAdmin):
    list_display = (
        'id', 'numero_serie', 'hh', 'marca', 'modelo', 'imprime_color',
        'tiene_ethernet', 'tiene_wifi', 'toner', 'departamento', 'establecimiento',
    )
    search_fields = (
        'numero_serie', 'hh', 'marca__nombre', 'modelo__nombre',
        'toner', 'departamento__nombre', 'observacion',
    )
    list_filter = (
        'marca', 'modelo', 'imprime_color', 'tiene_ethernet', 'tiene_wifi',
        'departamento', 'establecimiento', 'is_active',
    )
    list_display_links = ('numero_serie',)
    ordering = ('-id',)
    autocomplete_fields = ('marca', 'modelo', 'departamento')
    list_select_related = ('marca', 'modelo', 'departamento', 'establecimiento')
