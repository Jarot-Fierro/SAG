from django.apps import AppConfig


class InventarioTicConfig(AppConfig):
    name = 'inventario_tic'

    def ready(self):
        from . import signals  # noqa: F401
