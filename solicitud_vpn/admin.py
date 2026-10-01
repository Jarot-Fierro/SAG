from django.contrib import admin

from core.standard.admin import StandardAdmin
from solicitud_vpn.models import SolicitudVPN, BeneficiarioVPN, AccesoVPN, PerfilVPN


class BeneficiarioVPNInline(admin.TabularInline):
    model = BeneficiarioVPN
    extra = 0
    fields = ('rut', 'nombres', 'apellidos', 'nombre_completo', 'establecimiento', 'cargo', 'telefono', 'email')


@admin.register(PerfilVPN)
class PerfilVPNAdmin(StandardAdmin):
    list_display = (
        'id',
        'usuario',
        'bandeja_vpn',
        'nombre_completo',
        'rut',
        'establecimiento',
        'cargo',
        'email',
        'is_active',
    )
    search_fields = (
        'usuario__username',
        'nombre_completo',
        'rut',
        'establecimiento',
        'cargo',
        'email',
    )
    list_filter = (
        'bandeja_vpn',
        'is_active',
    )
    autocomplete_fields = ('usuario',)


@admin.register(SolicitudVPN)
class SolicitudVPNAdmin(StandardAdmin):
    list_display = (
        'id',
        'numero_solicitud',
        'establecimiento',
        'departamento_solicitante',
        'usuario_solicitante',
        'accion',
        'estado',
        'tecnico_nombre',
        'fecha_solicitud',
        'is_active',
    )
    search_fields = (
        'numero_solicitud',
        'tecnico_nombre',
        'tecnico_rut',
        'tecnico_email',
        'grupo_vpn',
        'ticket_econecta',
        'usuario_solicitante__username',
        'beneficiarios__rut',
        'beneficiarios__nombres',
        'beneficiarios__apellidos',
    )
    list_filter = (
        'estado',
        'accion',
        'establecimiento',
        'es_proveedor',
        'fecha_solicitud',
        'is_active',
    )
    list_display_links = ('numero_solicitud',)
    filter_horizontal = ('accesos',)
    inlines = [BeneficiarioVPNInline]


@admin.register(BeneficiarioVPN)
class BeneficiarioVPNAdmin(StandardAdmin):
    list_display = (
        'id',
        'solicitud',
        'rut',
        'nombre_completo',
        'establecimiento',
        'cargo',
        'email',
        'is_active',
    )
    search_fields = (
        'rut',
        'nombres',
        'apellidos',
        'nombre_completo',
        'solicitud__numero_solicitud',
        'email',
    )
    list_filter = (
        'establecimiento',
        'is_active',
    )


@admin.register(AccesoVPN)
class AccesoVPNAdmin(StandardAdmin):
    list_display = (
        'id',
        'plataforma',
        'ip',
        'is_active',
    )
    search_fields = (
        'plataforma',
        'ip',
    )
    list_filter = (
        'is_active',
    )
