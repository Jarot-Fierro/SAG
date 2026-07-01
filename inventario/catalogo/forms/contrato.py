from django import forms

from catalogo.models import Contrato
from core.validations import validate_exists


class FormContrato(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre del contrato',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_contrato',
                'class': 'form-control',
                'placeholder': 'Tipo / Clausulas / Fecha del contrato',
                'minlenght': '1',
                'maxlenght': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = Contrato.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = Contrato
        fields = ['nombre']
