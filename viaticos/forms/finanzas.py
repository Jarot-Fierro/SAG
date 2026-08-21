from django import forms

from ..models.finanzas import EgresoPagoViatico, RendicionCometido, DetalleRendicionGasto
from ..models.solicitud import SolicitudCometidoViatico


class EgresoPagoViaticoForm(forms.ModelForm):
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
        empty_label='Seleccione la solicitud a pagar',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    numero_egreso = forms.IntegerField(
        label='N° Egreso Presupuestario',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 5410'
        }),
        required=True
    )

    ano_egreso = forms.IntegerField(
        label='Año Presupuestario Egreso',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2026'
        }),
        initial=2026,
        required=True
    )

    medio_pago = forms.ChoiceField(
        choices=EgresoPagoViatico.MEDIO_PAGO_CHOICES,
        label='Medio de Pago',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        initial='TRANSFERENCIA',
        required=True
    )

    monto_total_pagado = forms.DecimalField(
        label='Monto Total Pagado ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control fw-bold',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        required=True
    )

    id_transferencia_bancaria = forms.CharField(
        label='ID / N° Transferencia Bancaria',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: TR-9988231'
        }),
        required=False
    )

    numero_cheque = forms.CharField(
        label='N° de Cheque Nominativo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: CH-002341'
        }),
        required=False
    )

    banco_origen = forms.CharField(
        label='Banco Origen Institucional',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Banco Estado'
        }),
        required=False
    )

    cuenta_origen = forms.CharField(
        label='N° Cuenta Corriente Origen',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 12345678'
        }),
        required=False
    )

    rut_beneficiario = forms.CharField(
        label='RUT Beneficiario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 12.345.678-9'
        }),
        required=True
    )

    nombre_beneficiario = forms.CharField(
        label='Nombre Completo Beneficiario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Juan Pérez Morales'
        }),
        required=True
    )

    cuenta_destino = forms.CharField(
        label='Cuenta Bancaria Destino (Banco / Tipo / N°)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Banco Estado - Cta RUT - 12345678'
        }),
        required=False
    )

    fecha_pago = forms.DateField(
        label='Fecha de Pago Efectiva',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )

    glosa_contable = forms.CharField(
        label='Glosa Contable / Detalle del Egreso',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Pago de viático por cometido funcional a...'
        }),
        required=False
    )

    class Meta:
        model = EgresoPagoViatico
        fields = [
            'solicitud',
            'numero_egreso',
            'ano_egreso',
            'medio_pago',
            'monto_total_pagado',
            'id_transferencia_bancaria',
            'numero_cheque',
            'banco_origen',
            'cuenta_origen',
            'rut_beneficiario',
            'nombre_beneficiario',
            'cuenta_destino',
            'fecha_pago',
            'glosa_contable',
        ]


class RendicionCometidoForm(forms.ModelForm):
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
        empty_label='Seleccione la solicitud a rendir',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    fecha_rendicion = forms.DateField(
        label='Fecha de Rendición',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )

    total_anticipo_recibido = forms.DecimalField(
        label='Total Anticipo Recibido ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=False
    )

    total_gastos_rendidos = forms.DecimalField(
        label='Total Gastos Rendidos y Justificados ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control fw-bold',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=True
    )

    monto_a_devolver_institucion = forms.DecimalField(
        label='Monto a Reintegrar / Devolver por Funcionario ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=False
    )

    monto_a_reembolsar_funcionario = forms.DecimalField(
        label='Monto a Reembolsar al Funcionario ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=False
    )

    informe_cometido_cumplido = forms.CharField(
        label='Informe Ejecutivo de Actividades Cumplidas',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Detalle de las actividades desarrolladas, objetivos alcanzados y justificación del gasto...'
        }),
        required=True
    )

    rendicion_aprobada = forms.BooleanField(
        label='¿Rendición aprobada por Jefatura y Finanzas?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    class Meta:
        model = RendicionCometido
        fields = [
            'solicitud',
            'fecha_rendicion',
            'total_anticipo_recibido',
            'total_gastos_rendidos',
            'monto_a_devolver_institucion',
            'monto_a_reembolsar_funcionario',
            'informe_cometido_cumplido',
            'rendicion_aprobada',
        ]


class DetalleRendicionGastoForm(forms.ModelForm):
    tipo_documento = forms.CharField(
        label='Tipo de Documento (Boleta / Factura / Ticket Peaje / Pasaje)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Factura Electrónica / Boleta Peaje'
        }),
        required=True
    )

    numero_documento = forms.CharField(
        label='N° Documento',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: F-12893'
        }),
        required=True
    )

    proveedor_razon_social = forms.CharField(
        label='Razón Social / Proveedor',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Hotel La Serena SpA / Autopista del Elqui'
        }),
        required=True
    )

    monto_documento = forms.DecimalField(
        label='Monto del Documento ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        required=True
    )

    comprobante_digital = forms.FileField(
        label='Imagen o PDF del Comprobante',
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        }),
        required=False
    )

    class Meta:
        model = DetalleRendicionGasto
        fields = [
            'tipo_documento',
            'numero_documento',
            'proveedor_razon_social',
            'monto_documento',
            'comprobante_digital',
        ]
