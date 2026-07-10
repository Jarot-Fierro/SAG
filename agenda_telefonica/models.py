from django.db import models

from core.standard.models import StandardModel, StandardModelEstablishment


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



class PerfilAgenda(StandardModel):
    usuario = models.OneToOneField(
        'core.User',
        on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    cargo = models.ForeignKey('agenda_telefonica.NivelOrganizacional', on_delete=models.CASCADE, null=True, blank=True, related_name='funcionarios')
    servicio = models.ManyToManyField('agenda_telefonica.Servicio', blank=True, verbose_name="Servicios")
    editor = models.BooleanField(default=True, verbose_name="Editor")
    mantenedores = models.BooleanField(default=False, verbose_name="¿Acceso a Mantenedores?")
    jefatura = models.BooleanField(default=False, verbose_name="¿Es Jefatura?")
    subrrogante = models.BooleanField(default=False, verbose_name="¿Es subrrogante?")
    posicion_subrrogante = models.IntegerField(default=0, verbose_name="Posición de subrogante", help_text="Si le dió Check"
                                                   "a es subrrogante entonces indique la posición")

