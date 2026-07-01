from django import forms

from catalogo.models import Toner
from core.validations import validate_exists


class FormToner(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la categoria',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_categoria',
                'class': 'form-control',
                'placeholder': 'Estándar Negro / Alta Capacidad / Toner Color',
                'minlenght': '1',
                'maxlenght': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = Toner.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = Toner
        fields = ['nombre']
