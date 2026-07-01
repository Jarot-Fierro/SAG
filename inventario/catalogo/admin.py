from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    Marca, Categoria, SubCategoria, Modelo, Propietario,
    LicenciaOs, MicrosoftOffice, SistemaOperativo, TipoCelular,
    TipoComputador, TipoImpresora, Toner, JefeTic, Contrato, PuestoTrabajo, Ips
)


# --- Resources ---

class MarcaResource(resources.ModelResource):
    class Meta:
        model = Marca
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'is_active')
        export_order = ('id', 'nombre', 'is_active')
        skip_unchanged = True
        report_skipped = True


class CategoriaResource(resources.ModelResource):
    class Meta:
        model = Categoria
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'is_active')
        export_order = ('id', 'nombre', 'is_active')
        skip_unchanged = True
        report_skipped = True


class SubCategoriaResource(resources.ModelResource):
    categoria_nombre = Field(attribute='categoria__nombre', column_name='Categoría')

    class Meta:
        model = SubCategoria
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'categoria', 'categoria_nombre', 'is_active')
        export_order = ('id', 'nombre', 'categoria_nombre', 'is_active')
        skip_unchanged = True
        report_skipped = True


class ModeloResource(resources.ModelResource):
    class Meta:
        model = Modelo
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'is_active')
        export_order = ('id', 'nombre', 'is_active')
        skip_unchanged = True
        report_skipped = True


class PropietarioResource(resources.ModelResource):
    class Meta:
        model = Propietario
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'is_active')
        export_order = ('id', 'nombre', 'is_active')
        skip_unchanged = True
        report_skipped = True


class LicenciaOsResource(resources.ModelResource):
    class Meta:
        model = LicenciaOs
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'is_active')
        export_order = ('id', 'nombre', 'is_active')
        skip_unchanged = True
        report_skipped = True


class MicrosoftOfficeResource(resources.ModelResource):
    class Meta:
        model = MicrosoftOffice
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'is_active')
        export_order = ('id', 'nombre', 'is_active')
        skip_unchanged = True
        report_skipped = True


class SistemaOperativoResource(resources.ModelResource):
    class Meta:
        model = SistemaOperativo
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'is_active')
        export_order = ('id', 'nombre', 'is_active')
        skip_unchanged = True
        report_skipped = True


class TipoCelularResource(resources.ModelResource):
    class Meta:
        model = TipoCelular
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'is_active')
        export_order = ('id', 'nombre', 'is_active')
        skip_unchanged = True
        report_skipped = True


class TipoComputadorResource(resources.ModelResource):
    class Meta:
        model = TipoComputador
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'is_active')
        export_order = ('id', 'nombre', 'is_active')
        skip_unchanged = True
        report_skipped = True


class TipoImpresoraResource(resources.ModelResource):
    class Meta:
        model = TipoImpresora
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'is_active')
        export_order = ('id', 'nombre', 'is_active')
        skip_unchanged = True
        report_skipped = True


class TonerResource(resources.ModelResource):
    class Meta:
        model = Toner
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'is_active')
        export_order = ('id', 'nombre', 'is_active')
        skip_unchanged = True
        report_skipped = True


class JefeTicResource(resources.ModelResource):
    class Meta:
        model = JefeTic
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'posicion', 'is_active')
        export_order = ('id', 'nombre', 'posicion', 'is_active')
        skip_unchanged = True
        report_skipped = True


class ContratoResource(resources.ModelResource):
    class Meta:
        model = Contrato
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'is_active')
        export_order = ('id', 'nombre', 'is_active')
        skip_unchanged = True
        report_skipped = True


class PuestoTrabajoResource(resources.ModelResource):
    class Meta:
        model = PuestoTrabajo
        import_id_fields = ['id']
        fields = ('id', 'nombre', 'is_active')
        export_order = ('id', 'nombre', 'is_active')
        skip_unchanged = True
        report_skipped = True


class IpsResource(resources.ModelResource):
    class Meta:
        model = Ips
        import_id_fields = ['id']
        fields = ('id', 'ip', 'asignado', 'establecimiento', 'departamento')
        export_order = ('id', 'ip', 'is_active')
        skip_unchanged = True
        report_skipped = True


# --- Admins ---

@admin.register(Marca)
class MarcaAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = MarcaResource
    list_display = ("id", "nombre", "is_active")
    search_fields = ("nombre",)
    ordering = ("-id",)


@admin.register(Categoria)
class CategoriaAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = CategoriaResource
    list_display = ("id", "nombre", "is_active")
    search_fields = ("nombre",)
    ordering = ("-id",)


@admin.register(SubCategoria)
class SubCategoriaAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = SubCategoriaResource
    list_display = ("id", "nombre", "categoria", "is_active")
    search_fields = ("nombre", "categoria__nombre")
    ordering = ("-id",)


@admin.register(Modelo)
class ModeloAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = ModeloResource
    list_display = ("id", "nombre", "is_active")
    search_fields = ("nombre",)
    ordering = ("-id",)


@admin.register(Propietario)
class PropietarioAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = PropietarioResource
    list_display = ("id", "nombre", "is_active")
    search_fields = ("nombre",)
    ordering = ("-id",)


@admin.register(LicenciaOs)
class LicenciaOsAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = LicenciaOsResource
    list_display = ("id", "nombre", "is_active")
    search_fields = ("nombre",)
    ordering = ("-id",)


@admin.register(MicrosoftOffice)
class MicrosoftOfficeAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = MicrosoftOfficeResource
    list_display = ("id", "nombre", "is_active")
    search_fields = ("nombre",)
    ordering = ("-id",)


@admin.register(SistemaOperativo)
class SistemaOperativoAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = SistemaOperativoResource
    list_display = ("id", "nombre", "is_active")
    search_fields = ("nombre",)
    ordering = ("-id",)


@admin.register(TipoCelular)
class TipoCelularAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = TipoCelularResource
    list_display = ("id", "nombre", "is_active")
    search_fields = ("nombre",)
    ordering = ("-id",)


@admin.register(TipoComputador)
class TipoComputadorAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = TipoComputadorResource
    list_display = ("id", "nombre", "is_active")
    search_fields = ("nombre",)
    ordering = ("-id",)


@admin.register(TipoImpresora)
class TipoImpresoraAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = TipoImpresoraResource
    list_display = ("id", "nombre", "is_active")
    search_fields = ("nombre",)
    ordering = ("-id",)


@admin.register(Toner)
class TonerAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = TonerResource
    list_display = ("id", "nombre", "is_active")
    search_fields = ("nombre",)
    ordering = ("-id",)


@admin.register(JefeTic)
class JefeTicAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = JefeTicResource
    list_display = ("id", "nombre", "posicion", "is_active")
    search_fields = ("nombre", "posicion")
    ordering = ("-id",)


@admin.register(Contrato)
class ContratoAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = ContratoResource
    list_display = ("id", "nombre", "is_active")
    search_fields = ("nombre",)
    ordering = ("-id",)


@admin.register(PuestoTrabajo)
class PuestoTrabajoAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = PuestoTrabajoResource
    list_display = ("id", "nombre", "is_active")
    search_fields = ("nombre",)
    ordering = ("-id",)


@admin.register(Ips)
class IpsAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    resource_class = IpsResource
    list_display = ("id", "ip", "asignado", "establecimiento", "departamento")
    search_fields = ("ip",)
    ordering = ("-id",)
