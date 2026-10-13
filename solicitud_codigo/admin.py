from django.contrib import admin

from core.standard.admin import StandardAdmin
from solicitud_codigo.models import (
    AreaSolicitud,
    SubareaSolicitud,
    MaestraCodigoSISSA,
    PerfilCodigo,
    SolicitudCodigo,
    HistorialSolicitudCodigo,
)


class SubareaSolicitudInline(admin.TabularInline):
    model = SubareaSolicitud
    extra = 1
    fields = ('nombre', 'codigo', 'descripcion', 'is_active')


@admin.register(AreaSolicitud)
class AreaSolicitudAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'codigo', 'is_active')
    search_fields = ('nombre', 'codigo')
    list_filter = ('is_active',)
    inlines = [SubareaSolicitudInline]


@admin.register(SubareaSolicitud)
class SubareaSolicitudAdmin(StandardAdmin):
    list_display = ('id', 'area', 'nombre', 'codigo', 'is_active')
    search_fields = ('nombre', 'codigo', 'area__nombre')
    list_filter = ('area', 'is_active')


@admin.register(MaestraCodigoSISSA)
class MaestraCodigoSISSAAdmin(StandardAdmin):
    list_display = ('id', 'codigo', 'nombre_producto', 'presentacion', 'area', 'subarea', 'is_active')
    search_fields = ('codigo', 'nombre_producto', 'presentacion', 'descripcion')
    list_filter = ('area', 'is_active')


@admin.register(PerfilCodigo)
class PerfilCodigoAdmin(StandardAdmin):
    list_display = (
        'id',
        'usuario',
        'es_referente',
        'es_referente_global',
        'puede_validar',
        'puede_crear_codigos',
        'puede_solicitar',
        'is_active',
    )
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
    list_filter = ('es_referente', 'es_referente_global', 'puede_validar', 'puede_crear_codigos', 'is_active')
    filter_horizontal = ('areas_asignadas',)


class HistorialSolicitudCodigoInline(admin.TabularInline):
    model = HistorialSolicitudCodigo
    extra = 0
    readonly_fields = ('usuario', 'accion', 'estado_anterior', 'estado_nuevo', 'detalle', 'fecha')
    can_delete = False


@admin.register(SolicitudCodigo)
class SolicitudCodigoAdmin(StandardAdmin):
    list_display = (
        'id',
        'numero_solicitud',
        'establecimiento',
        'usuario_solicitante',
        'area',
        'subarea',
        'producto_base',
        'estado',
        'fecha_solicitud',
        'is_active',
    )
    search_fields = (
        'numero_solicitud',
        'producto_base',
        'presentacion',
        'usuario_solicitante__username',
        'usuario_solicitante__first_name',
        'usuario_solicitante__last_name',
    )
    list_filter = ('estado', 'establecimiento', 'area', 'fecha_solicitud', 'is_active')
    list_display_links = ('numero_solicitud',)
    inlines = [HistorialSolicitudCodigoInline]


@admin.register(HistorialSolicitudCodigo)
class HistorialSolicitudCodigoAdmin(admin.ModelAdmin):
    list_display = ('id', 'solicitud', 'accion', 'estado_anterior', 'estado_nuevo', 'usuario', 'fecha')
    search_fields = ('solicitud__numero_solicitud', 'accion', 'detalle', 'usuario__username')
    list_filter = ('accion', 'fecha')
    readonly_fields = ('solicitud', 'usuario', 'accion', 'estado_anterior', 'estado_nuevo', 'detalle', 'fecha')
