from django import forms

from core.validations import validate_exists
from inventario.models import CategoriaInventario


class FormCategoriaInventario(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la categoria_inventario',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_categoria_inventario',
                'class': 'form-control',
                'placeholder': '',
                'minlenght': '1',
                'maxlenght': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = CategoriaInventario.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = CategoriaInventario
        fields = ['nombre']
