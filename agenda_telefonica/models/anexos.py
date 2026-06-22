from django.db import models

from core.standard.models import StandardModel


# Create your models here.
class Anexo(StandardModel):
    anexo = models.CharField(max_length=20, unique=True, verbose_name="Anexo")
    anexo_publico = models.CharField(max_length=20, blank=True, null=True, verbose_name="Anexo Público")
    nombre = models.CharField(max_length=255, verbose_name="Nombre")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo")
    departamento = models.ForeignKey('core.Departamento',blank=True, null=True, verbose_name="Departamento", on_delete=models.SET_NULL)
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    active = models.BooleanField(default=True, verbose_name="Activo")

    def __str__(self):
        return self.nombre