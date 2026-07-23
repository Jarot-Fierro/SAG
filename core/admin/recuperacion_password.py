from django.contrib import admin

from core.models.recuperacion_password import RecuperacionPassword


@admin.register(RecuperacionPassword)
class RecuperacionPasswordAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'establecimiento', 'fecha_creacion', 'estado', 'utilizado', 'solicitud_exitosa')
    list_filter = ('estado', 'utilizado', 'solicitud_exitosa', 'fecha_creacion')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'token_hash')
    readonly_fields = (
        'usuario', 'establecimiento', 'token_hash', 'fecha_creacion', 'fecha_expiracion',
        'utilizado', 'fecha_utilizacion', 'estado',
        'ip_solicitud', 'user_agent_solicitud', 'navegador_solicitud', 'version_navegador_solicitud',
        'sistema_operativo_solicitud', 'dispositivo_solicitud', 'es_pc_solicitud',
        'es_tablet_solicitud', 'es_movil_solicitud', 'es_bot_solicitud',
        'ip_utilizacion', 'user_agent_utilizacion', 'navegador_utilizacion', 'version_navegador_utilizacion',
        'sistema_operativo_utilizacion', 'dispositivo_utilizacion', 'es_pc_utilizacion',
        'es_tablet_utilizacion', 'es_movil_utilizacion', 'es_bot_utilizacion',
        'pais', 'region', 'ciudad', 'observacion', 'solicitud_exitosa'
    )

    def has_add_permission(self, request):
        return False
