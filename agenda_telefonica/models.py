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
    cargo = models.ForeignKey('agenda_telefonica.NivelOrganizacional', on_delete=models.CASCADE, null=True, blank=True, related_name='funcionarios')
    servicio = models.ManyToManyField('agenda_telefonica.Servicio', blank=True, verbose_name="Servicios")
    editor = models.BooleanField(default=True, verbose_name="Editor")
    mantenedores = models.BooleanField(default=False, verbose_name="¿Acceso a Mantenedores?")
    jefatura = models.BooleanField(default=False, verbose_name="¿Es Jefatura?")
    subrrogante = models.BooleanField(default=False, verbose_name="¿Es subrrogante?")
    posicion_subrrogante = models.IntegerField(default=0, verbose_name="Posición de subrogante", help_text="Si le dió Check"
                                                   "a es subrrogante entonces indique la posición")



class NivelOrganizacional(StandardModelEstablishment):
    """Modelo para manejar todos los niveles jerárquicos de manera flexible"""
    TIPO_NIVEL = [
        ('SUB', 'Subdirección'),
        ('SEC', 'Secretaría'),
        ('DPT', 'Departamento'),
        ('SDP', 'Subdepartamento'),
        ('UNI', 'Unidad'),
        ('SECC', 'Sección'),
        ('ENC', 'Encargado/a'),
        ('COORD', 'Coordinación'),
        ('OTRO', 'Otro'),
    ]

    tipo = models.CharField(max_length=50, choices=TIPO_NIVEL)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='hijos')
    orden = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Nivel Organizacional"
        verbose_name_plural = "Niveles Organizacionales"
        ordering = ['tipo', 'orden', 'nombre']

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.nombre}"

    def get_nivel_completo(self):
        """Retorna la jerarquía completa desde la raíz hasta este nivel"""
        niveles = []
        actual = self
        while actual:
            niveles.insert(0, actual.nombre)
            actual = actual.padre
        return ' > '.join(niveles)


class Cargo(StandardModel):
    nombre = models.CharField(max_length=200)
    codigo = models.CharField(max_length=50, unique=True, null=True, blank=True)
    nivel = models.ForeignKey(NivelOrganizacional, on_delete=models.CASCADE, related_name='cargos')
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} - {self.nivel.nombre}"