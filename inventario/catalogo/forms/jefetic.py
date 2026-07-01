from django import forms

from catalogo.models import JefeTic
from core.validations import validate_exists


class FormJefeTic(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_categoria',
                'class': 'form-control',
                'placeholder': 'Nombre de la Jefatura',
                'minlenght': '1',
                'maxlenght': '100'
            }),
        required=True
    )
    posicion = forms.ChoiceField(
        label='Posicion',
        choices=[
            ('JEFE DPTO TIC', 'JEFE DPTO TIC'),
            ('JEFE(S) DPTO TIC', 'JEFE(S) DPTO TIC'),
            ('JEFE DPTO MNT', 'JEFE DPTO MNT'),
            ('JEFE(S) DPTO MNT', 'JEFE(S) DPTO MNT')
        ],
        widget=forms.Select(
            attrs={
                'id': 'nombre_categoria',
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

        exists = JefeTic.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = JefeTic
        fields = ['nombre', 'posicion']
