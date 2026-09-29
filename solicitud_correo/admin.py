from django.contrib import admin

from core.standard.admin import StandardAdmin
from solicitud_correo.models import SolicitudCorreo, SolicitudCorreoDetalle


class SolicitudCorreoDetalleInline(admin.TabularInline):
    model = SolicitudCorreoDetalle
    extra = 0
    fields = (
        'rut', 'nombres', 'apellidos', 'departamento', 'cargo',
        'estado', 'motivo_rechazo', 'correo_creado', 'notificado'
    )


@admin.register(SolicitudCorreo)
class SolicitudCorreoAdmin(StandardAdmin):
    list_display = (
        'id',
        'numero_solicitud',
        'establecimiento',
        'departamento_solicitante',
        'usuario_solicitante',
        'estado',
        'fecha_solicitud',
    )
    search_fields = (
        'numero_solicitud',
        'usuario_solicitante__username',
        'usuario_solicitante__first_name',
        'usuario_solicitante__last_name',
        'departamento_nombre',
        'detalles__rut',
        'detalles__nombres',
        'detalles__apellidos',
    )
    list_filter = (
        'estado',
        'establecimiento',
        'fecha_solicitud',
        'is_active',
    )
    list_display_links = ('numero_solicitud',)
    inlines = [SolicitudCorreoDetalleInline]


@admin.register(SolicitudCorreoDetalle)
class SolicitudCorreoDetalleAdmin(StandardAdmin):
    list_display = (
        'id',
        'solicitud',
        'rut',
        'nombres',
        'apellidos',
        'estado',
        'correo_creado',
        'notificado',
    )
    search_fields = (
        'rut',
        'nombres',
        'apellidos',
        'solicitud__numero_solicitud',
        'correo_creado',
        'referencia_externa',
    )
    list_filter = (
        'estado',
        'notificado',
        'fecha_creacion',
        'is_active',
    )
