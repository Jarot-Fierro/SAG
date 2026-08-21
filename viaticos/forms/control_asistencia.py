from django import forms

from core.models.funcionario import Funcionario
from ..models.catalogos import LugarDestino
from ..models.control_asistencia import ValidacionRelojControl, PermisoGremial
from ..models.solicitud import SolicitudCometidoViatico


class ValidacionRelojControlForm(forms.ModelForm):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request:
            establecimiento = getattr(request.user, 'establecimiento', None)
            if establecimiento:
                self.fields['funcionario'].queryset = Funcionario.objects.filter(establecimiento=establecimiento)
                self.fields['solicitud'].queryset = SolicitudCometidoViatico.objects.filter(
                    establecimiento=establecimiento)

    funcionario = forms.ModelChoiceField(
        queryset=Funcionario.objects.all(),
        label='Funcionario',
        empty_label='Seleccione un funcionario',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    solicitud = forms.ModelChoiceField(
        queryset=SolicitudCometidoViatico.objects.all(),
        label='Cometido / Viático Asociado',
        empty_label='Seleccione solicitud asociada (opcional)',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )

    fecha_inicio_ausencia = forms.DateField(
        label='Fecha Inicio Ausencia',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )

    fecha_termino_ausencia = forms.DateField(
        label='Fecha Término Ausencia',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )

    tipo_ausentismo = forms.CharField(
        label='Tipo de Justificación de Asistencia',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'COMETIDO_FUNCIONAL'
        }),
        initial='COMETIDO_FUNCIONAL',
        required=True
    )

    dias_justificados = forms.IntegerField(
        label='Cantidad de Días Justificados',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1',
            'min': '1'
        }),
        initial=1,
        required=True
    )

    sincronizado_reloj = forms.BooleanField(
        label='¿Sincronizado con sistema Reloj Control?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    observacion_corte = forms.CharField(
        label='Observaciones de Asistencia / Reloj Control',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones relativas al corte de reloj control...'
        }),
        required=False
    )

    class Meta:
        model = ValidacionRelojControl
        fields = [
            'funcionario',
            'solicitud',
            'fecha_inicio_ausencia',
            'fecha_termino_ausencia',
            'tipo_ausentismo',
            'dias_justificados',
            'sincronizado_reloj',
            'observacion_corte',
        ]


class PermisoGremialForm(forms.ModelForm):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request:
            establecimiento = getattr(request.user, 'establecimiento', None)
            if establecimiento:
                self.fields['funcionario'].queryset = Funcionario.objects.filter(establecimiento=establecimiento)
                self.fields['aprobado_por'].queryset = Funcionario.objects.filter(establecimiento=establecimiento)
                self.fields['lugar_actividad'].queryset = LugarDestino.objects.filter(establecimiento=establecimiento)

    folio_gremial = forms.IntegerField(
        label='N° Folio Permiso Gremial',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 101'
        }),
        required=True
    )

    ano = forms.IntegerField(
        label='Año',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2026'
        }),
        initial=2026,
        required=True
    )

    funcionario = forms.ModelChoiceField(
        queryset=Funcionario.objects.all(),
        label='Dirigente / Funcionario',
        empty_label='Seleccione un dirigente gremial',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    cargo_en_gremio = forms.CharField(
        label='Cargo en la Asociación / Gremio (ej: AFSAG)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Presidente Regional / Secretario'
        }),
        required=True
    )

    lugar_actividad = forms.ModelChoiceField(
        queryset=LugarDestino.objects.all(),
        label='Lugar de la Actividad Gremial',
        empty_label='Seleccione lugar de destino',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    fecha_desde = forms.DateField(
        label='Desde',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )

    fecha_hasta = forms.DateField(
        label='Hasta',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )

    motivo = forms.CharField(
        label='Motivo de la Actividad Gremial',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describa la asamblea, reunión o comisión gremial...'
        }),
        required=True
    )

    aprobado = forms.BooleanField(
        label='¿Aprobado por Autoridad?',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )

    aprobado_por = forms.ModelChoiceField(
        queryset=Funcionario.objects.all(),
        label='Autoridad que Aprueba',
        empty_label='Seleccione autoridad aprobatoria',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )

    class Meta:
        model = PermisoGremial
        fields = [
            'folio_gremial',
            'ano',
            'funcionario',
            'cargo_en_gremio',
            'lugar_actividad',
            'motivo',
            'fecha_desde',
            'fecha_hasta',
            'aprobado',
            'aprobado_por',
        ]
