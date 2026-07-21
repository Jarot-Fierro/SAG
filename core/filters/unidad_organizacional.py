from django import forms


class FiltroUnidadOrganizacionalForm(forms.Form):
    nombre = forms.CharField(
        label="Nombre",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del Departamento',
        }),
    )
    direccion = forms.CharField(
        label="Dirección",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dirección',
        }),
    )
    es_departamento = forms.ChoiceField(
        label="Es Departamento",
        required=False,
        choices=(
            ("", "Todos los Departamentos"),
            ("True", "Sí"),
            ("False", "No"),
        ),
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )
    es_subdepartamento = forms.ChoiceField(
        label="Es Subdepartamento",
        required=False,
        choices=(
            ("", "Todos los Subdepartamentos"),
            ("True", "Sí"),
            ("False", "No"),
        ),
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )
    is_active = forms.ChoiceField(
        label="Estado (Activo)",
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
