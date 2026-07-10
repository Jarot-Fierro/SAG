from django.contrib import admin

from core.models.rol_organizacional import RolOrganizacional
from core.standard.admin import StandardAdmin


@admin.register(RolOrganizacional)
class RolOrganizacionalAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
