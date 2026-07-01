from django import forms

from catalogo.models import MicrosoftOffice
from core.validations import validate_exists


class FormMicrosoftOffice(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la versión de microsoft office',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_microsoft_office',
                'class': 'form-control',
                'placeholder': 'office 2007, office 2016, office 2019, Microsoft 365',
                'minlenght': '1',
                'maxlenght': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = MicrosoftOffice.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = MicrosoftOffice
        fields = ['nombre']
