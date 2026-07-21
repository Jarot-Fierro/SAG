from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from import_export import resources

from core.models.usuarios import User
from core.standard.admin import StandardAdmin


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        import_id_fields = ('username',)
        skip_unchanged = True
        report_skipped = True


@admin.register(User)
class UserAdmin(BaseUserAdmin, StandardAdmin):
    reset_password_value = 'SSA.2026'

    list_display = ('username', 'email', 'first_name', 'last_name', 'establecimiento', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'establecimiento',)
    search_fields = ('username', 'email', 'first_name', 'last_name', 'establecimiento__nombre')

    actions = ['reset_password']

    def reset_password(self, request, queryset):
        for user in queryset:
            user.set_password(self.reset_password_value)
            user.save()
        self.message_user(request, f"Se ha reseteado la contraseña de {queryset.count()} usuarios correctamente.")

    reset_password.short_description = "Resetear contraseña"

    resource_class = UserResource

    filter_horizontal = ('modulos',)
    autocomplete_fields = (
        'establecimiento',
    )

    fieldsets = (
        (None, {'fields': ('username', 'password')}),

        ('Información Personal', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'establecimiento',
                'modulos'
            )
        }),

        ('Permisos', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
            )
        }),

        ('Fechas importantes', {
            'fields': (
                'last_login',
                'date_joined',
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
            )
        }),
    )
