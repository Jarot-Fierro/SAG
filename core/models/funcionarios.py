from django.db import models

from core.standard.models import StandardModel


class PuestoTrabajo(StandardModel):
    nombre = models.CharField(max_length=100)

    UPPERCASE_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Puesto de Trabajo'
        verbose_name_plural = 'Puesto de Trabajo'

    def __str__(self):
        return self.nombre


class Funcionario(StandardModel):
    nombres = models.CharField(max_length=200, verbose_name='Nombres')
    rut = models.CharField(max_length=12, verbose_name='RUT', unique=True)
    correo = models.CharField(max_length=200, null=True, blank=True, verbose_name='Correo Electrónico')
    jefatura = models.BooleanField(default=False, verbose_name='¿Es Jefatura?')

    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Femenino')], default='NO INFORMADO',
                            verbose_name='Sexo')

    departamento = models.ForeignKey('core.Departamento', on_delete=models.CASCADE, null=True, blank=True,
                                     verbose_name='Departamento')
    puesto_trabajo = models.ForeignKey('core.PuestoTrabajo', on_delete=models.CASCADE, null=True, blank=True,
                                       verbose_name='Puesto de Trabajo')

    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de Nacimiento')

    establecimiento = models.ForeignKey('core.Establecimiento', on_delete=models.CASCADE, null=True, blank=True,
                                        verbose_name='Establecimiento')

    UPPERCASE_FIELDS = ['nombres', 'rut']
    LOWERCASE_FIELDS = ['correo']

    class Meta:
        verbose_name = 'Funcionario'
        verbose_name_plural = 'Funcionarios'

    def __str__(self):
        return self.nombres
