from django import forms
from django.core.exceptions import ValidationError

from ..models.mantenedores import Contrato, Ips, JefeTic, Modelo
from ..models.mantenedores import Propietario, Marca, Establecimiento, TipoProducto, FuncionarioInventario


class FormTipoProducto(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre del tipo de producto',
        max_length=100,
        widget=forms.TextInput(attrs={
            'id': 'nombre_tipo_producto',
            'class': 'form-control',
            'placeholder': 'Ejemplo: Mouse, Teclado, UPS',
            'minlength': '1',
            'maxlength': '100',
        }),
        required=True,
    )

    class Meta:
        model = TipoProducto
        fields = ['nombre']


class FormEstablecimiento(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre del establecimiento',
        max_length=100,
        widget=forms.TextInput(attrs={
            'id': 'nombre_establecimiento',
            'class': 'form-control',
            'placeholder': 'Nombre del establecimiento',
            'minlength': '1',
            'maxlength': '100',
        }),
        required=True,
    )

    class Meta:
        model = Establecimiento
        fields = ['nombre']


def validate_exists(value, exists):
    if exists:
        raise ValidationError(f"{value} ya existe.")


class FormContrato(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre del contrato',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_contrato',
                'class': 'form-control',
                'placeholder': 'Tipo / Clausulas / Fecha del contrato',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )
    file = forms.FileField(
        label='Contrato',
        widget=forms.FileInput(
            attrs={
                'id': 'file_contrato',
                'class': 'form-control',
                'placeholder': 'Contrato',
                'minlength': '1',
            }
        ),
        required=False
    )
    fecha_inicio = forms.DateField(
        label='Fecha del contrato',
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date', 'class': 'form-control', 'placeholder': 'Fecha de inicio'},
        ),
        required=False
    )
    fecha_vencimiento = forms.DateField(
        label='Fecha del contrato',
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date', 'class': 'form-control', 'placeholder': 'Fecha de vencimiento'},
        ),
        required=False
    )
    dias_aviso = forms.IntegerField(
        label='Días de aviso',
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'min': 0, 'step': 1},
        ),
        required=False
    )
    notificar_vencimiento = forms.BooleanField(
        label='Notificar vencimiento',
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input'},
        ),
        required=False
    )

    class Meta:
        model = Contrato
        fields = [
            'nombre', 'file', 'fecha_inicio', 'fecha_vencimiento',
            'dias_aviso', 'notificar_vencimiento',
        ]

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_vencimiento = cleaned_data.get('fecha_vencimiento')

        if fecha_inicio and fecha_vencimiento and fecha_vencimiento < fecha_inicio:
            self.add_error(
                'fecha_vencimiento',
                'La fecha de vencimiento no puede ser anterior a la fecha de inicio.',
            )

        if cleaned_data.get('notificar_vencimiento') and not fecha_vencimiento:
            self.add_error(
                'fecha_vencimiento',
                'Indica la fecha de vencimiento para habilitar las notificaciones.',
            )

        return cleaned_data


class FormIps(forms.ModelForm):
    ip = forms.GenericIPAddressField(
        label='Dirección IP',
        protocol='IPv4',
        widget=forms.TextInput(
            attrs={
                'id': 'ip_ip',
                'class': 'form-control',
                'placeholder': '192.168.0.1',
                'minlength': '7',
                'maxlength': '15'
            }
        ),
        required=True
    )

    mascara = forms.GenericIPAddressField(
        label='Máscara',
        protocol='IPv4',
        required=False,
        widget=forms.TextInput(
            attrs={
                'id': 'ip_mascara',
                'class': 'form-control',
                'placeholder': '255.255.255.0',
                'minlength': '7',
                'maxlength': '15'
            }
        )
    )

    gateway = forms.GenericIPAddressField(
        label='Gateway',
        protocol='IPv4',
        required=False,
        widget=forms.TextInput(
            attrs={
                'id': 'ip_gateway',
                'class': 'form-control',
                'placeholder': '192.168.0.254',
                'minlength': '7',
                'maxlength': '15'
            }
        )
    )

    vlan = forms.CharField(
        label='VLAN',
        required=False,
        max_length=50,
        widget=forms.TextInput(
            attrs={
                'id': 'ip_vlan',
                'class': 'form-control',
                'placeholder': 'Ej: VLAN 10'
            }
        )
    )

    asignado = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                'id': 'ip_asignado',
                'class': 'form-check-input'
            }
        )
    )

    observacion = forms.CharField(
        label='Observación',
        required=False,
        widget=forms.Textarea(
            attrs={
                'id': 'ip_observacion',
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ingrese una observación (opcional)'
            }
        )
    )

    class Meta:
        model = Ips
        fields = [
            'ip',
            'mascara',
            'gateway',
            'vlan',
            'asignado',
            'observacion',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FormJefeTic(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_categoria',
                'class': 'form-control',
                'placeholder': 'Nombre de la Jefatura',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )
    posicion = forms.ChoiceField(
        label='Posicion',
        choices=[
            ('JEFE DPTO TIC', 'JEFE DPTO TIC'),
            ('JEFE(S) DPTO TIC', 'JEFE(S) DPTO TIC'),
            ('SUBROGANTE DPTO TIC', 'SUBROGANTE DPTO TIC'),
            ('JEFE DPTO MNT', 'JEFE DPTO MNT'),
            ('JEFE(S) DPTO MNT', 'JEFE(S) DPTO MNT'),
            ('SUBROGANTE DPTO MNT', 'SUBROGANTE DPTO MNT'),
        ],
        widget=forms.Select(
            attrs={
                'id': 'posicion_jefetic',
                'class': 'form-select tom-select',
                'placeholder': 'Seleccione una posición',
            }),
        required=True
    )

    class Meta:
        model = JefeTic
        fields = ['nombre', 'posicion']


class FormMarca(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la marca',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_marca',
                'class': 'form-control',
                'placeholder': 'Entel, HP, ',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )

    class Meta:
        model = Marca
        fields = ['nombre']


class FormModelo(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la modelo',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_modelo',
                'class': 'form-control',
                'placeholder': 'Serie del Modelo',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )
    marca = forms.ModelChoiceField(
        label='Marca',
        empty_label="",
        queryset=Marca.objects.all(),
        widget=forms.Select(
            attrs={
                'id': 'marca_modelo',
                'class': 'form-control form-select tom-select',
            }),
        required=True
    )

    class Meta:
        model = Modelo
        fields = ['nombre', 'marca']


class FormPropietario(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre del propietario',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_propietario',
                'class': 'form-control',
                'placeholder': 'Propietario',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )

    class Meta:
        model = Propietario
        fields = ['nombre']


class FormFuncionarioInventario(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre completo', max_length=255, required=True,
        widget=forms.TextInput(attrs={
            'id': 'nombre_funcionario', 'class': 'form-control',
            'placeholder': 'Nombre completo del funcionario', 'maxlength': '255',
        }),
    )

    class Meta:
        model = FuncionarioInventario
        fields = ['nombre']

    def clean_nombre(self):
        nombre = ' '.join(self.cleaned_data['nombre'].split())
        if not nombre:
            raise forms.ValidationError('Ingrese el nombre del funcionario.')
        return nombre
