from django import forms

from core.models.funcionario import Funcionario
from gestion_tic.models import MovimientoActivo, TipoMovimiento
from gestion_tic.models.catalogo import Ips


class MovimientoActivoForm(forms.ModelForm):
    tipo_movimiento = forms.ModelChoiceField(
        label='Tipo Movimiento',
        empty_label='Seleccione un tipo de movimiento',
        required=True,
        queryset=TipoMovimiento.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    funcionario = forms.ModelChoiceField(
        label='Funcionario',
        empty_label='Seleccione un funcionario',
        required=False,
        queryset=Funcionario.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )

    ip = forms.ModelChoiceField(
        empty_label='Seleccione una IP',
        required=False,
        queryset=Ips.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )

    observacion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    class Meta:
        model = MovimientoActivo
        fields = ['tipo_movimiento', 'funcionario', 'ip', 'observacion']

    def __init__(self, *args, **kwargs):
        establecimiento = kwargs.pop('establecimiento', None)
        super().__init__(*args, **kwargs)
        if establecimiento:
            self.fields['tipo_movimiento'].queryset = TipoMovimiento.objects.filter(establecimiento=establecimiento,
                                                                                    is_active=True)
            self.fields['funcionario'].queryset = Funcionario.objects.filter(establecimiento=establecimiento,
                                                                             is_active=True)
            self.fields['ip'].queryset = Ips.objects.filter(establecimiento=establecimiento, is_active=True)
