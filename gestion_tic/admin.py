from django.contrib import admin, messages

from core.standard.admin import StandardAdmin
from gestion_tic.models import (
    TipoActivo, CampoTipoActivo, OpcionCampoTipoActivo,
    Activo, ActivoCaracteristica, TipoMovimiento, MovimientoActivo
)
from gestion_tic.models.catalogo import (
    Marca, Modelo, Propietario, JefeTic, Contrato, Ips
)


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
# ACTIVOS TIC ADMIN
# ==============================================================================

class CampoTipoActivoInline(admin.TabularInline):
    model = CampoTipoActivo
    extra = 1
    fields = ('nombre', 'tipo_campo', 'obligatorio', 'orden')


@admin.register(TipoActivo)
class TipoActivoAdmin(TicStandardAdmin):
    list_display = ('nombre', 'establecimiento', 'is_active')
    search_fields = ('nombre',)
    inlines = [CampoTipoActivoInline]


class OpcionCampoTipoActivoInline(admin.TabularInline):
    model = OpcionCampoTipoActivo
    extra = 1


@admin.register(CampoTipoActivo)
class CampoTipoActivoAdmin(TicStandardAdmin):
    list_display = ('nombre', 'tipo_activo', 'tipo_campo', 'orden')
    search_fields = ('nombre',)
    list_filter = ('tipo_activo', 'tipo_campo')
    inlines = [OpcionCampoTipoActivoInline]


@admin.register(TipoMovimiento)
class TipoMovimientoAdmin(TicStandardAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


class ActivoCaracteristicaInline(admin.TabularInline):
    model = ActivoCaracteristica
    extra = 0
    autocomplete_fields = ['campo']


class MovimientoActivoInline(admin.TabularInline):
    model = MovimientoActivo
    extra = 0
    fields = ('tipo_movimiento', 'funcionario', 'unidad_organizacional', 'ip', 'created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ['funcionario', 'unidad_organizacional', 'ip']


@admin.register(Activo)
class ActivoAdmin(TicStandardAdmin):
    list_display = ('codigo_barra', 'tipo', 'marca', 'modelo', 'serie', 'de_baja')
    list_filter = ('tipo', 'marca', 'de_baja', 'establecimiento')
    search_fields = ('codigo_barra', 'serie', 'observacion')
    inlines = [ActivoCaracteristicaInline, MovimientoActivoInline]
    autocomplete_fields = ['marca', 'modelo']


@admin.register(MovimientoActivo)
class MovimientoActivoAdmin(TicStandardAdmin):
    list_display = ('activo', 'tipo_movimiento', 'funcionario', 'unidad_organizacional', 'created_at')
    list_filter = ('tipo_movimiento', 'establecimiento', 'created_at')
    search_fields = ('activo__codigo_barra', 'activo__serie', 'funcionario__nombre')
    autocomplete_fields = ['activo', 'funcionario', 'unidad_organizacional', 'ip']
