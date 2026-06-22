from django.contrib import admin
from django.utils.html import format_html

from core.models.modulos import Modulo
from core.standard.admin import StandardAdmin


@admin.register(Modulo)
class ModuloAdmin(StandardAdmin):
    list_display = ('nombre', 'codigo', 'url', 'icono_corto', 'color')
    search_fields = ('nombre', 'codigo')
    list_filter = ('is_active',)

    def icono_corto(self, obj):
        return format_html(
            '<span title="{}">{}</span>',
            obj.icono,
            obj.icono[:20] + "..." if len(obj.icono) > 20 else obj.icono
        )
