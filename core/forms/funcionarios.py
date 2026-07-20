from django import forms

from core.models.funcionario import Funcionario
from core.models.rol_organizacional import RolOrganizacional
from core.models.unidad_organizacional import UnidadOrganizacional


class FuncionarioForm(forms.ModelForm):
    rut = forms.CharField(
        label="RUT",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "RUT",
            }
        ),
    )

    nombres = forms.CharField(
        label="Nombres",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Nombres",
            }
        ),
    )

    apellidos = forms.CharField(
        label="Apellidos",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Apellidos",
            }
        ),
    )

    email = forms.CharField(
        label="Correo",
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Correo",
            }
        ),
    )

    rol_organizacional = forms.ModelChoiceField(
        label="Rol Organizacional",
        required=True,
        queryset=RolOrganizacional.objects.all(),
        empty_label="Seleccione Cargo",
        widget=forms.Select(
            attrs={
                "class": "form-control form-control-sm",
            }
        ),
    )

    unidad_organizacional = forms.ModelChoiceField(
        label="Unidad organizacional",
        required=True,
        queryset=UnidadOrganizacional.objects.all(),
        empty_label="Seleccione Unidad",
        widget=forms.Select(
            attrs={
                "class": "form-control form-control-sm",
            }
        ),
    )

    is_active = forms.ChoiceField(
        label="Estado",
        required=True,
        choices=(
            ("True", "Activo"),
            ("False", "Inactivo"),
        ),
        widget=forms.Select(
            attrs={
                "class": "form-control form-control-sm",
            }
        ),
    )

    class Meta:
        model = Funcionario
        fields = [
            "rut",
            "nombres",
            "apellidos",
            "email",
            "rol_organizacional",
            "unidad_organizacional",
            "is_active",
        ]

    def clean_is_active(self):
        value = self.cleaned_data.get("is_active")
        if value in (True, False):
            return value
        if value in ("True", "False"):
            return value == "True"
        if self.instance.pk:
            return self.instance.is_active
        return True
