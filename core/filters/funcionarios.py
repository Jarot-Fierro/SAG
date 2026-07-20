from django import forms

from core.models.rol_organizacional import RolOrganizacional
from core.models.unidad_organizacional import UnidadOrganizacional


class FuncionarioFilter(forms.Form):
    rut = forms.CharField(
        label="RUT",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Buscar por RUT",
            }
        ),
    )

    nombres = forms.CharField(
        label="Nombres",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nombres",
            }
        ),
    )

    apellidos = forms.CharField(
        label="Apellidos",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Apellidos",
            }
        ),
    )

    email = forms.CharField(
        label="Correo",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Correo",
            }
        ),
    )

    rol_organizacional = forms.ModelChoiceField(
        label="Rol Organizacional",
        required=False,
        queryset=RolOrganizacional.objects.all(),
        empty_label="Todos los Cargos",
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    unidad_organizacional = forms.ModelChoiceField(
        label="Unidad organizacional",
        required=False,
        queryset=UnidadOrganizacional.objects.all(),
        empty_label="Todas las Unidades",
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    is_active = forms.ChoiceField(
        label="Estado",
        required=False,
        choices=(
            ("", "Todos los estados"),
            ("True", "Activo"),
            ("False", "Inactivo"),
        ),
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )
