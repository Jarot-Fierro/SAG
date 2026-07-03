from django.contrib import admin

from core.standard.admin import StandardAdmin
from .models import PerfilHoros, Acceso


@admin.register(PerfilHoros)
class PerfilHorosAdmin(StandardAdmin):
    list_display = (
        'id',
        'usuario',
        'is_active',
    )

    search_fields = (
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
        'usuario__email',
    )

    list_filter = (
        'is_active',
    )

    list_display_links = (
        'usuario',
    )

    ordering = (
        '-id',
    )

    autocomplete_fields = (
        'usuario',
    )

    filter_horizontal = (
        'acceso',
    )

    fieldsets = (
        (None, {
            'fields': (
                'usuario',
                'acceso',
                'is_active',
            )
        }),
    )


@admin.register(Acceso)
class AccesoAdmin(StandardAdmin):
    list_display = (
        'id',
        'nombre',
        'url',
        'icono',
        'is_active',
    )

    search_fields = (
        'nombre',
        'url',
        'icono',
    )

    list_filter = (
        'is_active',
    )

    list_display_links = (
        'nombre',
    )

    ordering = (
        '-id',
    )

    fieldsets = (
        (None, {
            'fields': (
                'nombre',
                'url',
                'icono',
                'is_active',
            )
        }),
    )
