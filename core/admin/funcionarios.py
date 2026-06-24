from django.contrib import admin
from import_export import resources

from core.models.funcionarios import Funcionario
from core.models.funcionarios import PuestoTrabajo
from core.standard.admin import StandardAdmin


class FuncionarioResource(resources.ModelResource):
    class Meta:
        model = Funcionario
        import_id_fields = ('rut',)


@admin.register(PuestoTrabajo)
class PuestoTrabajoAdmin(StandardAdmin):
    list_display = (
        'id',
        'nombre',
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


@admin.register(Funcionario)
class FuncionarioAdmin(StandardAdmin):
    resource_class = FuncionarioResource
    list_display = (
        'id',
        'nombres',
        'rut',
        'correo',
        'departamento',
        'puesto_trabajo',
        'jefatura',

    )

    search_fields = (
        'nombres',
        'rut',
        'correo',
    )

    list_filter = (
        'is_active',
        'jefatura',
        'establecimiento',
        'puesto_trabajo',
    )

    list_display_links = (
        'nombres',
    )

    ordering = (
        'nombres',
    )
