from django.contrib import admin

from core.models.departamentos import Departamento
from core.standard.admin import StandardAdmin


@admin.register(Departamento)
class DepartamentoAdmin(StandardAdmin):
    list_display = ('nombre', 'establecimiento',)
    search_fields = ('nombre', 'establecimiento')
    list_filter = ('is_active', 'establecimiento')
