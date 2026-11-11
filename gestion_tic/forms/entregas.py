from django import forms
from django.forms import formset_factory
from core.models.funcionario import Funcionario
from gestion_tic.models import EntregaActivos, DetalleEntrega, TipoMovimiento, JefeTic, Ips, Accesorio


def estilizar(form):
    for field in form.fields.values():
        field.widget.attrs['class'] = ('form-select' if isinstance(field.widget, forms.Select)
                                      else 'form-control')
        if isinstance(field.widget, forms.Textarea):
            field.widget.attrs['rows'] = 2


class EntregaForm(forms.ModelForm):
    class Meta:
        model = EntregaActivos
        fields = ['funcionario', 'tipo_movimiento', 'jefe_firmante', 'observacion']
        labels = {'funcionario': 'Funcionario destinatario', 'tipo_movimiento': 'Tipo de movimiento',
                  'jefe_firmante': 'Jefe firmante', 'observacion': 'Observaciones de la entrega'}

    def __init__(self, *args, establecimiento, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)
        self.fields['funcionario'].queryset = Funcionario.objects.filter(
            establecimiento=establecimiento, is_active=True)
        self.fields['tipo_movimiento'].queryset = TipoMovimiento.objects.filter(
            establecimiento=establecimiento, is_active=True, requiere_recepcion=True)
        self.fields['jefe_firmante'].queryset = JefeTic.objects.filter(
            establecimiento=establecimiento, is_active=True)


class DetalleForm(forms.ModelForm):
    codigo = forms.CharField(label='Código de barras o serie', max_length=150)

    class Meta:
        model = DetalleEntrega
        fields = ['ip', 'observacion']
        labels = {'observacion': 'Observaciones del activo'}

    def __init__(self, *args, establecimiento, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)
        self.fields['ip'].queryset = Ips.objects.filter(
            establecimiento=establecimiento, is_active=True).order_by('ip')
        self.fields['ip'].label = 'IP (opcional)'
        self.order_fields(['codigo', 'ip', 'observacion'])
        self.fields['codigo'].widget.attrs['autofocus'] = True
        if self.instance.pk:
            self.fields['codigo'].initial = self.instance.activo.codigo_barra
            self.fields['codigo'].disabled = True


class AccesorioForm(forms.Form):
    accesorio = forms.ModelChoiceField(queryset=Accesorio.objects.none(), required=False)
    cantidad = forms.IntegerField(min_value=1, initial=1)
    observacion = forms.CharField(max_length=255, required=False)

    def __init__(self, *args, establecimiento, **kwargs):
        super().__init__(*args, **kwargs)
        estilizar(self)
        self.fields['accesorio'].queryset = Accesorio.objects.filter(
            establecimiento=establecimiento, is_active=True).order_by('nombre')


AccesoriosFormSet = formset_factory(AccesorioForm, extra=1, can_delete=True, max_num=100,
                                   validate_max=True)
