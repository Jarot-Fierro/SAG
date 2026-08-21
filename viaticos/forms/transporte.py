from django import forms

from ..models.solicitud import SolicitudCometidoViatico
from ..models.transporte import GastoTransporte


class GastoTransporteForm(forms.ModelForm):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request:
            establecimiento = getattr(request.user, 'establecimiento', None)
            if establecimiento:
                self.fields['solicitud'].queryset = SolicitudCometidoViatico.objects.filter(
                    establecimiento=establecimiento)

    solicitud = forms.ModelChoiceField(
        queryset=SolicitudCometidoViatico.objects.all(),
        label='Solicitud de Cometido / Viático',
        empty_label='Seleccione la solicitud asociada',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    tipo_gasto = forms.ChoiceField(
        choices=GastoTransporte.TIPO_GASTO_CHOICES,
        label='Tipo de Gasto / Pasaje',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    origen = forms.CharField(
        label='Ciudad / Localidad de Origen',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: La Serena'
        }),
        required=True
    )

    destino = forms.CharField(
        label='Ciudad / Localidad de Destino',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Santiago'
        }),
        required=True
    )

    fecha_ida = forms.DateField(
        label='Fecha Ida',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )

    fecha_regreso = forms.DateField(
        label='Fecha Regreso',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )

    aerolinea = forms.CharField(
        label='Línea Aérea',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: LATAM Airlines / SKY Airline'
        }),
        required=False
    )

    codigo_reserva_pnr = forms.CharField(
        label='Código de Reserva / PNR',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: QWERTY'
        }),
        required=False
    )

    numero_billete = forms.CharField(
        label='N° Billete / Ticket Aéreo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 045-1234567890'
        }),
        required=False
    )

    numero_vale_bencina = forms.CharField(
        label='N° de Vale(s) Combustible',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: V-4501, V-4502'
        }),
        required=False
    )

    tipo_combustible = forms.CharField(
        label='Tipo de Combustible',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Gasolina 95 / Diesel'
        }),
        required=False
    )

    kilometros_recorridos = forms.IntegerField(
        label='Kilómetros Estimados / Recorridos',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        }),
        initial=0,
        required=False
    )

    precio_por_litro = forms.DecimalField(
        label='Precio por Litro ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=False
    )

    monto_cotizado = forms.DecimalField(
        label='Monto Cotizado / Autorizado ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=False
    )

    monto_real_ejecutado = forms.DecimalField(
        label='Monto Real Ejecutado ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=False
    )

    pagado_directo_proveedor = forms.BooleanField(
        label='¿Pagado por Orden de Compra Institucional?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    class Meta:
        model = GastoTransporte
        fields = [
            'solicitud',
            'tipo_gasto',
            'origen',
            'destino',
            'fecha_ida',
            'fecha_regreso',
            'aerolinea',
            'codigo_reserva_pnr',
            'numero_billete',
            'numero_vale_bencina',
            'tipo_combustible',
            'kilometros_recorridos',
            'precio_por_litro',
            'monto_cotizado',
            'monto_real_ejecutado',
            'pagado_directo_proveedor',
        ]
