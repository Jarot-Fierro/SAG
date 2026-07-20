from django.contrib import admin

from core.models.direccion import Direccion
from core.standard.admin import StandardAdmin


@admin.register(Direccion)
class DireccionAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'enlace_google_maps')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
