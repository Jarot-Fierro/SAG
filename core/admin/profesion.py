from django.contrib import admin

from core.models.profesion import Profesion
from core.standard.admin import StandardAdmin


@admin.register(Profesion)
class ProfesionAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
