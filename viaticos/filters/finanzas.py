from django import forms

from ..models.finanzas import EgresoPagoViatico


class FiltroEgresoPagoViatico(forms.Form):
    numero_egreso = forms.IntegerField(
        label='N° Egreso',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'N° Egreso'
        }),
        required=False
    )

    ano_egreso = forms.IntegerField(
        label='Año',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Año'
        }),
        required=False
    )

    medio_pago = forms.ChoiceField(
        choices=[('', 'Todos los Medios de Pago')] + EgresoPagoViatico.MEDIO_PAGO_CHOICES,
        label='Medio de Pago',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )

    beneficiario = forms.CharField(
        label='Beneficiario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre o RUT'
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


class FiltroRendicionCometido(forms.Form):
    folio_solicitud = forms.IntegerField(
        label='N° Folio Solicitud',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Folio'
        }),
        required=False
    )

    rendicion_aprobada = forms.ChoiceField(
        choices=[('', 'Estado Aprobación (Todos)'), ('1', 'Solo Aprobadas'), ('0', 'Pendientes de Aprobación')],
        label='Estado Rendición',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
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
