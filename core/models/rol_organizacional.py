from django.db import models

from core.standard.models import StandardModel


class RolOrganizacional(StandardModel):
    nombre = models.CharField(max_length=100,unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Rol Organizacional"
        verbose_name_plural = "Roles Organizacionales"

    def __str__(self):
        return self.nombre