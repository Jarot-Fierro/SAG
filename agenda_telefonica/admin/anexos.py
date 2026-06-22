from django.contrib import admin
from agenda_telefonica.models import Anexo
from core.standard.admin import StandardAdmin


@admin.register(Anexo)
class AnexoAdmin(StandardAdmin):
    list_display = (
        'anexo',
        'nombre',
        'anexo_publico',
        'departamento',
        'email',
        'active',
    )

    search_fields = (
        'anexo',
        'nombre',
        'email',
        'departamento__nombre',
    )

    list_filter = (
        'active',
        'departamento',
    )

    ordering = ('anexo',)