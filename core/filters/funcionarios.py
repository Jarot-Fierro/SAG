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
                "class": "form-control select2",
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

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        self.user = user
        super().__init__(*args, **kwargs)

        # Configurar clases CSS y solo mostrar el nombre en unidad_organizacional
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control form-control-sm"})
            if field_name == "unidad_organizacional":
                field.widget.attrs["class"] += " select2"
                field.label_from_instance = lambda obj: obj.nombre

        if user:
            qs = UnidadOrganizacional.objects.all()

            # Filtrar por el establecimiento del usuario
            if user.establecimiento:
                qs = qs.filter(establecimiento=user.establecimiento)

            # Filtrar por unidades permitidas y sus descendientes (lógica conservada)
            if hasattr(user, "perfilagenda"):
                unidades_permitidas = user.perfilagenda.unidad_organizacional.all()
                if unidades_permitidas.exists():
                    todas_permitidas_ids = set()

                    def obtener_descendientes(unidad):
                        todas_permitidas_ids.add(unidad.id)
                        for hijo in unidad.hijos.all():
                            obtener_descendientes(hijo)

                    for unidad in unidades_permitidas:
                        obtener_descendientes(unidad)

                    qs = qs.filter(id__in=todas_permitidas_ids)

            self.fields["unidad_organizacional"].queryset = qs
