from django import forms

from core.models.rol_organizacional import RolOrganizacional
from core.models.unidad_organizacional import UnidadOrganizacional


class AnexoFilter(forms.Form):
    # ===== Campos de Anexo =====

    anexo = forms.CharField(
        label="Anexo",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Anexo"
        })
    )

    anexo_publico = forms.CharField(
        label="Anexo público",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Anexo público",
        })
    )

    numero_telefonico = forms.CharField(
        label="Teléfono",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Teléfono",
        })
    )

    # ===== Campos de Funcionario =====

    nombre = forms.CharField(
        label="Nombre",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Nombre",
        })
    )

    email = forms.CharField(
        label="Correo",
        required=False,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Correo",
        })
    )

    cargo = forms.CharField(
        label="Cargo",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Cargo",
        })
    )

    rol_organizacional = forms.ModelChoiceField(
        queryset=RolOrganizacional.objects.all(),
        required=False,
        empty_label="Todos los Puestos",
        widget=forms.Select(attrs={
            "class": "form-control",
            "data-placeholder": "Rol organizacional"
        })
    )

    unidad_organizacional = forms.ModelChoiceField(
        queryset=UnidadOrganizacional.objects.all(),
        required=False,
        empty_label="Todas las Unidades",
        widget=forms.Select(attrs={
            "class": "form-control",
            "data-placeholder": "Unidad organizacional"
        })
    )

    is_active = forms.ChoiceField(
        required=False,
        choices=(
            ("", "Todos los estados"),
            ("True", "Activo"),
            ("False", "Inactivo"),
        ),
        widget=forms.Select(attrs={
            "class": "form-control",
            "data-placeholder": "Estado"
        })
    )
