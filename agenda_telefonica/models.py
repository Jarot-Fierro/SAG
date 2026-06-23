from django.db import models

from core.standard.models import StandardModel, StandardModelEstablishment


class Direccion(StandardModelEstablishment):
    nombre = models.CharField(max_length=255, verbose_name="Nombre")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Dirección'
        verbose_name_plural = 'Direcciones'
        ordering = ['nombre']


class Ubicacion(StandardModelEstablishment):
    nombre = models.CharField(max_length=255, verbose_name="Nombre")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Ubicación'
        verbose_name_plural = 'Ubicaciones'
        ordering = ['nombre']


class Anexo(StandardModelEstablishment):
    anexo = models.CharField(max_length=20, unique=True, verbose_name="Anexo")
    anexo_publico = models.CharField(max_length=20, blank=True, null=True, verbose_name="Anexo Público")
    nombre = models.CharField(max_length=255, verbose_name="Nombre")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo")
    servicio = models.ForeignKey('agenda_telefonica.Servicio', blank=True, null=True, verbose_name="Servicio",
                                 on_delete=models.SET_NULL)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'
        ordering = ['nombre']


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


class Servicio(StandardModelEstablishment):
    nombre = models.CharField(max_length=255, verbose_name="Nombre")
    ubicacion = models.ForeignKey('agenda_telefonica.Ubicacion', blank=True, null=True, verbose_name="Ubicación",
                                  on_delete=models.SET_NULL)
    direccion = models.ForeignKey('agenda_telefonica.Direccion', blank=True, null=True, verbose_name="Dirección",
                                  on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.nombre} - {self.establecimiento}"

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['nombre']


class PerfilAgenda(StandardModel):
    usuario = models.OneToOneField(
        'core.User',
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    servicio = models.ManyToManyField('agenda_telefonica.Servicio', blank=True, verbose_name="Servicios")
    editor = models.BooleanField(default=True, verbose_name="Editor")
