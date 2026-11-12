from django import forms
from django.forms import formset_factory

from core.models.funcionario import Funcionario
from gestion_tic.models import EntregaActivos, DetalleEntrega, TipoMovimiento, JefeTic, Ips, Accesorio


class EntregaForm(forms.ModelForm):
    funcionario = forms.ModelChoiceField(
        label='Funcionario destinatario',
        queryset=Funcionario.objects.none(),
        empty_label='',
        required=True,
        widget=forms.Select(attrs={'class': 'form-select tom-select'})
    )
    tipo_movimiento = forms.ModelChoiceField(
        label='Tipo de movimiento',
        empty_label='',
        queryset=TipoMovimiento.objects.none(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select tom-select'})
    )
    jefe_firmante = forms.ModelChoiceField(
        label='Jefe firmante',
        empty_label='',
        queryset=JefeTic.objects.none(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select tom-select'})
    )
    observacion = forms.CharField(
        label='Observaciones de la entrega',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    class Meta:
        model = EntregaActivos
        fields = ['funcionario', 'tipo_movimiento', 'jefe_firmante', 'observacion']

    def __init__(self, *args, establecimiento, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['funcionario'].queryset = Funcionario.objects.filter(
            establecimiento=establecimiento, is_active=True)
        self.fields['tipo_movimiento'].queryset = TipoMovimiento.objects.filter(
            establecimiento=establecimiento, is_active=True, requiere_recepcion=True)
        self.fields['jefe_firmante'].queryset = JefeTic.objects.filter(
            establecimiento=establecimiento, is_active=True)


class DetalleForm(forms.ModelForm):
    codigo = forms.CharField(
        label='Código de barras o serie',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autofocus': True})
    )
    ip = forms.ModelChoiceField(
        label='IP (opcional)',
        queryset=Ips.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select tom-select'})
    )
    observacion = forms.CharField(
        label='Observaciones del activo',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    class Meta:
        model = DetalleEntrega
        fields = ['ip', 'observacion']

    def __init__(self, *args, establecimiento, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ip'].queryset = Ips.objects.filter(
            establecimiento=establecimiento, is_active=True).order_by('ip')
        self.order_fields(['codigo', 'ip', 'observacion'])
        if self.instance.pk:
            self.fields['codigo'].initial = self.instance.activo.codigo_barra
            self.fields['codigo'].disabled = True


class AccesorioForm(forms.Form):
    accesorio = forms.ModelChoiceField(
        label='Accesorio',
        queryset=Accesorio.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select tom-select'})
    )
    cantidad = forms.IntegerField(
        label='Cantidad',
        min_value=1,
        initial=1,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    observacion = forms.CharField(
        label='Observación',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, establecimiento, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['accesorio'].queryset = Accesorio.objects.filter(
            establecimiento=establecimiento, is_active=True).order_by('nombre')


AccesoriosFormSet = formset_factory(AccesorioForm, extra=1, can_delete=True, max_num=100,
                                    validate_max=True)
