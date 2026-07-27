from django import forms

from ..models.tipo_activo import TipoActivo


class FormTipoActivo(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Computador, Impresora, etc.'
        })
    )
    descripcion = forms.CharField(
        label='Descripción',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Breve descripción del tipo de activo'
        })
    )

    class Meta:
        model = TipoActivo
        fields = ['nombre', 'descripcion']
