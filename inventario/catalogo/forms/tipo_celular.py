from django import forms

from catalogo.models import TipoCelular
from core.validations import validate_exists


class FormTipoCelular(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la tipo plan',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_tipo_celular',
                'class': 'form-control',
                'placeholder': 'Smartphone / Anexo',
                'minlenght': '1',
                'maxlenght': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = TipoCelular.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = TipoCelular
        fields = ['nombre']
