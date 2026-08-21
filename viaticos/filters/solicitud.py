from django import forms

from core.models.funcionario import Funcionario
from ..models.catalogos import LugarDestino
from ..models.solicitud import SolicitudCometidoViatico


class FiltroSolicitud(forms.Form):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request:
            establecimiento = getattr(request.user, 'establecimiento', None)
            if establecimiento:
                self.fields['funcionario'].queryset = Funcionario.objects.filter(establecimiento=establecimiento)

    folio = forms.IntegerField(
        label='N° Folio',
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
        empty_label='Todos los funcionarios',
        label='Funcionario',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )

    tipo_solicitud = forms.ChoiceField(
        choices=[('', 'Todos los Tipos')] + SolicitudCometidoViatico.TIPO_SOLICITUD_CHOICES,
        label='Tipo',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )

    estado = forms.ChoiceField(
        choices=[('', 'Todos los Estados')] + SolicitudCometidoViatico.ESTADO_CHOICES,
        label='Estado',
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

    es_urgente = forms.ChoiceField(
        choices=[('', 'Urgencia (Todos)'), ('1', 'Solo Urgentes'), ('0', 'No Urgentes')],
        label='Urgencia',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )


class FiltroMisSolicitudes(forms.Form):
    folio = forms.IntegerField(
        label='N° Folio',
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

    estado = forms.ChoiceField(
        choices=[('', 'Todos los Estados')] + SolicitudCometidoViatico.ESTADO_CHOICES,
        label='Estado',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )

    tipo_solicitud = forms.ChoiceField(
        choices=[('', 'Todos los Tipos')] + SolicitudCometidoViatico.TIPO_SOLICITUD_CHOICES,
        label='Tipo',
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


class FiltroItinerario(forms.Form):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request:
            establecimiento = getattr(request.user, 'establecimiento', None)
            if establecimiento:
                self.fields['lugar_destino'].queryset = LugarDestino.objects.filter(establecimiento=establecimiento)

    lugar_destino = forms.ModelChoiceField(
        queryset=LugarDestino.objects.all(),
        empty_label='Todos los destinos',
        label='Destino',
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
