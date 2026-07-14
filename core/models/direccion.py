from django.db import models

from core.standard.models import StandardModel


class Direccion(StandardModel):
    nombre = models.CharField(max_length=150, unique=True)
    enlace_google_maps = models.URLField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="Pegue aquí el enlace de Google Maps. Puede ser el enlace de 'Compartir' o el de 'Insertar un mapa'. "
                  "Para obtener mejores resultados: 1. Busque la dirección en Google Maps. 2. Haga clic en 'Compartir'. "
                  "3. Seleccione 'Insertar un mapa' y copie solo el contenido entre comillas de 'src=\"...\"'. "
                  "Si pega el enlace normal de compartir, se mostrará un botón para abrirlo externamente."
    )

    class Meta:
        ordering = ['nombre']
        verbose_name = "Dirección"
        verbose_name_plural = "Direcciones"

    def __str__(self):
        return self.nombre
