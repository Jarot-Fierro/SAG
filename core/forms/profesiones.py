from django import forms

from ..models.profesion import Profesion


class ProfesionForm(forms.ModelForm):
    class Meta:
        model = Profesion
        fields = ['nombre', 'is_active']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la profesión'}),
            'is_active': forms.Select(attrs={'class': 'form-control'}, choices=Profesion.STATUS_CHOICES),
        }
