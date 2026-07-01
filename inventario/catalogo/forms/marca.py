from django import forms

from catalogo.models import Marca
from core.validations import validate_exists


class FormMarca(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la marca',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_marca',
                'class': 'form-control',
                'placeholder': 'Entel, HP, ',
                'minlenght': '1',
                'maxlenght': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = Marca.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = Marca
        fields = ['nombre']
