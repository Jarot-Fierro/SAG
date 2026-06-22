from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from core.models.usuarios import User
from core.standard.admin import StandardAdmin


@admin.register(User)
class UserAdmin(BaseUserAdmin, StandardAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'establecimiento', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'establecimiento')

    filter_horizontal = ('modulos',)

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
