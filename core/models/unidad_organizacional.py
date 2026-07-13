from django.db import models

from core.models import Establecimiento
from core.standard.models import StandardModel


class UnidadOrganizacional(StandardModel):

    establecimiento = models.ForeignKey(
        Establecimiento,
        on_delete=models.PROTECT,
        related_name="unidades"
    )
    unidad_principal = models.BooleanField(default=False)
    nombre = models.CharField(max_length=200, default='SIN NOMBRE',null=False, blank=False)

    padre = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="hijos"
    )

    def __str__(self):
        return self.get_jerarquia()

    def get_jerarquia(self):
        nombres = [self.nombre]
        actual = self.padre
        while actual:
            nombres.append(actual.nombre)
            actual = actual.padre
        return " > ".join(reversed(nombres))

    def get_departamento(self):
        actual = self
        while actual:
            if "DEPARTAMENTO" in actual.nombre.upper():
                return actual.nombre
            actual = actual.padre
        return None

    def get_subdepto(self):
        actual = self
        while actual:
            if "SUBDEPTO" in actual.nombre.upper():
                return actual.nombre
            actual = actual.padre
        return None

    class Meta:
        verbose_name = "Unidad Organizacional"
        verbose_name_plural = "Unidades Organizacionales"