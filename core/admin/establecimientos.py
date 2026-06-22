from django.contrib import admin

from core.models.establecimientos import Establecimiento
from core.standard.admin import StandardAdmin


@admin.register(Establecimiento)
class EstablecimientoAdmin(StandardAdmin):
    list_display = ('nombre', 'region', 'telefono')
    search_fields = ('nombre', 'region')
    list_filter = ('is_active', 'region')
