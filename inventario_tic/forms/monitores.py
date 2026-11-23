from django import forms

from ..models.mantenedores import Marca, Modelo, Establecimiento, JefeTic, FuncionarioInventario
from ..models.monitores import Monitor


class FormMonitor(forms.ModelForm):
    numero_serie = forms.CharField(
        label='Número de Serie',
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'id': 'numero_serie_monitor', 'class': 'form-control',
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
            attrs={'id': 'marca_monitor', 'class': 'form-select tom-select'}
        ),
        required=True,
    )
    modelo = forms.ModelChoiceField(
        label='Modelo',
        queryset=Modelo.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Seleccione un modelo',
        widget=forms.Select(
            attrs={'id': 'modelo_monitor', 'class': 'form-select tom-select'}
        ),
        required=True,
    )
    pulgadas = forms.DecimalField(
        label='Tamaño en Pulgadas',
        max_digits=4,
        decimal_places=1,
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                'id': 'pulgadas_monitor', 'class': 'form-control',
                'placeholder': 'Ejemplo: 24', 'min': '1', 'step': '0.1',
            }
        ),
        required=False,
    )
    resolucion = forms.CharField(
        label='Resolución',
        max_length=50,
        help_text='Ejemplo: 1920 x 1080.',
        widget=forms.TextInput(
            attrs={
                'id': 'resolucion_monitor', 'class': 'form-control',
                'placeholder': '1920 x 1080', 'maxlength': '50',
            }
        ),
        required=False,
    )
    frecuencia_hz = forms.IntegerField(
        label='Frecuencia de Actualización (Hz)',
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                'id': 'frecuencia_hz_monitor', 'class': 'form-control',
                'placeholder': 'Ejemplo: 60', 'min': '1', 'step': '1',
            }
        ),
        required=False,
    )
    tiene_hdmi = forms.BooleanField(
        label='¿Tiene HDMI?',
        widget=forms.CheckboxInput(
            attrs={'id': 'tiene_hdmi_monitor', 'class': 'form-check-input'}
        ),
        required=False,
    )
    tiene_displayport = forms.BooleanField(
        label='¿Tiene DisplayPort?',
        widget=forms.CheckboxInput(
            attrs={'id': 'tiene_displayport_monitor', 'class': 'form-check-input'}
        ),
        required=False,
    )
    tiene_vga = forms.BooleanField(
        label='¿Tiene VGA?',
        widget=forms.CheckboxInput(
            attrs={'id': 'tiene_vga_monitor', 'class': 'form-check-input'}
        ),
        required=False,
    )
    tiene_dvi = forms.BooleanField(
        label='¿Tiene DVI?',
        widget=forms.CheckboxInput(
            attrs={'id': 'tiene_dvi_monitor', 'class': 'form-check-input'}
        ),
        required=False,
    )
    tiene_usb_c = forms.BooleanField(
        label='¿Tiene USB-C?',
        widget=forms.CheckboxInput(
            attrs={'id': 'tiene_usb_c_monitor', 'class': 'form-check-input'}
        ),
        required=False,
    )
    observacion = forms.CharField(
        label='Observación',
        widget=forms.Textarea(
            attrs={
                'id': 'observacion_monitor', 'class': 'form-control',
                'placeholder': 'Ingrese una observación', 'rows': 3,
            }
        ),
        required=False,
    )

    class Meta:
        model = Monitor
        fields = [
            'numero_serie', 'marca', 'modelo', 'pulgadas', 'resolucion', 'frecuencia_hz',
            'tiene_hdmi', 'tiene_displayport', 'tiene_vga', 'tiene_dvi', 'tiene_usb_c', 'observacion',
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


class FormRecepcionMonitor(forms.ModelForm):
    establecimiento_mantenedor = forms.ModelChoiceField(
        label='Establecimiento Destino',
        queryset=Establecimiento.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Selecciona un Establecimiento',
        widget=forms.Select(
            attrs={'id': 'establecimiento_mantenedor_monitor', 'class': 'form-select tom-select'}
        ),
        required=True,
    )
    jefe_entrega = forms.ModelChoiceField(
        label='Jefe Entrega',
        queryset=JefeTic.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Selecciona una Opción',
        widget=forms.Select(
            attrs={'id': 'jefe_tic_monitor', 'class': 'form-select'}
        ),
        required=True,
    )
    responsable = forms.ModelChoiceField(
        label='Responsable',
        queryset=FuncionarioInventario.objects.none(),
        empty_label='Seleccione un funcionario',
        widget=forms.Select(attrs={'id': 'responsable_monitor', 'class': 'form-select tom-select'}),
        required=True,
    )

    class Meta:
        model = Monitor
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
                queryset = queryset.filter(establecimiento_id=establecimiento_id) if establecimiento_id else queryset.none()
            self.fields['responsable'].queryset = queryset.order_by('nombre', 'pk')
