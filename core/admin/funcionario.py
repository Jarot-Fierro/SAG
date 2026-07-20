from django.contrib import admin

from core.models.funcionario import Funcionario
from core.standard.admin import StandardAdmin


@admin.register(Funcionario)
class FuncionarioAdmin(StandardAdmin):
    list_display = ('id', 'rut', 'nombres', 'apellidos', 'cargo', 'rol_organizacional',
                    'unidad_organizacional_nombre', 'establecimiento',)
    search_fields = ('rut', 'nombres', 'apellidos', 'cargo', 'profesion__nombre',
                     'unidad_organizacional__nombre')
    list_filter = ('is_active', 'establecimiento', 'cargo', 'rol_organizacional', 'unidad_organizacional')
    list_display_links = ('id', 'nombres', 'apellidos',)
    # autocomplete_fields = ('unidad_organizacional',)
    raw_id_fields = ("unidad_organizacional",)

    @admin.display(description='Unidad Organizacional', ordering='unidad_organizacional__nombre')
    def unidad_organizacional_nombre(self, obj):
        return obj.unidad_organizacional.nombre if obj.unidad_organizacional else "-"
