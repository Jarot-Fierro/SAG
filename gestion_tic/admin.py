from django.contrib import admin, messages

from core.standard.admin import StandardAdmin
from gestion_tic.models.catalogo import (
    Marca, Modelo, Propietario, LicenciaOs,
    MicrosoftOffice, TipoCelular, TipoComputador,
    TipoImpresora, Toner, JefeTic, Contrato, Ips
)
from gestion_tic.models.celular import Celular
from gestion_tic.models.equipos import Equipo, AsignacionIP


# ==============================================================================
# BASE TIC ADMIN
# ==============================================================================

class TicStandardAdmin(StandardAdmin):
    actions = StandardAdmin.actions + ['asignar_establecimiento']

    @admin.action(description='Asignar mi establecimiento masivamente')
    def asignar_establecimiento(self, request, queryset):
        establecimiento = getattr(request.user, 'establecimiento', None)
        if not establecimiento:
            self.message_user(request, "Su usuario no tiene un establecimiento asignado.", level=messages.ERROR)
            return

        updated = queryset.update(establecimiento=establecimiento)
        self.message_user(request, f"Se han asignado {updated} registros al establecimiento: {establecimiento}")


# ==============================================================================
# CATALOGO ADMIN
# ==============================================================================

@admin.register(Marca)
class MarcaAdmin(TicStandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Modelo)
class ModeloAdmin(TicStandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Propietario)
class PropietarioAdmin(TicStandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(LicenciaOs)
class LicenciaOsAdmin(TicStandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(MicrosoftOffice)
class MicrosoftOfficeAdmin(TicStandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(TipoCelular)
class TipoCelularAdmin(TicStandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(TipoComputador)
class TipoComputadorAdmin(TicStandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(TipoImpresora)
class TipoImpresoraAdmin(TicStandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Toner)
class TonerAdmin(TicStandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(JefeTic)
class JefeTicAdmin(TicStandardAdmin):
    list_display = ('id', 'nombre', 'posicion', 'establecimiento')
    search_fields = ('nombre', 'posicion')
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Contrato)
class ContratoAdmin(TicStandardAdmin):
    list_display = ('id', 'nombre', 'establecimiento')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Ips)
class IpsAdmin(TicStandardAdmin):
    list_display = ('id', 'ip', 'asignado', 'establecimiento',)
    search_fields = ('ip', 'observacion')
    list_filter = ('asignado', 'establecimiento', 'is_active')
    list_display_links = ('ip',)
    ordering = ('ip',)


# ==============================================================================
# EQUIPOS ADMIN
# ==============================================================================

@admin.register(Equipo)
class EquipoAdmin(TicStandardAdmin):
    list_display = (
        'id', 'serie', 'tipo_equipo', 'marca', 'modelo',
        'establecimiento', 'responsable', 'de_baja',
    )
    search_fields = ('serie', 'mac', 'hh', 'observaciones')
    list_filter = (
        'tipo_equipo', 'marca', 'establecimiento',
        'de_baja', 'is_active'
    )
    list_display_links = ('serie',)
    ordering = ('serie',)
    autocomplete_fields = (
        'ip', 'marca', 'modelo', 'propietario',
        'establecimiento', 'responsable', 'jefe_entrega', 'contrato',
        'tipo_pc', 'sistema_operativo', 'microsoft_office',
        'tipo_impresora', 'toner'
    )


@admin.register(AsignacionIP)
class AsignacionIPAdmin(TicStandardAdmin):
    list_display = ('id', 'ip', 'equipo', 'activa', 'establecimiento')
    search_fields = ('ip__ip', 'equipo__serie', 'observacion')
    list_filter = ('activa', 'is_active')
    list_display_links = ('ip',)
    ordering = ('-updated_at',)


# ==============================================================================
# CELULAR ADMIN
# ==============================================================================

@admin.register(Celular)
class CelularAdmin(TicStandardAdmin):
    list_display = (
        'id', 'numero_telefono', 'imei', 'marca', 'modelo',
        'responsable', 'asignado', 'de_baja', 'establecimiento',
    )
    search_fields = ('numero_telefono', 'imei', 'numero_chip', 'observaciones')
    list_filter = (
        'marca', 'tipo', 'asignado', 'establecimiento',
        'de_baja', 'is_active'
    )
    list_display_links = ('numero_telefono',)
    ordering = ('numero_telefono',)
    autocomplete_fields = (
        'marca', 'modelo', 'tipo', 'propietario',
        'jefe_entrega', 'responsable', 'contrato', 'establecimiento'
    )
