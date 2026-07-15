from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin

from core.models.unidad_organizacional import UnidadOrganizacional
from core.standard.admin import StandardAdmin


@admin.register(UnidadOrganizacional)
class UnidadOrganizacionalAdmin(DraggableMPTTAdmin, StandardAdmin):
    mptt_level_indent = 20
    list_display = ('tree_actions', 'indented_title', 'establecimiento', 'unidad_principal', 'is_active')
    list_display_links = ('indented_title',)
    list_filter = ('is_active', 'establecimiento', 'unidad_principal')
    search_fields = ('nombre', 'establecimiento__nombre')
    autocomplete_fields = ('padre', 'direccion')
