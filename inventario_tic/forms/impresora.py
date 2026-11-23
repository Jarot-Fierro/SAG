from django import forms
from .contratos import ContratoEquipoFormMixin

from core.models.unidad_organizacional import UnidadOrganizacional
from ..models.impresoras import Impresora
from ..models.mantenedores import Marca, Modelo


class FormImpresora(ContratoEquipoFormMixin, forms.ModelForm):
    numero_serie = forms.CharField(
        label='Número de Serie', max_length=150, required=True,
        widget=forms.TextInput(attrs={
            'id': 'numero_serie_impresora', 'class': 'form-control',
            'placeholder': 'Número de serie', 'maxlength': '150',
        }),
    )
    hh = forms.CharField(
        label='HH', max_length=150, required=True,
        widget=forms.TextInput(attrs={
            'id': 'hh_impresora', 'class': 'form-control',
            'placeholder': 'HH', 'maxlength': '150',
        }),
    )
    marca = forms.ModelChoiceField(
        label='Marca', required=True,
        queryset=Marca.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Seleccione una marca',
        widget=forms.Select(attrs={'id': 'marca_impresora', 'class': 'form-select tom-select'}),
    )
    modelo = forms.ModelChoiceField(
        label='Modelo', required=True,
        queryset=Modelo.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Seleccione un modelo',
        widget=forms.Select(attrs={'id': 'modelo_impresora', 'class': 'form-select tom-select'}),
    )
    imprime_color = forms.BooleanField(
        label='¿Imprime a Color?', required=False,
        widget=forms.CheckboxInput(attrs={'id': 'imprime_color_impresora', 'class': 'form-check-input'}),
    )
    tiene_ethernet = forms.BooleanField(
        label='¿Tiene Ethernet?', required=False,
        widget=forms.CheckboxInput(attrs={'id': 'tiene_ethernet_impresora', 'class': 'form-check-input'}),
    )
    tiene_wifi = forms.BooleanField(
        label='¿Tiene Wi-Fi?', required=False,
        widget=forms.CheckboxInput(attrs={'id': 'tiene_wifi_impresora', 'class': 'form-check-input'}),
    )
    toner = forms.CharField(
        label='Modelo de Consumible', max_length=150, required=False,
        help_text='Referencia del tóner, cartucho o tinta compatible.',
        widget=forms.TextInput(attrs={
            'id': 'toner_impresora', 'class': 'form-control',
            'placeholder': 'Tóner, cartucho o tinta', 'maxlength': '150',
        }),
    )
    departamento = forms.ModelChoiceField(
        label='Departamento Asignado', required=True,
        queryset=UnidadOrganizacional.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Seleccione un departamento',
        widget=forms.Select(attrs={'id': 'departamento_impresora', 'class': 'form-select tom-select'}),
    )
    observacion = forms.CharField(
        label='Observación', required=False,
        widget=forms.Textarea(attrs={
            'id': 'observacion_impresora', 'class': 'form-control',
            'placeholder': 'Ingrese una observación', 'rows': 3,
        }),
    )

    class Meta:
        model = Impresora
        fields = [
            'numero_serie', 'contrato', 'hh', 'marca', 'modelo', 'imprime_color',
            'tiene_ethernet', 'tiene_wifi', 'toner', 'departamento', 'observacion',
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        establecimiento_id = getattr(
            getattr(self.request, 'user', None), 'establecimiento_id', None,
        )
        self.fields['departamento'].queryset = (
            UnidadOrganizacional.objects.filter(
                establecimiento_id=establecimiento_id, is_active=True,
            ).order_by('nombre')
            if establecimiento_id else UnidadOrganizacional.objects.none()
        )
        modelos = self.fields['modelo'].queryset
        self.modelos_por_marca = list(modelos.values('id', 'nombre', 'marca_id'))
        marca_id = self.data.get(self.add_prefix('marca')) if self.is_bound else self.initial.get('marca')
        try:
            marca_id = int(marca_id)
        except (TypeError, ValueError):
            marca_id = None
        self.fields['modelo'].queryset = modelos.filter(marca_id=marca_id) if marca_id else modelos.none()
        if not marca_id:
            self.fields['modelo'].widget.attrs['disabled'] = True

    def clean(self):
        cleaned_data = super().clean()
        marca = cleaned_data.get('marca')
        modelo = cleaned_data.get('modelo')
        if marca and modelo and modelo.marca_id != marca.pk:
            self.add_error('modelo', 'El modelo seleccionado no pertenece a la marca indicada.')
        return cleaned_data
