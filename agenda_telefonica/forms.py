from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.urls import reverse_lazy

from agenda_telefonica.models import Anexo
from core.models.profesion import Profesion
from core.models.rol_organizacional import RolOrganizacional
from core.models.unidad_organizacional import UnidadOrganizacional


class UnidadOrganizacionalModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        nombre_lower = obj.nombre.lower()
        if 'secretaria' in nombre_lower or 'secretaría' in nombre_lower:
            if obj.padre:
                return f"{obj.padre.nombre} / {obj.nombre}"
        return obj.nombre


class AnexoFuncionarioForm(forms.ModelForm):
    # Campos de Funcionario
    rut = forms.CharField(max_length=12, label="Rut", required=True)
    nombres = forms.CharField(max_length=255, label="Nombres", required=True)
    apellidos = forms.CharField(max_length=255, label="Apellidos", required=True)
    email = forms.EmailField(label="Correo", required=False)

    cargo = forms.CharField(max_length=255, label="Encargado/a de:", required=True)
    rol_organizacional = forms.ModelChoiceField(queryset=RolOrganizacional.objects.filter(is_active=True),
                                                label="Puesto", required=True, empty_label="-- Seleccione un puesto --")
    unidad_organizacional = UnidadOrganizacionalModelChoiceField(queryset=UnidadOrganizacional.objects.all(),
                                                                 label="Unidad Organizacional", )

    # Heredamos los campos de Anexo del ModelForm
    class Meta:
        model = Anexo
        fields = ['anexo', 'anexo_publico', 'numero_telefonico', 'establecimiento']
        # El campo 'funcionario' lo manejaremos en la vista

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if rut:
            rut = rut.upper()
            from core.models.funcionario import Funcionario
            # Verificar si ya existe un funcionario con este RUT
            funcionario = Funcionario.objects.filter(rut=rut).first()
            if funcionario:
                # Verificar si este funcionario ya tiene un anexo
                # Excluir el anexo actual si estamos editando
                anexo_query = Anexo.objects.filter(funcionario=funcionario)
                if self.instance and self.instance.pk:
                    anexo_query = anexo_query.exclude(pk=self.instance.pk)

                if anexo_query.exists():
                    raise ValidationError("Este funcionario ya tiene un anexo asignado.")
        return rut

    def clean_anexo(self):
        anexo = self.cleaned_data.get('anexo')

        if anexo:
            anexo = str(anexo)

            if not anexo.isdigit():
                raise ValidationError("El anexo solo puede contener números.")

            if len(anexo) != 6:
                raise ValidationError("El anexo debe tener exactamente 6 dígitos.")

        return anexo

    def clean(self):
        cleaned_data = super().clean()
        unidad_organizacional = cleaned_data.get('unidad_organizacional')

        if self.user and self.user.establecimiento and unidad_organizacional:
            if unidad_organizacional.establecimiento != self.user.establecimiento:
                raise ValidationError(
                    f"La unidad organizacional '{unidad_organizacional.nombre}' no corresponde a su establecimiento."
                )
        return cleaned_data

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self.user = user
        super().__init__(*args, **kwargs)
        # Añadir clases de bootstrap a todos los campos
        for field_name, field in self.fields.items():
            if field_name == 'unidad_organizacional':
                field.widget.attrs.update({'class': 'form-control form-control-sm select2'})
            else:
                field.widget.attrs.update({'class': 'form-control form-control-sm'})

        # Filtrar unidades organizacionales según el perfil del usuario
        if user and hasattr(user, 'perfilagenda'):
            perfil = user.perfilagenda
            unidades_permitidas = perfil.unidad_organizacional.all()

            if unidades_permitidas.exists():
                # Obtener todas las unidades descendientes recursivamente
                todas_permitidas_ids = set()

                def obtener_descendientes(unidad):
                    todas_permitidas_ids.add(unidad.id)
                    for hijo in unidad.hijos.all():
                        obtener_descendientes(hijo)

                for unidad in unidades_permitidas:
                    obtener_descendientes(unidad)

                self.fields['unidad_organizacional'].queryset = UnidadOrganizacional.objects.filter(
                    id__in=todas_permitidas_ids
                )

        # Si estamos editando y tiene un funcionario, cargar sus datos
        if self.instance and self.instance.funcionario:
            f = self.instance.funcionario
            self.fields['rut'].initial = f.rut
            self.fields['nombres'].initial = f.nombres
            self.fields['apellidos'].initial = f.apellidos
            self.fields['email'].initial = f.email
            self.fields['cargo'].initial = f.cargo
            self.fields['unidad_organizacional'].initial = f.unidad_organizacional
            self.fields['rol_organizacional'].initial = f.rol_organizacional


class AnexoFuncionarioCompletoForm(forms.ModelForm):
    rut = forms.CharField(
        max_length=12,
        label="Rut",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "RUT"}),
    )
    nombres = forms.CharField(
        max_length=255,
        label="Nombres",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Nombres"}),
    )
    apellidos = forms.CharField(
        max_length=255,
        label="Apellidos",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Apellidos"}),
    )
    email = forms.EmailField(
        label="Correo",
        required=False,
        widget=forms.EmailInput(attrs={"placeholder": "Correo"}),
    )
    cargo = forms.CharField(
        max_length=255,
        label="Cargo",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Cargo"}),
    )
    profesion = forms.ModelChoiceField(
        queryset=Profesion.objects.filter(is_active=True),
        label="Profesión",
        required=False,
        empty_label="-- Seleccione una profesión --",
    )
    rol_organizacional = forms.ModelChoiceField(
        queryset=RolOrganizacional.objects.filter(is_active=True),
        label="Puesto",
        required=True,
        empty_label="-- Seleccione un puesto --",
    )
    unidad_organizacional = UnidadOrganizacionalModelChoiceField(
        queryset=UnidadOrganizacional.objects.all(),
        label="Unidad Organizacional",
        required=True,
    )

    class Meta:
        model = Anexo
        fields = ["anexo", "anexo_publico", "numero_telefonico", "establecimiento"]

    def clean_rut(self):
        rut = self.cleaned_data.get("rut")
        if rut:
            rut = rut.upper()
            from core.models.funcionario import Funcionario

            funcionario = Funcionario.objects.filter(rut=rut).first()
            if funcionario:
                anexo_query = Anexo.objects.filter(funcionario=funcionario)
                if self.instance and self.instance.pk:
                    anexo_query = anexo_query.exclude(pk=self.instance.pk)

                if anexo_query.exists():
                    raise ValidationError("Este funcionario ya tiene un anexo asignado.")
        return rut

    def clean_anexo(self):
        anexo = self.cleaned_data.get("anexo")
        if anexo:
            anexo = str(anexo)
            if not anexo.isdigit():
                raise ValidationError("El anexo solo puede contener números.")
            if len(anexo) != 6:
                raise ValidationError("El anexo debe tener exactamente 6 dígitos.")
        return anexo

    def clean(self):
        cleaned_data = super().clean()
        unidad_organizacional = cleaned_data.get("unidad_organizacional")

        if self.user and self.user.establecimiento and unidad_organizacional:
            if unidad_organizacional.establecimiento != self.user.establecimiento:
                raise ValidationError(
                    f"La unidad organizacional '{unidad_organizacional.nombre}' no corresponde a su establecimiento."
                )
        return cleaned_data

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        self.user = user
        super().__init__(*args, **kwargs)

        self.fields["anexo"].widget.attrs.update({"placeholder": "Anexo"})
        self.fields["anexo_publico"].widget.attrs.update({"placeholder": "Anexo público"})
        self.fields["numero_telefonico"].widget.attrs.update({"placeholder": "Teléfono"})

        for field_name, field in self.fields.items():
            if field_name == "unidad_organizacional":
                field.widget.attrs.update({"class": "form-control form-control-sm select2"})
            else:
                field.widget.attrs.update({"class": "form-control form-control-sm"})

        if user and hasattr(user, "perfilagenda"):
            perfil = user.perfilagenda
            unidades_permitidas = perfil.unidad_organizacional.all()
            if unidades_permitidas.exists():
                todas_permitidas_ids = set()

                def obtener_descendientes(unidad):
                    todas_permitidas_ids.add(unidad.id)
                    for hijo in unidad.hijos.all():
                        obtener_descendientes(hijo)

                for unidad in unidades_permitidas:
                    obtener_descendientes(unidad)

                self.fields["unidad_organizacional"].queryset = UnidadOrganizacional.objects.filter(
                    id__in=todas_permitidas_ids
                )

        if self.instance and self.instance.funcionario:
            funcionario = self.instance.funcionario
            self.fields["rut"].initial = funcionario.rut
            self.fields["nombres"].initial = funcionario.nombres
            self.fields["apellidos"].initial = funcionario.apellidos
            self.fields["email"].initial = funcionario.email
            self.fields["cargo"].initial = funcionario.cargo
            self.fields["profesion"].initial = funcionario.profesion
            self.fields["unidad_organizacional"].initial = funcionario.unidad_organizacional
            self.fields["rol_organizacional"].initial = funcionario.rol_organizacional


class AnexoSinFuncionarioForm(forms.ModelForm):
    unidad_organizacional = UnidadOrganizacionalModelChoiceField(
        queryset=UnidadOrganizacional.objects.all(),
        label="Unidad Organizacional",
    )

    class Meta:
        model = Anexo
        fields = [
            'anexo', 'anexo_publico', 'numero_telefonico',
            'nombre_anexo', 'email', 'rol_organizacional', 'encargado_de',
            'unidad_organizacional', 'establecimiento'
        ]

    def clean_anexo(self):
        anexo = self.cleaned_data.get('anexo')
        if anexo:
            anexo = str(anexo)
            if not anexo.isdigit():
                raise ValidationError("El anexo solo puede contener números.")
            if len(anexo) != 6:
                raise ValidationError("El anexo debe tener exactamente 6 dígitos.")
        return anexo

    def clean(self):
        cleaned_data = super().clean()
        unidad_organizacional = cleaned_data.get('unidad_organizacional')

        if self.user and self.user.establecimiento and unidad_organizacional:
            if unidad_organizacional.establecimiento != self.user.establecimiento:
                raise ValidationError(
                    f"La unidad organizacional '{unidad_organizacional.nombre}' no corresponde a su establecimiento."
                )
        return cleaned_data

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self.user = user
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'unidad_organizacional':
                field.widget.attrs.update({'class': 'form-control form-control-sm select2'})
            else:
                field.widget.attrs.update({'class': 'form-control form-control-sm'})

        if user and hasattr(user, 'perfilagenda'):
            perfil = user.perfilagenda
            unidades_permitidas = perfil.unidad_organizacional.all()
            if unidades_permitidas.exists():
                todas_permitidas_ids = set()

                def obtener_descendientes(unidad):
                    todas_permitidas_ids.add(unidad.id)
                    for hijo in unidad.hijos.all():
                        obtener_descendientes(hijo)

                for unidad in unidades_permitidas:
                    obtener_descendientes(unidad)

                self.fields['unidad_organizacional'].queryset = UnidadOrganizacional.objects.filter(
                    id__in=todas_permitidas_ids
                )


class AnexoFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Búsqueda',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar por nombre, anexo o correo...',
            'hx-get': reverse_lazy('agenda:buscar_anexo'),
            'hx-target': '#table-results-public',
            'hx-trigger': 'keyup changed delay:500ms, search',
        })
    )

    per_page = forms.ChoiceField(
        choices=[(10, '10'), (20, '20'), (50, '50'), (100, '100')],
        initial=10,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
            'hx-get': reverse_lazy('agenda:buscar_anexo'),
            'hx-target': '#table-results-public',
            'hx-trigger': 'change',
            'name': 'per_page',
        })
    )

    unidad_organizacional = UnidadOrganizacionalModelChoiceField(
        queryset=UnidadOrganizacional.objects.none(),
        required=False,
        label='Unidad Organizacional',
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm select2',
            'hx-get': reverse_lazy('agenda:buscar_anexo'),
            'hx-target': '#table-results-public',
            'hx-trigger': 'change',
        })
    )

    def __init__(self, *args, **kwargs):
        establecimiento = kwargs.pop('establecimiento', None)
        super().__init__(*args, **kwargs)

        q_unidades = Q(nombre__icontains='SUBDIRECCION') | \
                     Q(nombre__icontains='SUBDIRECCIÓN') | \
                     Q(nombre__icontains='DEPARTAMENTO') | \
                     Q(nombre__icontains='SUBDEPTO') | \
                     Q(nombre__icontains='SECRETARIA') | \
                     Q(nombre__icontains='SECRETARÍA')
        # Q(nombre__icontains='Secretaría')
        queryset = UnidadOrganizacional.objects.filter(q_unidades, is_active=True)

        if establecimiento:
            queryset = queryset.filter(establecimiento_id=establecimiento)

        self.fields['unidad_organizacional'].queryset = queryset
        self.fields['unidad_organizacional'].empty_label = "-- Todas las unidades --"
