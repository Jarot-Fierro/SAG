from colorfield.fields import ColorField
from django.db import models
from django.utils.safestring import mark_safe

from bodega.models.mantenedores import CategoriaProducto
from core.standard.models import StandardModelEstablishment


class Bodega(StandardModelEstablishment):
    COLOR_CHOICES = [
        ("#006FB3", "Primary (Azul)"),
        ("#7F8F99", "Secondary (Gris)"),
        ("#3fa1ad", "Success (Verde)"),
        ("#876bbe", "Info (Morado)"),
        ("#FFA11B", "Warning (Naranja)"),
        ("#1976D2", "Azul Corporativo"),
        ("#1565C0", "Azul Oscuro"),
        ("#0097A7", "Turquesa"),
        ("#2E7D32", "Verde"),
        ("#43A047", "Verde Claro"),
        ("#7CB342", "Lima"),
        ("#F57C00", "Naranjo"),
        ("#FFB300", "Ámbar"),
        ("#D32F2F", "Rojo"),
        ("#C62828", "Burdeo"),
        ("#8E24AA", "Morado"),
        ("#5E35B1", "Violeta"),
        ("#3949AB", "Índigo"),
        ("#455A64", "Gris Oscuro"),
        ("#607D8B", "Gris"),
    ]

    TEXT_COLOR_CHOICES = [
        ("#ffffff", "Blanco"),
        ("#000000", "Negro"),
    ]

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)

    color = ColorField(default='#006FB3', samples=COLOR_CHOICES)
    texto_color = ColorField(default='#ffffff', samples=TEXT_COLOR_CHOICES, verbose_name="Color de texto")

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
            """),
        default=
        """
        <svg class="small-box-icon" fill="currentColor" viewBox="0 0 24 24"
             xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path fill-rule="evenodd" clip-rule="evenodd"
                  d="M11.47 2.47a1.5 1.5 0 011.06 0l7.5 3A1.5 1.5 0 0121 6.86v10.28a1.5 1.5 0 01-.94 1.39l-7.5 3a1.5 1.5 0 01-1.12 0l-7.5-3A1.5 1.5 0 013 17.14V6.86a1.5 1.5 0 01.94-1.39l7.5-3zM12 3.94 5.2 6.66 12 9.38l6.8-2.72L12 3.94zm7.5 4.33-6.75 2.7v8.28l6.75-2.7V8.27zm-8.25 11V10.97L4.5 8.27v8.28l6.75 2.7z"/>
        </svg>
        """
    )

    categorias = models.ManyToManyField(
        CategoriaProducto,
        blank=True,
        related_name="bodegas"
    )

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
