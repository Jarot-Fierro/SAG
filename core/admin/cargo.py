from django.contrib import admin

from core.models.cargo import Cargo
from core.standard.admin import StandardAdmin


@admin.register(Cargo)
class CargoAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
