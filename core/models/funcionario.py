from django.db import models

from core.standard.models import StandardModel


class Funcionario(StandardModel):
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True, verbose_name="Rut")
    nombres = models.CharField(max_length=255, null=True, blank=True, verbose_name="Nombres")
    apellidos = models.CharField(max_length=255, blank=True, null=True, verbose_name="Apellidos")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo")
    nombre = models.CharField(max_length=255, null=True, blank=True, verbose_name="Nombre")

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
        ordering = ["-id"]

    def __str__(self):
        return self.nombre
