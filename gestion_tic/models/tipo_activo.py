from django.db import models

from core.standard.models import StandardModelEstablishment


class TipoActivo(StandardModelEstablishment):
    # Computador
    # Notebook
    # Monitor
    # UPS
    # Impresora
    # Anexo
    # Router
    # Switch
    # Servidor
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre"
    )

    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción"
    )

    class Meta:
        verbose_name = "Tipo de Activo"
        verbose_name_plural = "Tipos de Activos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
