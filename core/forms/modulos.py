from django import forms

from ..models.modulos import Modulo


class ModuloForm(forms.ModelForm):
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

    nombre = forms.CharField(
        label='Nombre del Modulo',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_modulo',
                'class': 'form-control',
                'placeholder': 'Nombre del Modulo',
                'minlength': '1',
            }
        )
    )
    icono = forms.CharField(
        label='Icono',
        widget=forms.Textarea(
            attrs={
                'id': 'icono_modulo',
                'class': 'form-control',
                'placeholder': 'Icono',
                'rows': 1,
            }
        ),
        help_text="""
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
        """
    )

    codigo = forms.CharField(
        label='Código del Modulo',
        widget=forms.TextInput(
            attrs={
                'id': 'codigo_modulo',
                'class': 'form-control',
                'placeholder': 'Código del Modulo',
                'minlength': '1',
            }
        )
    )

    url = forms.CharField(
        label='URL',
        required=False,
        widget=forms.TextInput(
            attrs={
                'id': 'url_modulo',
                'class': 'form-control',
                'placeholder': 'URL del Modulo',
            }
        )
    )

    consulta = forms.CharField(
        label='Consulta',
        required=False,
        widget=forms.TextInput(
            attrs={
                'id': 'consulta_modulo',
                'class': 'form-control',
                'placeholder': 'Consulta SQL o similar',
            }
        )
    )

    color = forms.ChoiceField(
        label='Color',
        choices=COLOR_CHOICES,
        widget=forms.Select(
            attrs={
                'id': 'color_modulo',
                'class': 'form-control select2',
            }
        ),
        initial='#006FB3'
    )

    texto_color = forms.ChoiceField(
        label='Color de texto',
        choices=TEXT_COLOR_CHOICES,
        widget=forms.Select(
            attrs={
                'id': 'texto_color_modulo',
                'class': 'form-control select2',
            }
        ),
        initial='#ffffff'
    )

    en_mantenimiento = forms.BooleanField(
        label='En mantenimiento',
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                'id': 'en_mantenimiento_modulo',
                'class': 'form-check-input',
            }
        )
    )

    mantenimiento_hasta = forms.DateTimeField(
        label='Mantenimiento hasta',
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                'id': 'mantenimiento_hasta_modulo',
                'class': 'form-control',
                'type': 'datetime-local',
            }
        )
    )

    es_clinico = forms.BooleanField(
        label='Es clínico',
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                'id': 'es_clinico_modulo',
                'class': 'form-check-input',
            }
        )
    )

    class Meta:
        model = Modulo
        fields = [
            'nombre', 'icono', 'codigo', 'url', 'consulta',
            'color', 'texto_color', 'en_mantenimiento',
            'mantenimiento_hasta', 'es_clinico'
        ]
