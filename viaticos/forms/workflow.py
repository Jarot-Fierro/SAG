from django import forms

from ..models.wokflow import AprobacionCometido


class AprobacionCometidoForm(forms.ModelForm):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request:
            if hasattr(request.user, 'funcionario') and request.user.funcionario:
                if request.user.funcionario.cargo:
                    self.initial['en_calidad_de'] = request.user.funcionario.cargo

    etapa = forms.ChoiceField(
        choices=AprobacionCometido.ETAPA_CHOICES,
        label='Etapa del Flujo',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    accion = forms.ChoiceField(
        choices=AprobacionCometido.ESTADO_ACCION_CHOICES,
        label='Acción a Realizar',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    en_calidad_de = forms.CharField(
        label='En Calidad de (Cargo / Función)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Jefe Departamento / Director Regional (S)'
        }),
        required=True
    )

    es_subrogante = forms.BooleanField(
        label='¿Firma en calidad de Subrogante?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    firmado_con_fea = forms.BooleanField(
        label='¿Firmado con Firma Electrónica Avanzada (FEA)?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    observaciones = forms.CharField(
        label='Observaciones / Motivo de Aprobación, Rechazo o Devolución',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Indique comentarios, justificación técnica o motivos en caso de devolución/rechazo...'
        }),
        required=False
    )

    class Meta:
        model = AprobacionCometido
        fields = [
            'etapa',
            'accion',
            'en_calidad_de',
            'es_subrogante',
            'firmado_con_fea',
            'observaciones',
        ]
