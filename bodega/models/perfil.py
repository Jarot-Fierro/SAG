from django.db import models

from bodega.models.bodega import Bodega
from config import settings
from core.standard.models import StandardModel


class PerfilBodega(StandardModel):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_bodega"
    )

    bodegas = models.ManyToManyField(
        Bodega,
        blank=True,
        related_name="usuarios"
    )

    class Meta:
        verbose_name = "Perfil de bodega"
        verbose_name_plural = "Perfiles de bodega"

    def __str__(self):
        return self.usuario.get_username()
