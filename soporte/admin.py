from django.contrib import admin

from core.standard.admin import StandardAdmin
from soporte.models import TipoSoporte, Ticket, PerfilSoporte


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

@admin.register(PerfilSoporte)
class PerfilSoporteAdmin(StandardAdmin):
    list_display = (
        'id',
        'usuario',
        'usuario_soporte',
        'is_active',
    )
    list_filter = (
        'usuario_soporte',
        'is_active',
        'usuario__groups',
    )

    search_fields = (
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
    )

    list_display_links = (
        'nombre',
    )
    autocomplete_fields = ('usuario',)

    ordering = (
        '-id',
    )

    fieldsets = (
        (None, {'fields': ('usuario', 'usuario_soporte', 'is_active')}),
    )

    def get_usuarios(self, obj):
        return ", ".join([f"{u.first_name} {u.last_name} ({u.username})" for u in obj.usuario.all()])

    get_usuarios.short_description = 'Usuarios'
