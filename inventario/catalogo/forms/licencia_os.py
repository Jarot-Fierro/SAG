from django import forms

from catalogo.models import LicenciaOs
from core.validations import validate_exists


class FormLicenciaOs(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la licencia_os',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_licencia_os',
                'class': 'form-control',
                'placeholder': 'Lebu',
                'minlenght': '1',
                'maxlenght': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = LicenciaOs.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = LicenciaOs
        fields = ['nombre']
