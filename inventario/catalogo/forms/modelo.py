from django import forms

from catalogo.models import Modelo
from core.validations import validate_exists


class FormModelo(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la modelo',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_modelo',
                'class': 'form-control',
                'placeholder': 'Serie del Modelo',
                'minlenght': '1',
                'maxlenght': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = Modelo.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = Modelo
        fields = ['nombre']
