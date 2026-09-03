from django import forms
from django.db.models.expressions import RawSQL

from core.models.funcionario import Funcionario
from gestion_tic.models import MovimientoActivo, TipoMovimiento
from gestion_tic.models.catalogo import Ips, JefeTic


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

    jefe_firmante = forms.ModelChoiceField(
        empty_label='Seleccione una IP',
        required=True,
        queryset=JefeTic.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    observacion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    class Meta:
        model = MovimientoActivo
        fields = ['tipo_movimiento', 'funcionario', 'ip', 'observacion', 'jefe_firmante']

    def __init__(self, *args, **kwargs):
        establecimiento = kwargs.pop('establecimiento', None)
        super().__init__(*args, **kwargs)
        if establecimiento:
            self.fields['tipo_movimiento'].queryset = TipoMovimiento.objects.filter(establecimiento=establecimiento,
                                                                                    is_active=True)
            self.fields['funcionario'].queryset = Funcionario.objects.filter(is_active=True)
            self.fields['ip'].queryset = (
                Ips.objects
                .filter(
                    establecimiento=establecimiento,
                    is_active=True
                )
                .annotate(
                    ip_sort=RawSQL(
                        """
                        (
                            CAST(SUBSTRING_INDEX(ip, '.', 1) AS UNSIGNED) * 16777216 +
                            CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(ip, '.', 2), '.', -1) AS UNSIGNED) * 65536 +
                            CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(ip, '.', 3), '.', -1) AS UNSIGNED) * 256 +
                            CAST(SUBSTRING_INDEX(ip, '.', -1) AS UNSIGNED)
                        )
                        """,
                        []
                    )
                )
                .order_by('ip_sort')
            )
            self.fields['jefe_firmante'].queryset = JefeTic.objects.filter(establecimiento=establecimiento,
                                                                           is_active=True)
