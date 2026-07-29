from django.contrib import admin

from core.standard.admin import StandardAdmin
from soporte.models import TipoSoporte, Ticket


@admin.register(TipoSoporte)
class TipoSoporteAdmin(StandardAdmin):
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


@admin.register(Ticket)
class TicketAdmin(StandardAdmin):
    list_display = (
        'id',
        'numero_ticket',
        'titulo',
        'estado',
        'area_soporte',
        'tipo_soporte',
        'establecimiento',
        'asignado_a',
        'fecha_cierre',
    )

    search_fields = (
        'numero_ticket',
        'titulo',
        'descripcion',
        'solucion',
        'establecimiento__nombre',
    )

    list_filter = (
        'estado',
        'area_soporte',
        'tipo_soporte',
        'establecimiento',
        'is_active',
    )

    list_display_links = (
        'numero_ticket',
    )

    ordering = (
        '-id',
    )

    autocomplete_fields = (
        'establecimiento',
        'asignado_a',
        'tipo_soporte',
        'funcionario',
    )
