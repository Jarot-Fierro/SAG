from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from simple_history.admin import SimpleHistoryAdmin

from inventario.equipo.models.equipos import Equipo, AsignacionIP


# =====================================================
# RESOURCES
# =====================================================

class EquipoResource(resources.ModelResource):
    marca_nombre = Field(attribute='marca__nombre', column_name='Marca')
    modelo_nombre = Field(attribute='modelo__nombre', column_name='Modelo')
    establecimiento_nombre = Field(attribute='establecimiento__nombre', column_name='Establecimiento')
    responsable_nombre = Field(attribute='responsable__nombres', column_name='Responsable')
    ip_direccion = Field(attribute='ip__ip', column_name='IP')

    class Meta:
        model = Equipo
        import_id_fields = ['id']
        skip_unchanged = True
        report_skipped = True


class AsignacionIPResource(resources.ModelResource):
    ip_direccion = Field(attribute='ip__ip', column_name='IP')
    equipo_serie = Field(attribute='equipo__serie', column_name='Serie Equipo')

    class Meta:
        model = AsignacionIP
        import_id_fields = ['id']
        skip_unchanged = True
        report_skipped = True


# =====================================================
# ADMINS
# =====================================================
@admin.register(Equipo)
class EquipoAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = EquipoResource

    list_display = (
        "id",
        "tipo_equipo",
        "serie",
        "marca",
        "modelo",
        "ip",
        "establecimiento",
        "responsable",
        "de_baja",
        "is_active",
    )

    search_fields = (
        "serie",
        "mac",
        "hh",
        "marca__nombre",
        "modelo__nombre",
        "ip__ip",
        "responsable__nombres",
    )

    list_filter = (
        "tipo_equipo",
        "marca",
        "establecimiento",
        "de_baja",
        "is_active",
    )

    ordering = ("-id",)

    autocomplete_fields = (
        "ip",
        "marca",
        "modelo",
        "propietario",
        "departamento",
        "establecimiento",
        "responsable",
        "jefe_entrega",
        "contrato",
        "tipo_pc",
        "sistema_operativo",
        "microsoft_office",
        "tipo_impresora",
        "toner",
    )

    fieldsets = (

        ("Identificación General", {
            "fields": (
                "tipo_equipo",
                "serie",
                "ip",
                "marca",
                "modelo",
            )
        }),

        ("Ubicación / Responsable", {
            "fields": (
                "propietario",
                "departamento",
                "establecimiento",
                "responsable",
                "jefe_entrega",
                "contrato",
            )
        }),

        ("Datos PC / Notebook", {
            "fields": (
                "tipo_pc",
                "mac",
                "sistema_operativo",
                "microsoft_office",
                "es_armado",
                "ram_gb",
                "wifi",
                "procesador",
                "tarjeta_video",
                "red_lan",
                "tipo_disco",
                "capacidad_disco_gb",
            )
        }),

        ("Datos Impresora", {
            "fields": (
                "tipo_impresora",
                "hh",
                "toner",
            )
        }),

        ("Estado General", {
            "fields": (
                "de_baja",
                "is_active",
                "motivo_baja",
                "observaciones",
            )
        }),
    )


@admin.register(AsignacionIP)
class AsignacionIPAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = AsignacionIPResource

    list_display = (
        "id",
        "ip",
        "equipo",
        "activa",
        "is_active",
        "updated_at",
    )

    search_fields = (
        "ip__ip",
        "equipo__serie",
    )

    list_filter = (
        "activa",
        "is_active",
    )

    ordering = ("-id",)
