from django import forms

from ..models.computadores import Computador
from ..models.mantenedores import Marca, Modelo, Establecimiento, JefeTic, FuncionarioInventario, Contrato


class FormComputador(forms.ModelForm):
    numero_serie = forms.CharField(
        label='Número de Serie',
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'id': 'numero_serie_computador', 'class': 'form-control',
                'placeholder': 'Número de serie', 'maxlength': '150',
            }
        ),
        required=True,
    )
    marca = forms.ModelChoiceField(
        label='Marca',
        queryset=Marca.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Seleccione una marca',
        widget=forms.Select(
            attrs={'id': 'marca_computador', 'class': 'form-select tom-select'}
        ),
        required=True,
    )
    contrato = forms.ModelChoiceField(
        label='Contrato', required=True,
        queryset=Contrato.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Seleccione un contrato',
        widget=forms.Select(attrs={'id': 'contrato_impresora', 'class': 'form-select tom-select'}),
    )
    modelo = forms.ModelChoiceField(
        label='Modelo',
        queryset=Modelo.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Seleccione un modelo',
        widget=forms.Select(
            attrs={'id': 'modelo_computador', 'class': 'form-select tom-select'}
        ),
        required=True,
    )
    formato = forms.ChoiceField(
        label='Formato del Equipo',
        choices=[('', 'Seleccione un formato'), *Computador.Formato.choices],
        widget=forms.Select(attrs={'id': 'formato_computador', 'class': 'form-select tom-select'}),
        required=True,
    )
    procesador = forms.CharField(
        label='Procesador', max_length=150,
        widget=forms.TextInput(attrs={
            'id': 'procesador_computador', 'class': 'form-control',
            'placeholder': 'Ejemplo: Intel Core i5', 'maxlength': '150',
        }),
        required=False,
    )
    memoria_ram_gb = forms.IntegerField(
        label='Memoria RAM (GB)', min_value=1,
        widget=forms.NumberInput(attrs={
            'id': 'memoria_ram_gb_computador', 'class': 'form-control',
            'placeholder': 'Ejemplo: 16', 'min': '1', 'step': '1',
        }),
        required=False,
    )
    almacenamiento = forms.CharField(
        label='Almacenamiento', max_length=255,
        help_text='Ejemplo: SSD NVMe de 512 GB + HDD de 1 TB.',
        widget=forms.TextInput(attrs={
            'id': 'almacenamiento_computador', 'class': 'form-control',
            'placeholder': 'Ejemplo: SSD NVMe de 512 GB', 'maxlength': '255',
        }),
        required=False,
    )
    tarjeta_grafica = forms.CharField(
        label='Tarjeta Gráfica', max_length=150,
        widget=forms.TextInput(attrs={
            'id': 'tarjeta_grafica_computador', 'class': 'form-control',
            'placeholder': 'Ejemplo: Intel UHD Graphics', 'maxlength': '150',
        }),
        required=False,
    )
    observacion = forms.CharField(
        label='Observación',
        widget=forms.Textarea(attrs={
            'id': 'observacion_computador', 'class': 'form-control',
            'placeholder': 'Ingrese una observación', 'rows': 3,
        }),
        required=False,
    )

    class Meta:
        model = Computador
        fields = [
            'numero_serie', 'contrato', 'marca', 'modelo', 'formato', 'procesador',
            'memoria_ram_gb', 'almacenamiento', 'tarjeta_grafica', 'observacion',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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


class FormRecepcionComputador(forms.ModelForm):
    establecimiento_mantenedor = forms.ModelChoiceField(
        label='Establecimiento Destino',
        queryset=Establecimiento.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Selecciona un Establecimiento',
        widget=forms.Select(
            attrs={'id': 'establecimiento_mantenedor_computador', 'class': 'form-select tom-select'}
        ),
        required=True,
    )
    jefe_entrega = forms.ModelChoiceField(
        label='Jefe Entrega',
        queryset=JefeTic.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Selecciona una Opción',
        widget=forms.Select(
            attrs={'id': 'jefe_tic_computador', 'class': 'form-select'}
        ),
        required=True,
    )
    responsable = forms.ModelChoiceField(
        label='Responsable',
        queryset=FuncionarioInventario.objects.none(),
        empty_label='Seleccione un funcionario',
        widget=forms.Select(attrs={'id': 'responsable_computador', 'class': 'form-select tom-select'}),
        required=True,
    )

    class Meta:
        model = Computador
        fields = [
            'establecimiento_mantenedor', 'responsable',
            'jefe_entrega',
        ]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if request is not None:
            queryset = FuncionarioInventario.objects.filter(is_active=True)
            if not request.user.is_superuser:
                establecimiento_id = getattr(request.user, 'establecimiento_id', None)
                queryset = queryset.filter(
                    establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
            self.fields['responsable'].queryset = queryset.order_by('nombre', 'pk')
