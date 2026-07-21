from django import forms

from core.models.direccion import Direccion


class DireccionForm(forms.ModelForm):
    class Meta:
        model = Direccion
        fields = ['nombre', 'enlace_google_maps', 'is_active']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la dirección'}),
            'enlace_google_maps': forms.URLInput(
                attrs={'class': 'form-control', 'placeholder': 'https://maps.google.com/...'}),
            'is_active': forms.Select(attrs={'class': 'form-control'}),
        }
