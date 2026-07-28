from django import forms

from ..models.establecimientos import Establecimiento


class EstablecimientoForm(forms.ModelForm):
    class Meta:
        model = Establecimiento
        fields = ['nombre', 'alias', 'region', 'direccion', 'telefono', 'is_active']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del establecimiento'}),
            'alias': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alias (ej: HDS)'}),
            'region': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Región'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Dirección', 'rows': 2}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'is_active': forms.Select(attrs={'class': 'form-control'}, choices=Establecimiento.STATUS_CHOICES),
        }
