from django import forms

from catalogo.models import Propietario
from core.validations import validate_exists


class FormPropietario(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre del propietario',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_propietario',
                'class': 'form-control',
                'placeholder': 'Propietario',
                'minlenght': '1',
                'maxlenght': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = Propietario.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = Propietario
        fields = ['nombre']
