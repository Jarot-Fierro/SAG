from django import forms

from ..models.catalogos import VistoLegal
from ..models.resoluciones import ResolucionCometido
from ..models.solicitud import SolicitudCometidoViatico


class ResolucionCometidoForm(forms.ModelForm):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request:
            establecimiento = getattr(request.user, 'establecimiento', None)
            if establecimiento:
                self.fields['vistos'].queryset = VistoLegal.objects.filter(establecimiento=establecimiento)
                self.fields['solicitud'].queryset = SolicitudCometidoViatico.objects.filter(
                    establecimiento=establecimiento)

    solicitud = forms.ModelChoiceField(
        queryset=SolicitudCometidoViatico.objects.all(),
        label='Solicitud de Cometido / Viático',
        empty_label='Seleccione la solicitud a formalizar',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    numero_resolucion = forms.IntegerField(
        label='N° Resolución Exenta',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 1420'
        }),
        required=True
    )

    ano_resolucion = forms.IntegerField(
        label='Año Resolución',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2026'
        }),
        initial=2026,
        required=True
    )

    fecha_emision = forms.DateField(
        label='Fecha de Emisión',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )

    vistos = forms.ModelMultipleChoiceField(
        queryset=VistoLegal.objects.all(),
        label='Vistos Legales Aplicados',
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control form-select',
            'size': '5'
        }),
        required=False
    )

    firmante_nombre = forms.CharField(
        label='Nombre del Firmante Legal',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Dr. Juan Pérez'
        }),
        required=True
    )

    firmante_cargo = forms.CharField(
        label='Cargo del Firmante Legal',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Director Regional SAG Coquimbo'
        }),
        required=True
    )

    considerandos = forms.CharField(
        label='Considerandos Específicos',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Indique los considerandos y motivos fundados de la resolución...'
        }),
        required=True
    )

    texto_resuelve = forms.CharField(
        label='Cuerpo del Resuelve',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': '1° AUTORÍZASE el cometido funcional...\n2° IMPÚTESE el gasto a la cuenta...'
        }),
        required=True
    )

    documento_pdf_firmado = forms.FileField(
        label='Documento PDF Resolución Firmada',
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        }),
        required=False
    )

    class Meta:
        model = ResolucionCometido
        fields = [
            'solicitud',
            'numero_resolucion',
            'ano_resolucion',
            'fecha_emision',
            'vistos',
            'firmante_nombre',
            'firmante_cargo',
            'considerandos',
            'texto_resuelve',
            'documento_pdf_firmado',
        ]
