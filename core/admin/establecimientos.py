from django.contrib import admin, messages
from django.db.models import ProtectedError

from core.models.establecimientos import Establecimiento
from core.standard.admin import StandardAdmin


@admin.register(Establecimiento)
class EstablecimientoAdmin(StandardAdmin):
    list_display = ('id', 'nombre', 'region', 'telefono')
    search_fields = ('nombre', 'region')
    list_filter = ('is_active', 'region')
    list_display_links = (
        'nombre',
    )

    def delete_model(self, request, obj):
        try:
            from django.db import IntegrityError
            super().delete_model(request, obj)
        except ProtectedError as e:
            related_objects = [str(o) for o in e.protected_objects]
            self.message_user(
                request,
                f"No se puede eliminar '{obj}' porque tiene registros relacionados protegidos: {', '.join(related_objects[:5])}...",
                level=messages.ERROR
            )
        except IntegrityError:
            self.message_user(
                request,
                f"Error de integridad al intentar eliminar '{obj}'.",
                level=messages.ERROR
            )

    def delete_queryset(self, request, queryset):
        try:
            # Intentamos realizar la eliminación en una transacción para que sea atómica
            from django.db import transaction, IntegrityError
            with transaction.atomic():
                return super().delete_queryset(request, queryset)
        except ProtectedError as e:
            self.message_user(
                request,
                f"No se pudieron eliminar algunos establecimientos porque tienen registros relacionados protegidos.",
                level=messages.ERROR
            )
        except IntegrityError:
            self.message_user(
                request,
                "Error de integridad al intentar eliminar los establecimientos. Asegúrese de que no existan dependencias protegidas.",
                level=messages.ERROR
            )
