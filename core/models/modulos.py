from colorfield.fields import ColorField
from django.db import models
from django.utils.safestring import mark_safe

from core.standard.models import StandardModel


class Modulo(StandardModel):
    COLOR_CHOICES = [
        ("#006FB3", "Primary (Azul)"),
        ("#7F8F99", "Secondary (Gris)"),
        ("#3fa1ad", "Success (Verde)"),
        ("#876bbe", "Info (Morado)"),
        ("#FFA11B", "Warning (Naranja)"),
    ]

    nombre = models.CharField(max_length=100)
    icono = models.TextField(
        blank=True,
        help_text=mark_safe("""
        <p><strong>Formato esperado:</strong></p>

        <pre style="background:#f5f5f5;padding:10px;border-radius:4px;overflow:auto;">
    &lt;svg class="small-box-icon" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"&gt;
        &lt;path d="PEGAR_AQUI_EL_PATH"/&gt;
    &lt;/svg&gt;
        </pre>

        <p>
            Solo debe reemplazar el valor del atributo <code>d</code> del elemento
            <code>&lt;path&gt;</code>.
        </p>

        <p>
            Puede obtener el <strong>path</strong> desde
            <a href="https://heroicons.com/" target="_blank">Heroicons</a>
            (copiando únicamente el contenido del atributo <code>d</code>).
        </p>
        """)
    )
    codigo = models.CharField(
        max_length=50,
        unique=True
    )
    url = models.CharField(max_length=200, blank=True)
    consulta = models.CharField(max_length=200, blank=True)
    color = ColorField(default='#006FB3', samples=COLOR_CHOICES)
    en_mantenimiento = models.BooleanField(default=False)
    mantenimiento_hasta = models.DateTimeField(default=None, null=True, blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Modulo'
        verbose_name_plural = 'Modulos'
        ordering = ['nombre']
