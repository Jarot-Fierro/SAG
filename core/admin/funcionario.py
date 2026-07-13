from django.contrib import admin

from core.models.funcionario import Funcionario
from core.standard.admin import StandardAdmin


@admin.register(Funcionario)
class FuncionarioAdmin(StandardAdmin):
    list_display = ('id', 'establecimiento', 'cargo', 'profesion', 'rol_organizacional', 'unidad_organizacional',
                    'is_active')
    search_fields = ('nombres', 'apellidos', 'user__username', 'cargo__nombre', 'profesion__nombre',
                     'unidad_organizacional__nombre')
    list_filter = ('is_active', 'establecimiento', 'cargo', 'rol_organizacional', 'unidad_organizacional')
    list_display_links = ('id', 'user',)
