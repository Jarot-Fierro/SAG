from django.contrib import admin

from core.forms.configuracion_correo import ConfiguracionCorreoForm
from core.models.configuracion_correo import ConfiguracionCorreo


@admin.register(ConfiguracionCorreo)
class ConfiguracionCorreoAdmin(admin.ModelAdmin):
    form = ConfiguracionCorreoForm
    list_display = ('establecimiento', 'email_remitente', 'smtp_host', 'activo')
    search_fields = ('establecimiento__nombre', 'email_remitente')
    list_filter = ('activo',)
