from django.contrib import admin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from mptt.admin import DraggableMPTTAdmin

from core.models import Establecimiento
from core.models.unidad_organizacional import UnidadOrganizacional
from core.standard.admin import StandardAdmin


class UnidadOrganizacionalResource(resources.ModelResource):
    establecimiento = fields.Field(
        column_name='establecimiento',
        attribute='establecimiento',
        widget=ForeignKeyWidget(Establecimiento, 'nombre')
    )
    padre = fields.Field(
        column_name='padre',
        attribute='padre',
        widget=ForeignKeyWidget(UnidadOrganizacional, 'nombre')
    )

    class Meta:
        model = UnidadOrganizacional
        # Excluir campos internos de MPTT que se gestionan automáticamente
        exclude = ('lft', 'rght', 'tree_id', 'level')

    def after_import(self, dataset, result, island=False, **kwargs):
        # Reconstruir el árbol MPTT después de la importación para asegurar la integridad
        UnidadOrganizacional.objects.rebuild()


@admin.register(UnidadOrganizacional)
class UnidadOrganizacionalAdmin(DraggableMPTTAdmin, StandardAdmin):
    resource_class = UnidadOrganizacionalResource
    mptt_level_indent = 20
    list_display = ('tree_actions', 'indented_title', 'establecimiento', 'unidad_principal', 'is_active')
    list_display_links = ('indented_title',)
    list_filter = ('is_active', 'establecimiento', 'unidad_principal')
    search_fields = ('nombre', 'establecimiento__nombre')
    autocomplete_fields = ('padre', 'direccion')
