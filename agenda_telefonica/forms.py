from django import forms

from agenda_telefonica.models import Anexo
from core.models.rol_organizacional import RolOrganizacional
from core.models.unidad_organizacional import UnidadOrganizacional


class FormAnexos(forms.ModelForm):
    anexo = forms.CharField(
        required=True,
        label='Anexo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el número de anexo'
        })
    )
    anexo_publico = forms.CharField(
        required=False,
        label='Anexo Público',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el número de anexo público'
        })
    )
    numero_telefonico = forms.CharField(
        required=False,
        label='Número Telefónico Institucional',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el número de teléfono institucional'
        })
    )
    nombre_anexo = forms.CharField(
        required=True,
        label='Nombre del Anexo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el nombre del anexo'
        })
    )
    email = forms.EmailField(
        required=False,
        label='Correo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el correo electrónico'
        })
    )
    rol_organizacional = forms.ModelChoiceField(
        required=True,
        label='Rol',
        empty_label='Selecciona un rol',
        queryset=RolOrganizacional.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        })
    )
    encargado_de = forms.CharField(
        required=True,
        label='Encargado de',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la funcion o el cargo que desempeña'
        })
    )
    unidad_organizacional = forms.ModelChoiceField(
        required=True,
        label='Departamento / Servicio',
        empty_label='Selecciona un departamento',
        queryset=UnidadOrganizacional.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control form-select tom-select'
        })
    )

    class Meta:
        model = Anexo
        fields = [
            'anexo',
            'anexo_publico',
            'numero_telefonico',
            'nombre_anexo',
            'email',
            'rol_organizacional',
            'encargado_de',
            'unidad_organizacional',
        ]
