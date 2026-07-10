from django.contrib import admin

from core.models.unidad_organizacional import UnidadOrganizacional
from core.standard.admin import StandardAdmin


@admin.register(UnidadOrganizacional)
class UnidadOrganizacionalAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'padre', 'establecimiento','is_active')
    list_filter = ('is_active', 'establecimiento')
    search_fields = ('nombre', 'establecimiento__nombre',)
    list_display_links = ('id', 'nombre')
