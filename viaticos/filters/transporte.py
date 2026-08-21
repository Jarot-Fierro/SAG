from django import forms

from ..models.transporte import GastoTransporte


class FiltroGastoTransporte(forms.Form):
    tipo_gasto = forms.ChoiceField(
        choices=[('', 'Todos los Tipos de Transporte')] + GastoTransporte.TIPO_GASTO_CHOICES,
        label='Tipo Gasto',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )

    origen = forms.CharField(
        label='Origen',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Origen'
        }),
        required=False
    )

    destino = forms.CharField(
        label='Destino',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Destino'
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
