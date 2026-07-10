from django.conf import settings
from django.db import models

from core.standard.models import StandardModel


class Funcionario(StandardModel):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="funcionario_profile",
        verbose_name="Usuario",
        null=True,
        blank=True,
        help_text="Usuario del sistema asociado al funcionario."
    )

    establecimiento = models.ForeignKey(
        "core.Establecimiento",
        on_delete=models.PROTECT,
        related_name="funcionarios",
        verbose_name="Establecimiento"
    )

    cargo = models.ForeignKey(
        "core.Cargo",
        on_delete=models.PROTECT,
        related_name="funcionarios",
        verbose_name="Cargo",
        help_text="Encargado De: Cargo que desempeña el funcionario en el establecimiento."
    )
    profesion = models.ForeignKey(
        "core.Profesion",
        on_delete=models.PROTECT,
        related_name="profesiones",
        verbose_name="Profesion"
    )

    rol_organizacional = models.ForeignKey(
        "core.RolOrganizacional",
        on_delete=models.PROTECT,
        related_name="funcionarios",
        null=True,
        blank=True,
        verbose_name="Rol organizacional",
        help_text="Jefe, Subrogante, Coordinador, Encargado, etc."
    )

    unidad_organizacional = models.ForeignKey(
        "core.UnidadOrganizacional",
        on_delete=models.SET_NULL,
        related_name="funcionarios",
        null=True,
        blank=True,
        verbose_name="Unidad Organizacional"
    )

    class Meta:
        verbose_name = "Funcionario"
        verbose_name_plural = "Funcionarios"
        ordering = ["user__first_name", "user__last_name"]

    def __str__(self):
        if self.user:
            return self.user.get_full_name()
        return f"Funcionario #{self.pk}"