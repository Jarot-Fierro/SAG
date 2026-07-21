from django import forms

from core.models.unidad_organizacional import UnidadOrganizacional


class UnidadOrganizacionalForm(forms.ModelForm):
    class Meta:
        model = UnidadOrganizacional
        fields = [
            'establecimiento',
            'nombre',
            'padre',
            'direccion',
            'es_departamento',
            'es_subdepartamento',
            'is_active'
        ]
        widgets = {
            'establecimiento': forms.Select(attrs={'class': 'form-control select2'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la unidad'}),
            'padre': forms.Select(attrs={'class': 'form-control select2'}),
            'direccion': forms.Select(attrs={'class': 'form-control select2'}),
            'es_departamento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'es_subdepartamento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.Select(attrs={'class': 'form-control'}),
        }
