from django import forms

from agenda_telefonica.models import Anexo
from core.models.cargo import Cargo
from core.models.profesion import Profesion


class AnexoFuncionarioForm(forms.ModelForm):
    # Campos de Funcionario
    rut = forms.CharField(max_length=12, label="Rut", required=True)
    nombres = forms.CharField(max_length=255, label="Nombres", required=True)
    apellidos = forms.CharField(max_length=255, label="Apellidos", required=True)
    email = forms.EmailField(label="Correo", required=False)

    cargo = forms.ModelChoiceField(queryset=Cargo.objects.filter(is_active=True), label="Cargo", required=True)
    profesion = forms.ModelChoiceField(queryset=Profesion.objects.filter(is_active=True), label="Profesión",
                                       required=True)

    # Heredamos los campos de Anexo del ModelForm
    class Meta:
        model = Anexo
        fields = ['anexo', 'anexo_publico', 'numero_telefonico', 'establecimiento']
        # El campo 'funcionario' lo manejaremos en la vista

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Añadir clases de bootstrap a todos los campos
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control form-control-sm'})

        # Si estamos editando y tiene un funcionario, cargar sus datos
        if self.instance and self.instance.funcionario:
            f = self.instance.funcionario
            self.fields['rut'].initial = f.rut
            self.fields['nombres'].initial = f.nombres
            self.fields['apellidos'].initial = f.apellidos
            self.fields['email'].initial = f.email
            self.fields['cargo'].initial = f.cargo
            self.fields['profesion'].initial = f.profesion
