from django import forms
from django.core.exceptions import ValidationError

from agenda_telefonica.models import Anexo
from core.models.profesion import Profesion
from core.models.rol_organizacional import RolOrganizacional
from core.models.unidad_organizacional import UnidadOrganizacional


class AnexoFuncionarioForm(forms.ModelForm):
    # Campos de Funcionario
    rut = forms.CharField(max_length=12, label="Rut", required=True)
    nombres = forms.CharField(max_length=255, label="Nombres", required=True)
    apellidos = forms.CharField(max_length=255, label="Apellidos", required=True)
    email = forms.EmailField(label="Correo", required=False)

    cargo = forms.CharField(max_length=255, label="Encargado/a de:", required=True)
    rol_organizacional = forms.ModelChoiceField(queryset=RolOrganizacional.objects.filter(is_active=True),
                                                label="Puesto", required=True, empty_label="-- Seleccione un puesto --")
    profesion = forms.ModelChoiceField(queryset=Profesion.objects.filter(is_active=True), label="Profesión",
                                       required=True,
                                       empty_label="-- Seleccione una profesión --")
    unidad_organizacional = forms.ModelChoiceField(queryset=UnidadOrganizacional.objects.all(),
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

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
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
            self.fields['profesion'].initial = f.profesion
            self.fields['unidad_organizacional'].initial = f.unidad_organizacional
            self.fields['rol_organizacional'].initial = f.rol_organizacional
