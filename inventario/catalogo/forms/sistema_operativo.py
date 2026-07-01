from django import forms

from catalogo.models import SistemaOperativo
from core.validations import validate_exists


class FormSistemaOperativo(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la sistema operativo',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_sistema_operativo',
                'class': 'form-control',
                'placeholder': 'Windows 11 / Windows 10 / Windows 7 / Linux / macOS',
                'minlenght': '1',
                'maxlenght': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = SistemaOperativo.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = SistemaOperativo
        fields = ['nombre']
