from django.contrib import admin

from agenda_telefonica.models import Anexo, PerfilAgenda, MenuSidebar
from core.standard.admin import StandardAdmin


@admin.register(Anexo)
class AnexoAdmin(StandardAdmin):
    list_display = (
        'id',
        'anexo',
        'funcionario',
        'establecimiento',
    )
    list_display_links = (
        'id',
        'anexo',
        'funcionario',
    )
    search_fields = (
        'anexo',
        'funcionario',
        'establecimiento',
    )
    autocomplete_fields = ('funcionario',)


@admin.register(MenuSidebar)
class MenuSidebarAdmin(StandardAdmin):
    list_display = (
        'id',
        'establecimiento',
        'orden',
        'mostrar',
    )

    search_fields = (
        'establecimiento__nombre',
    )

    list_filter = (
        'mostrar',
        'is_active',
    )
    list_display_links = (
        'id',
        'establecimiento__nombre',
    )

    ordering = (
        'orden',
        'establecimiento__nombre',
    )


@admin.register(PerfilAgenda)
class PerfilAgendaAdmin(StandardAdmin):
    list_display = ('id', 'usuario', 'editor',)
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
    list_filter = ('editor', 'is_active')
    autocomplete_fields = ('usuario',)
    filter_horizontal = ('unidad_organizacional',)
    list_display_links = ('usuario',)
