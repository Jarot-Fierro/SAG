from django.contrib.auth.models import Group
from django.db import models

from core.standard.models import StandardModel, StandardModelEstablishment


class Anexo(StandardModelEstablishment):
    anexo = models.CharField(max_length=6, unique=True, verbose_name="Anexo")
    anexo_publico = models.CharField(max_length=20, blank=True, null=True, verbose_name="Anexo Público")
    numero_telefonico = models.CharField(max_length=20, blank=True, null=True,
                                         verbose_name="Número Telefónico Institucional")

    funcionario = models.OneToOneField('core.Funcionario', blank=True, null=True, verbose_name="Funcionario",
                                       on_delete=models.SET_NULL)

    def __str__(self):
        return self.anexo

    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'
        ordering = ['-anexo']


class MenuSidebar(StandardModel):
    establecimiento = models.ForeignKey(
        'core.Establecimiento',
        on_delete=models.CASCADE,
        verbose_name='Establecimiento'
    )

    orden = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden'
    )

    mostrar = models.BooleanField(
        default=True,
        verbose_name='Mostrar en menú'
    )

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return str(self.establecimiento)


class PerfilAgenda(StandardModel):
    usuario = models.OneToOneField(
        'core.User',
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    # servicio = models.ManyToManyField(Servicio, blank=True, verbose_name="Servicios")
    editor = models.BooleanField(default=True, verbose_name="Editor")
    mantenedores = models.BooleanField(default=False, verbose_name="¿Acceso a Mantenedores?")
    unidad_organizacional = models.ManyToManyField(
        'core.UnidadOrganizacional',
        verbose_name='Unidad Organizacional',
        blank=True
    )
