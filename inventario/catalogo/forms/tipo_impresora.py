from django import forms

from catalogo.models import TipoImpresora
from core.validations import validate_exists


class FormTipoImpresora(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la tipo impresora',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_tipo_impresora',
                'class': 'form-control',
                'placeholder': 'Multifuncion / Con escaner',
                'minlenght': '1',
                'maxlenght': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = TipoImpresora.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = TipoImpresora
        fields = ['nombre']
