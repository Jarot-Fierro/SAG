from django.contrib import admin

from core.standard.admin import StandardAdmin
from gestion_tic.models.catalogo import (
    Marca, Categoria, SubCategoria, Modelo, Propietario, LicenciaOs,
    MicrosoftOffice, SistemaOperativo, TipoCelular, TipoComputador,
    TipoImpresora, Toner, JefeTic, Contrato, PuestoTrabajo, Ips
)
from gestion_tic.models.celular import Celular
from gestion_tic.models.equipos import Equipo, AsignacionIP


# ==============================================================================
# CATALOGO ADMIN
# ==============================================================================

@admin.register(Marca)
class MarcaAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Categoria)
class CategoriaAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(SubCategoria)
class SubCategoriaAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'categoria', 'ver_mantencion', 'ver_informatica', 'is_active')
    search_fields = ('nombre', 'categoria__nombre')
    list_filter = ('categoria', 'ver_mantencion', 'ver_informatica', 'is_active')
    list_display_links = ('nombre',)
    ordering = ('categoria', 'nombre')


@admin.register(Modelo)
class ModeloAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Propietario)
class PropietarioAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(LicenciaOs)
class LicenciaOsAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(MicrosoftOffice)
class MicrosoftOfficeAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(SistemaOperativo)
class SistemaOperativoAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(TipoCelular)
class TipoCelularAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(TipoComputador)
class TipoComputadorAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(TipoImpresora)
class TipoImpresoraAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Toner)
class TonerAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(JefeTic)
class JefeTicAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'posicion', 'is_active')
    search_fields = ('nombre', 'posicion')
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Contrato)
class ContratoAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(PuestoTrabajo)
class PuestoTrabajoAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'is_active')
    search_fields = ('nombre',)
    list_filter = ('is_active',)
    list_display_links = ('nombre',)
    ordering = ('nombre',)


@admin.register(Ips)
class IpsAdmin(StandardAdmin):
    list_display = ('id', 'ip', 'asignado', 'establecimiento', 'is_active')
    search_fields = ('ip', 'observacion')
    list_filter = ('asignado', 'establecimiento', 'is_active')
    list_display_links = ('ip',)
    ordering = ('ip',)


# ==============================================================================
# EQUIPOS ADMIN
# ==============================================================================

@admin.register(Equipo)
class EquipoAdmin(StandardAdmin):
    list_display = (
        'id', 'serie', 'tipo_equipo', 'marca', 'modelo',
        'establecimiento', 'responsable', 'de_baja', 'is_active'
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
class AsignacionIPAdmin(StandardAdmin):
    list_display = ('id', 'ip', 'equipo', 'activa', 'is_active')
    search_fields = ('ip__ip', 'equipo__serie', 'observacion')
    list_filter = ('activa', 'is_active')
    list_display_links = ('ip',)
    ordering = ('-updated_at',)


# ==============================================================================
# CELULAR ADMIN
# ==============================================================================

@admin.register(Celular)
class CelularAdmin(StandardAdmin):
    list_display = (
        'id', 'numero_telefono', 'imei', 'marca', 'modelo',
        'responsable', 'asignado', 'de_baja', 'is_active'
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
