from django import forms

from core.models import Funcionario
from soporte.models import Ticket


class FormTicket(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and getattr(user, 'usuario_soporte', False):
            self.fields['funcionario'].queryset = Funcionario.objects.filter(departamento=user.departamento)

    titulo = forms.CharField(
        label='Título del problema',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Problema con impresora'
        }),
        required=True
    )

    descripcion = forms.CharField(
        label='Descripción del problema',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describa el problema que está presentando'
        }),
        required=False
    )

    area_soporte = forms.ChoiceField(
        label='Área de soporte',
        choices=[('MANTENCION', 'Mantencion'), ('INFORMATICA', 'Informatica')],
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=True
    )

    funcionario = forms.ModelChoiceField(
        label='Funcionario solicitante',
        queryset=Funcionario.objects.filter(),
        widget=forms.Select(attrs={
            'class': 'form-control select2'
        }),
        required=True
    )

    class Meta:
        model = Ticket
        fields = [
            'titulo',
            'funcionario',
            'area_soporte',
            'descripcion',
        ]
