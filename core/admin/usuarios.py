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
    list_display = ('username', 'email', 'first_name', 'last_name', 'departamento', 'establecimiento', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'establecimiento')

    resource_class = UserResource

    filter_horizontal = ('modulos',)
    autocomplete_fields = (
        'establecimiento',
        'departamento',
    )

    fieldsets = (
        (None, {'fields': ('username', 'password')}),

        ('Información Personal', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'establecimiento',
                'departamento',
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
