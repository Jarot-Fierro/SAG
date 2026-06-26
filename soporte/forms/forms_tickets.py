from django import forms
from django.urls import reverse_lazy

from core.models import User
from soporte.models import Ticket


class FormTicket(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields['area_soporte'].initial = 'INFORMATICA'

        # Para que ModelChoiceField acepte el valor enviado por Select2 (AJAX)
        if 'funcionario' in self.data:
            try:
                funcionario_id = self.data.get('funcionario')
                self.fields['funcionario'].queryset = User.objects.filter(id=funcionario_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.funcionario:
            self.fields['funcionario'].queryset = User.objects.filter(id=self.instance.funcionario.id)

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
        queryset=User.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control select2-ajax',
            'data-ajax-url': reverse_lazy('usuarios:buscar_funcionario_ajax')
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
