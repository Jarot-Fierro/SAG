from django.contrib import admin

from agenda_telefonica.models import Anexo, Direccion, Ubicacion, Servicio, PerfilAgenda, NivelOrganizacional, Cargo
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


@admin.register(Direccion)
class DireccionAdmin(StandardAdmin):
    list_display = (
        'id',
        'nombre',
        'is_active',
    )

    search_fields = (
        'nombre',
    )

    list_filter = (
        'is_active',
    )
    list_display_links = (
        'nombre',
    )

    ordering = (
        'nombre',
    )


@admin.register(Ubicacion)
class UbicacionAdmin(StandardAdmin):
    list_display = (
        'id',
        'nombre',
        'is_active',
    )

    search_fields = (
        'nombre',
    )

    list_filter = (
        'is_active',
    )
    list_display_links = (
        'nombre',
    )

    ordering = (
        'nombre',
    )


@admin.register(Servicio)
class ServicioAdmin(StandardAdmin):
    list_display = (
        'id',
        'nombre',
        'ubicacion',
        'direccion',
        'establecimiento',
        'is_active',
    )

    search_fields = (
        'nombre',
    )

    list_filter = (
        'is_active',
        'establecimiento',
    )
    list_display_links = (
        'nombre',
    )

    ordering = (
        'nombre',
    )


@admin.register(PerfilAgenda)
class PerfilAgendaAdmin(StandardAdmin):
    list_display = ('usuario', 'editor', 'is_active')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
    list_filter = ('editor', 'is_active')
    filter_horizontal = ('servicio',)
    autocomplete_fields = ('usuario',)


@admin.register(NivelOrganizacional)
class NivelOrganizacionalAdmin(StandardAdmin):
    list_display = (
        'id',
        'tipo',
        'nombre',
        'padre',
        'orden',
        'is_active',
    )
    search_fields = (
        'nombre',
        'descripcion',
    )
    list_filter = (
        'tipo',
        'is_active',
    )
    ordering = ('tipo', 'orden', 'nombre')


@admin.register(Cargo)
class CargoAdmin(StandardAdmin):
    list_display = (
        'id',
        'nombre',
        'codigo',
        'nivel',
        'is_active',
    )
    search_fields = (
        'nombre',
        'codigo',
        'nivel__nombre',
    )
    list_filter = (
        'nivel',
        'is_active',
    )
    ordering = ('nombre',)
