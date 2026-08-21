from django import forms

from ..models.wokflow import AprobacionCometido


class FiltroAprobacionCometido(forms.Form):
    etapa = forms.ChoiceField(
        choices=[('', 'Todas las Etapas')] + AprobacionCometido.ETAPA_CHOICES,
        label='Etapa',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )

    accion = forms.ChoiceField(
        choices=[('', 'Todas las Acciones')] + AprobacionCometido.ESTADO_ACCION_CHOICES,
        label='Acción',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )

    firmante = forms.CharField(
        label='Firmante',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre o usuario'
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


class FiltroBandejaFirmas(forms.Form):
    etapa = forms.ChoiceField(
        choices=[
            ('', 'Todas las Etapas Pendientes'),
            ('JEFE_DIRECTO', 'Jefatura Directa (ENVIADO_JEFATURA)'),
            ('SERVICIOS_GENERALES', 'Servicios Generales (EN_REVISION_SSGG)'),
            ('RRHH_CONTROL', 'Personal / RRHH (EN_REVISION_RRHH)'),
            ('EN_PAGO', 'Finanzas / Pago (EN_PAGO)'),
        ],
        label='Etapa Pendiente',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )

    folio = forms.IntegerField(
        label='N° Folio',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Folio'
        }),
        required=False
    )

    funcionario = forms.CharField(
        label='Funcionario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre funcionario'
        }),
        required=False
    )

    es_urgente = forms.ChoiceField(
        choices=[('', 'Todos'), ('1', 'Solo Urgentes'), ('0', 'No Urgentes')],
        label='Urgencia',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )
