from django import forms

from ..models.catalogos import LugarDestino, EscalaViatico, VistoLegal


class LugarDestinoForm(forms.ModelForm):
    codigo = forms.CharField(
        label='Código de Lugar',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: LUG-001'
        }),
        required=True
    )
    nombre = forms.CharField(
        label='Nombre / Ciudad / Localidad',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Vicuña / Paihuano'
        }),
        required=True
    )
    region = forms.CharField(
        label='Región',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Coquimbo'
        }),
        initial='Coquimbo',
        required=True
    )
    comuna = forms.CharField(
        label='Comuna',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: La Serena'
        }),
        required=False
    )
    distancia_km_referencial = forms.IntegerField(
        label='Distancia Referencial (KM)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        }),
        initial=0,
        required=False
    )
    es_rural_dificil_acceso = forms.BooleanField(
        label='¿Es zona rural o de difícil acceso?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )
    descripcion_adicional = forms.CharField(
        label='Detalle / Observaciones de Ubicación',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Detalles de la ruta, accesos, etc.'
        }),
        required=False
    )

    class Meta:
        model = LugarDestino
        fields = [
            'codigo',
            'nombre',
            'region',
            'comuna',
            'distancia_km_referencial',
            'es_rural_dificil_acceso',
            'descripcion_adicional',
        ]


class EscalaViaticoForm(forms.ModelForm):
    ano_vigencia = forms.IntegerField(
        label='Año de Vigencia Presupuestaria',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2026'
        }),
        required=True
    )
    grado_desde = forms.CharField(
        label='Grado Desde',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 1'
        }),
        required=True
    )
    grado_hasta = forms.CharField(
        label='Grado Hasta',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 5'
        }),
        required=True
    )
    estamento = forms.CharField(
        label='Estamento / Ley Aplicable',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Ley Médica / Directivo / Profesional'
        }),
        required=False
    )
    valor_100_pernocta = forms.DecimalField(
        label='Valor Viático 100% Pernocta ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        required=True
    )
    valor_50_parcial = forms.DecimalField(
        label='Valor Viático 50% Alimentación / Parcial ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        required=True
    )
    valor_faena = forms.DecimalField(
        label='Valor Viático Faena ($)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        initial=0,
        required=False
    )
    observacion = forms.CharField(
        label='Observaciones',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Observaciones adicionales de la escala tarifaria'
        }),
        required=False
    )

    class Meta:
        model = EscalaViatico
        fields = [
            'ano_vigencia',
            'grado_desde',
            'grado_hasta',
            'estamento',
            'valor_100_pernocta',
            'valor_50_parcial',
            'valor_faena',
            'observacion',
        ]


class VistoLegalForm(forms.ModelForm):
    codigo = forms.CharField(
        label='Código / Referencia',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: VISTO-01'
        }),
        required=True
    )
    corresponde_a = forms.CharField(
        label='Corresponde a (Cometido / Viático / Ambos)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Cometido y Viático'
        }),
        required=False
    )
    orden = forms.IntegerField(
        label='Orden de Aparición',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1'
        }),
        initial=1,
        required=True
    )
    texto_visto = forms.CharField(
        label='Texto del Visto Legal',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Texto formal del visto para la resolución exenta...'
        }),
        required=True
    )

    class Meta:
        model = VistoLegal
        fields = [
            'codigo',
            'corresponde_a',
            'orden',
            'texto_visto',
        ]
