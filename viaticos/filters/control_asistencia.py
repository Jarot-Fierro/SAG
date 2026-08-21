from django import forms

from core.models.funcionario import Funcionario


class FiltroValidacionRelojControl(forms.Form):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request:
            establecimiento = getattr(request.user, 'establecimiento', None)
            if establecimiento:
                self.fields['funcionario'].queryset = Funcionario.objects.filter(establecimiento=establecimiento)

    funcionario = forms.ModelChoiceField(
        queryset=Funcionario.objects.all(),
        empty_label='Todos los funcionarios',
        label='Funcionario',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )

    sincronizado_reloj = forms.ChoiceField(
        choices=[('', 'Todos'), ('1', 'Sincronizados'), ('0', 'Pendientes de Sincronización')],
        label='Sincronización Reloj',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )

    tipo_ausentismo = forms.CharField(
        label='Tipo Ausentismo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tipo ausentismo'
        }),
        required=False
    )

    fecha_desde = forms.DateField(
        label='Desde',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )

    fecha_hasta = forms.DateField(
        label='Hasta',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )


class FiltroPermisoGremial(forms.Form):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request:
            establecimiento = getattr(request.user, 'establecimiento', None)
            if establecimiento:
                self.fields['funcionario'].queryset = Funcionario.objects.filter(establecimiento=establecimiento)

    folio_gremial = forms.IntegerField(
        label='N° Folio Gremial',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Folio'
        }),
        required=False
    )

    ano = forms.IntegerField(
        label='Año',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Año'
        }),
        required=False
    )

    funcionario = forms.ModelChoiceField(
        queryset=Funcionario.objects.all(),
        empty_label='Todos los dirigentes/funcionarios',
        label='Dirigente / Funcionario',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )

    aprobado = forms.ChoiceField(
        choices=[('', 'Todos'), ('1', 'Aprobados'), ('0', 'Pendientes')],
        label='Estado Aprobación',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )
