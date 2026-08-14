from django.db import models

from core.standard.models import StandardModelEstablishment
from .activo import Activo
from .campo_tipo_activo import CampoTipoActivo


class ActivoCaracteristica(StandardModelEstablishment):
    # | Campo           | Valor         |
    # | ----------      | -----------   |
    # | RAM             | 16GB          |
    # | Procesador      | Inteli5       |
    # | Disco           | 512 SSD       |
    # | MAC             | AA: BB:CC: DD |

    activo = models.ForeignKey(
        Activo,
        on_delete=models.CASCADE,
        related_name="caracteristicas"
    )

    campo = models.ForeignKey(
        CampoTipoActivo,
        on_delete=models.CASCADE
    )

    valor = models.TextField(
        blank=True
    )

    class Meta:
        unique_together = (
            "activo",
            "campo",
        )

    def __str__(self):
        return f"{self.campo.nombre}: {self.valor}"
