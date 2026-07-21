from django.contrib import admin, messages
from django.shortcuts import render, redirect
from mptt.admin import DraggableMPTTAdmin

from core.models.direccion import Direccion
from core.models.unidad_organizacional import UnidadOrganizacional
from core.standard.admin import StandardAdmin


@admin.register(UnidadOrganizacional)
class UnidadOrganizacionalAdmin(DraggableMPTTAdmin, StandardAdmin):
    mptt_level_indent = 50
    list_display = ('tree_actions', 'indented_title', 'establecimiento', 'unidad_principal', 'direccion__nombre')
    list_display_links = ('indented_title',)
    list_filter = ('is_active', 'establecimiento', 'unidad_principal', 'es_departamento', 'es_subdepartamento')
    search_fields = ('nombre', 'establecimiento__nombre')
    autocomplete_fields = ('padre', 'direccion')
    actions = ['asignar_direccion_masiva', 'marcar_como_departamento', 'marcar_como_no_departamento',
               'marcar_como_subdepartamento', 'marcar_como_no_subdepartamento']

    @admin.action(description="Marcar como subdepartamento")
    def marcar_como_subdepartamento(self, request, queryset):
        count = queryset.update(es_subdepartamento=True)
        self.message_user(request, f"Se han marcado {count} unidades como subdepartamento.", messages.SUCCESS)

    @admin.action(description="Marcar como NO subdepartamento")
    def marcar_como_no_subdepartamento(self, request, queryset):
        count = queryset.update(es_subdepartamento=False)
        self.message_user(request, f"Se han marcado {count} unidades como NO subdepartamento.", messages.SUCCESS)

    @admin.action(description="Marcar como departamento")
    def marcar_como_departamento(self, request, queryset):
        count = queryset.update(es_departamento=True)
        self.message_user(request, f"Se han marcado {count} unidades como departamento.", messages.SUCCESS)

    @admin.action(description="Marcar como NO departamento")
    def marcar_como_no_departamento(self, request, queryset):
        count = queryset.update(es_departamento=False)
        self.message_user(request, f"Se han marcado {count} unidades como NO departamento.", messages.SUCCESS)

    @admin.action(description="Asignar dirección a seleccionados")
    def asignar_direccion_masiva(self, request, queryset):
        if 'apply' in request.POST:
            direccion_id = request.POST.get('direccion_id')
            if direccion_id:
                direccion = Direccion.objects.get(pk=direccion_id)
                count = queryset.update(direccion=direccion)
                self.message_user(request, f"Se ha asignado la dirección '{direccion.nombre}' a {count} unidades.",
                                  messages.SUCCESS)
                return redirect(request.get_full_path())
            else:
                self.message_user(request, "Debe seleccionar una dirección.", messages.ERROR)

        direcciones = Direccion.objects.all()
        return render(request, 'admin/core/unidadorganizacional/asignar_direccion.html', {
            'unidades': queryset,
            'direcciones': direcciones,
            'action': 'asignar_direccion_masiva'
        })
