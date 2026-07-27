from django.db import models

from core.standard.models import StandardModelEstablishment
from .tipo_activo import TipoActivo


class CampoTipoActivo(StandardModelEstablishment):
    # | Tipo            | Campo         |
    # | ----------      | ----------    |
    # | Computador      | RAM           |
    # | Computador      | Procesador    |
    # | Computador      | Disco         |
    # | Computador      | MAC           |
    # | UPS             | Potencia      |
    # | UPS             | Voltaje       |
    # | Monitor         | Pulgadas      |
    # | Monitor         | Resolución    |

    TIPO_CAMPO = (
        ("text", "Texto"),
        ("number", "Número"),
        ("date", "Fecha"),
        ("boolean", "Sí / No"),
        ("select", "Lista"),
    )

    tipo_activo = models.ForeignKey(
        TipoActivo,
        on_delete=models.CASCADE,
        related_name="campos"
    )

    nombre = models.CharField(
        max_length=100
    )

    tipo_campo = models.CharField(
        max_length=20,
        choices=TIPO_CAMPO,
        default="text"
    )

    obligatorio = models.BooleanField(
        default=False
    )

    orden = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        ordering = ["orden", "nombre"]

    def __str__(self):
        return f"{self.tipo_activo} - {self.nombre}"
