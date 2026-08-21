from django import forms
from django.urls import reverse

from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional
from ..models.catalogos import LugarDestino, EscalaViatico
from ..models.solicitud import SolicitudCometidoViatico, ItinerarioDestino, CalculoViatico


class SolicitudCometidoViaticoForm(forms.ModelForm):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)

        if request:
            establecimiento = getattr(request.user, 'establecimiento', None)
            if establecimiento:
                self.fields['funcionario'].queryset = Funcionario.objects.filter(establecimiento=establecimiento)
                self.fields['unidad_organizacional'].queryset = UnidadOrganizacional.objects.filter(
                    establecimiento=establecimiento)

            if not self.instance.pk and hasattr(request.user, 'funcionario') and request.user.funcionario:
                self.initial['funcionario'] = request.user.funcionario
                if request.user.funcionario.unidad_organizacional:
                    self.initial['unidad_organizacional'] = request.user.funcionario.unidad_organizacional
                if request.user.funcionario.cargo:
                    self.initial['cargo_desempenado'] = request.user.funcionario.cargo

            self.fields['funcionario'].widget.attrs.update({
                'hx-get': reverse('funcionarios:consumo_api')
            })

    tipo_solicitud = forms.ChoiceField(
        choices=SolicitudCometidoViatico.TIPO_SOLICITUD_CHOICES,
        label='Tipo de Solicitud',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    funcionario = forms.CharField(
        label='Funcionario Solicitante',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'hx-trigger': 'blur',
                'hx-target': '#contenedor-unidad-organizacional',
                'hx-swap': 'outerHTML',
            }
        ),
        required=True
    )

    unidad_organizacional = forms.CharField(
        label='Unidad / Departamento',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'readonly': True,
            }
        ),
        required=False
    )

    cargo_desempenado = forms.CharField(
        label='Cargo Desempeñado',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Fiscalizador Sanitario'
        }),
        required=False
    )

    grado_funcionario = forms.CharField(
        label='Grado Funcionario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 10'
        }),
        required=False
    )

    motivo_viaje = forms.CharField(
        label='Motivo / Justificación del Cometido',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describa detalladamente el motivo institucional del cometido o comisión de servicio'
        }),
        required=True
    )

    fecha_inicio = forms.DateField(
        label='Fecha Inicio',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )

    fecha_termino = forms.DateField(
        label='Fecha Término',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )

    hora_salida = forms.TimeField(
        label='Hora Salida',
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        required=True
    )

    hora_llegada = forms.TimeField(
        label='Hora Estimada Llegada',
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        required=True
    )

    total_dias = forms.IntegerField(
        label='Total Días Comisión',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1',
            'min': '1'
        }),
        initial=1,
        required=True
    )

    es_proyecto = forms.BooleanField(
        label='¿Financiado con fondos de Proyecto?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    nombre_codigo_proyecto = forms.CharField(
        label='Nombre o Código del Proyecto',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Proyecto Control Mosca de la Fruta'
        }),
        required=False
    )

    es_urgente = forms.BooleanField(
        label='¿Carácter Urgente / Prioritario?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    tiene_derecho_pasaje = forms.BooleanField(
        label='¿Tiene derecho a pasajes / traslados?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    requiere_vehiculo_institucional = forms.BooleanField(
        label='¿Requiere asignación de Vehículo Institucional?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    requiere_vales_bencina = forms.BooleanField(
        label='¿Requiere Vales de Combustible?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    class Meta:
        model = SolicitudCometidoViatico
        fields = [
            'tipo_solicitud',
            'funcionario',
            'unidad_organizacional',
            'cargo_desempenado',
            'grado_funcionario',
            'motivo_viaje',
            'fecha_inicio',
            'fecha_termino',
            'hora_salida',
            'hora_llegada',
            'total_dias',
            'es_proyecto',
            'nombre_codigo_proyecto',
            'es_urgente',
            'tiene_derecho_pasaje',
            'requiere_vehiculo_institucional',
            'requiere_vales_bencina',
        ]


class ItinerarioDestinoForm(forms.ModelForm):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request:
            establecimiento = getattr(request.user, 'establecimiento', None)
            if establecimiento:
                self.fields['lugar_destino'].queryset = LugarDestino.objects.filter(establecimiento=establecimiento)

    orden_visita = forms.IntegerField(
        label='Orden de Parada / Secuencia',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1',
            'min': '1'
        }),
        initial=1,
        required=True
    )

    lugar_destino = forms.ModelChoiceField(
        queryset=LugarDestino.objects.all(),
        label='Lugar de Destino',
        empty_label='Seleccione un destino',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    descripcion_actividad_lugar = forms.CharField(
        label='Actividad Específica en este Destino',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Inspección fitosanitaria predial en Fundo Elqui'
        }),
        required=True
    )

    fecha_llegada = forms.DateField(
        label='Fecha Llegada al Destino',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )

    fecha_salida = forms.DateField(
        label='Fecha Salida del Destino',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )

    medio_transporte_tramo = forms.ChoiceField(
        choices=[
            ('VEHICULO_INSTITUCIONAL', 'Vehículo Institucional'),
            ('BUS_INTERURBANO', 'Bus Interurbano'),
            ('AVION', 'Avión'),
            ('VEHICULO_PARTICULAR', 'Vehículo Particular'),
            ('OTRO', 'Otro Transporte'),
        ],
        label='Medio de Transporte en Tramo',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        initial='VEHICULO_INSTITUCIONAL',
        required=True
    )

    pernocta_en_lugar = forms.BooleanField(
        label='¿Pernocta en este lugar (100% Viático)?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    aplica_alimentacion_50 = forms.BooleanField(
        label='¿Aplica 50% Viático (Alimentación)?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    aplica_faena = forms.BooleanField(
        label='¿Aplica Tarifa de Faena?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    class Meta:
        model = ItinerarioDestino
        fields = [
            'orden_visita',
            'lugar_destino',
            'descripcion_actividad_lugar',
            'fecha_llegada',
            'fecha_salida',
            'medio_transporte_tramo',
            'pernocta_en_lugar',
            'aplica_alimentacion_50',
            'aplica_faena',
        ]


class CalculoViaticoForm(forms.ModelForm):
    escala_aplicada = forms.ModelChoiceField(
        queryset=EscalaViatico.objects.all(),
        label='Escala Tarifaria Aplicada',
        empty_label='Seleccione escala tarifaria',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    dias_100 = forms.IntegerField(
        label='Cantidad Días 100% (Pernocta)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'min': '0'
        }),
        initial=0,
        required=False
    )

    monto_unitario_100 = forms.DecimalField(
        label='Monto Unitario 100% ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=False
    )

    total_monto_100 = forms.DecimalField(
        label='Subtotal 100% ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=False
    )

    dias_50 = forms.IntegerField(
        label='Cantidad Días 50% (Alimentación)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'min': '0'
        }),
        initial=0,
        required=False
    )

    monto_unitario_50 = forms.DecimalField(
        label='Monto Unitario 50% ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=False
    )

    total_monto_50 = forms.DecimalField(
        label='Subtotal 50% ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=False
    )

    dias_faena = forms.IntegerField(
        label='Cantidad Días Faena',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'min': '0'
        }),
        initial=0,
        required=False
    )

    monto_unitario_faena = forms.DecimalField(
        label='Monto Unitario Faena ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=False
    )

    total_monto_faena = forms.DecimalField(
        label='Subtotal Faena ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=False
    )

    total_bruto_viatico = forms.DecimalField(
        label='Total Viático Calculado ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control fw-bold',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=True
    )

    monto_anticipo_entregado = forms.DecimalField(
        label='Monto Anticipo Entregado ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=False
    )

    saldo_a_pagar = forms.DecimalField(
        label='Saldo Final a Pagar ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control fw-bold',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=True
    )

    class Meta:
        model = CalculoViatico
        fields = [
            'escala_aplicada',
            'dias_100',
            'monto_unitario_100',
            'total_monto_100',
            'dias_50',
            'monto_unitario_50',
            'total_monto_50',
            'dias_faena',
            'monto_unitario_faena',
            'total_monto_faena',
            'total_bruto_viatico',
            'monto_anticipo_entregado',
            'saldo_a_pagar',
        ]
