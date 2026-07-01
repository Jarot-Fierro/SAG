from django import forms

from catalogo.models import TipoComputador
from core.validations import validate_exists


class FormTipoComputador(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la tipo computador',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_tipo_computador',
                'class': 'form-control',
                'placeholder': 'Escritorio/Notebook/OnlyOne',
                'minlenght': '1',
                'maxlenght': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = TipoComputador.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = TipoComputador
        fields = ['nombre']
