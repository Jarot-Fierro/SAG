from django import forms

from catalogo.models import SubCategoria, Categoria
from core.validations import validate_exists


class FormSubCategoria(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la subcategoria',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_subcategoria',
                'class': 'form-control',
                'placeholder': 'Pulgadas/Modelo/Tipo',
                'minlenght': '1',
                'maxlenght': '100'
            }),
        required=True
    )
    categoria = forms.ModelChoiceField(
        required=True,
        empty_label='Selecciona una Categoría',
        label='Categoría',
        queryset=Categoria.objects.filter(status=True),
        widget=forms.Select(
            attrs={
                'id': 'categoria_subcategoria',
                'class': 'form-control select2',
            }
        ),
    )
    ver_mantencion = forms.BooleanField(
        required=False,
        label='Ver para Mantención',
        widget=forms.CheckboxInput(attrs={'class': 'mt-4 form-check-input'}),
    )
    ver_informatica = forms.BooleanField(
        required=False,
        label='Ver para Informática',
        widget=forms.CheckboxInput(attrs={'class': 'mt-4 form-check-input'}),
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = SubCategoria.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = SubCategoria
        fields = ['nombre', 'categoria', 'ver_mantencion', 'ver_informatica']
