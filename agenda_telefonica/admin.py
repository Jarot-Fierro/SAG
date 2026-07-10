from django.contrib import admin

from agenda_telefonica.models import Anexo, PerfilAgenda
from agenda_telefonica.models import MenuSidebar
from core.standard.admin import StandardAdmin


@admin.register(Anexo)
class AnexoAdmin(StandardAdmin):
    list_display = (
        'id',
        'anexo',
        'nombre',
        'anexo_publico',
        'servicio',
        'email',
    )

    search_fields = (
        'anexo',
        'nombre',
        'email',
        'servicio__nombre',
    )

    list_filter = (
        'is_active',
        'servicio',
    )
    list_display_links = (
        'nombre',
    )

    ordering = ('anexo',)


@admin.register(MenuSidebar)
class MenuSidebarAdmin(StandardAdmin):
    list_display = (
        'id',
        'establecimiento',
        'orden',
        'mostrar',
        'is_active',
    )

    search_fields = (
        'establecimiento__nombre',
    )

    list_filter = (
        'mostrar',
        'is_active',
    )
    list_display_links = (
        'establecimiento__nombre',
    )

    ordering = (
        'orden',
        'establecimiento__nombre',
    )



@admin.register(PerfilAgenda)
class PerfilAgendaAdmin(StandardAdmin):
    list_display = ('usuario', 'editor', 'is_active')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
    list_filter = ('editor', 'is_active')
    filter_horizontal = ('servicio',)
    autocomplete_fields = ('usuario',)


