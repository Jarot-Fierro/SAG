from django.contrib import admin

from agenda_telefonica.models import Anexo, PerfilAgenda, MenuSidebar
from core.standard.admin import StandardAdmin


@admin.register(Anexo)
class AnexoAdmin(StandardAdmin):
    list_display = (
        'id',
        'anexo',
        'nombre_anexo',
        'unidad_organizacional',
        'funcionario',
        'establecimiento',
    )
    list_display_links = (
        'id',
        'anexo',
        'funcionario',
    )
    search_fields = (
        'anexo',
        'establecimiento__nombre',
        'unidad_organizacional__nombre',
        'funcionario__rut',
        'funcionario__nombres',
    )
    list_filter = ('is_active', 'establecimiento',)
    autocomplete_fields = ('funcionario',)


@admin.register(MenuSidebar)
class MenuSidebarAdmin(StandardAdmin):
    list_display = (
        'id',
        'establecimiento',
        'orden',
        'mostrar',
    )

    search_fields = (
        'establecimiento__nombre',
    )

    list_filter = (
        'mostrar',
        'is_active',
    )
    list_display_links = (
        'id',
        'establecimiento__nombre',
    )

    ordering = (
        'orden',
        'establecimiento__nombre',
    )


@admin.register(PerfilAgenda)
class PerfilAgendaAdmin(StandardAdmin):
    list_display = ('id', 'usuario', 'mostrar_unidades', 'editor')
    search_fields = (
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
        'unidad_organizacional__nombre',
    )
    list_filter = ('editor', 'is_active')
    autocomplete_fields = ('usuario',)
    filter_horizontal = ('unidad_organizacional',)
    list_display_links = ('usuario',)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        field = super().formfield_for_manytomany(
            db_field, request, **kwargs
        )

        if db_field.name == 'unidad_organizacional':
            field.label_from_instance = lambda unidad: (
                f'{unidad.establecimiento} > {unidad.get_jerarquia()}'
            )

        return field

    @admin.display(description='Unidades organizacionales')
    def mostrar_unidades(self, obj):
        return ', '.join(
            # str(unidad)
            str(unidad.pk)
            for unidad in obj.unidad_organizacional.all()
        ) or 'Sin asignar'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'unidad_organizacional'
        )
