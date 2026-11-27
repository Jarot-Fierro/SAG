from django import forms

from ..models.celulares import Celular
from ..models.mantenedores import Marca, Modelo, Propietario, Establecimiento, JefeTic, FuncionarioInventario, Contrato


class FormCelular(forms.ModelForm):
    imei = forms.CharField(
        label='IMEI Principal',
        max_length=15,
        min_length=15,
        widget=forms.TextInput(
            attrs={
                'id': 'imei_celular',
                'class': 'form-control',
                'placeholder': 'IMEI de 15 dígitos',
                'minlength': '15',
                'maxlength': '15',
                'inputmode': 'numeric',
                'pattern': '[0-9]{15}',
            }
        ),
        required=True,
    )
    numero_telefono = forms.CharField(
        label='Número de Teléfono',
        max_length=20,
        widget=forms.TextInput(
            attrs={
                'id': 'id_numero_telefonico',
                'class': 'form-control',
                'placeholder': '+56912345678',
                'type': 'tel',
                'maxlength': '20',
            }
        ),
        required=False,
    )
    contrato = forms.ModelChoiceField(
        label='Contrato', required=True,
        queryset=Contrato.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Seleccione un contrato',
        widget=forms.Select(attrs={'id': 'contrato_impresora', 'class': 'form-select tom-select'}),
    )
    marca = forms.ModelChoiceField(
        label='Marca',
        queryset=Marca.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Seleccione una marca',
        widget=forms.Select(
            attrs={'id': 'marca_celular', 'class': 'form-select tom-select'}
        ),
        required=False,
    )
    modelo = forms.ModelChoiceField(
        label='Modelo',
        queryset=Modelo.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Seleccione un modelo',
        widget=forms.Select(
            attrs={'id': 'modelo_celular', 'class': 'form-select tom-select'}
        ),
        required=False,
    )
    propietario = forms.ModelChoiceField(
        label='Propietario',
        queryset=Propietario.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Seleccione un propietario',
        widget=forms.Select(
            attrs={'id': 'propietario_celular', 'class': 'form-select tom-select'}
        ),
        required=False,
    )
    minsal = forms.BooleanField(
        label='Minsal',
        widget=forms.CheckboxInput(
            attrs={'id': 'minsal_celular', 'class': 'form-check-input'}
        ),
        required=False,
    )
    pin = forms.CharField(
        label='PIN',
        max_length=20,
        widget=forms.TextInput(
            attrs={
                'id': 'pin_celular', 'class': 'form-control',
                'placeholder': 'PIN', 'maxlength': '20',
            }
        ),
        required=False,
    )
    puk = forms.CharField(
        label='PUK',
        max_length=20,
        widget=forms.TextInput(
            attrs={
                'id': 'puk_celular', 'class': 'form-control',
                'placeholder': 'PUK', 'maxlength': '20',
            }
        ),
        required=False,
    )
    numero_chip = forms.CharField(
        label='Número de Chip',
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'id': 'numero_chip_celular', 'class': 'form-control',
                'placeholder': 'Número de chip', 'maxlength': '100',
            }
        ),
        required=False,
    )
    minutos = forms.CharField(
        label='Minutos',
        max_length=20,
        widget=forms.TextInput(
            attrs={
                'id': 'minutos_celular', 'class': 'form-control',
                'placeholder': 'Ejemplo: 500 o ilimitados', 'maxlength': '20',
            }
        ),
        required=False,
    )

    observacion = forms.CharField(
        label='Observación',
        widget=forms.Textarea(
            attrs={
                'id': 'observacion_celular', 'class': 'form-control',
                'placeholder': 'Ingrese una observación', 'rows': 3,
            }
        ),
        required=False,
    )

    class Meta:
        model = Celular
        fields = [
            'imei', 'contrato', 'numero_telefono', 'marca', 'modelo', 'propietario',
            'minsal', 'pin', 'puk', 'numero_chip', 'minutos', 'observacion',

        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        modelos = self.fields['modelo'].queryset
        self.modelos_por_marca = list(modelos.values('id', 'nombre', 'marca_id'))

        marca_id = (
            self.data.get(self.add_prefix('marca'))
            if self.is_bound else self.initial.get('marca')
        )
        try:
            marca_id = int(marca_id)
        except (TypeError, ValueError):
            marca_id = None

        self.fields['modelo'].queryset = (
            modelos.filter(marca_id=marca_id) if marca_id else modelos.none()
        )
        if not marca_id:
            self.fields['modelo'].widget.attrs['disabled'] = True

    def clean(self):
        cleaned_data = super().clean()
        marca = cleaned_data.get('marca')
        modelo = cleaned_data.get('modelo')

        if marca and modelo and modelo.marca_id != marca.pk:
            self.add_error('modelo', 'El modelo seleccionado no pertenece a la marca indicada.')

        return cleaned_data


class FormRecepcionCelular(forms.ModelForm):
    establecimiento_mantenedor = forms.ModelChoiceField(
        label='Establecimiento Destino',
        queryset=Establecimiento.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Selecciona un Establecimiento',
        widget=forms.Select(
            attrs={'id': 'establecimiento_mantenedor_celular', 'class': 'form-select tom-select'}
        ),
        required=True,
    )
    jefe_entrega = forms.ModelChoiceField(
        label='Jefe Entrega',
        queryset=JefeTic.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Selecciona una Opción',
        widget=forms.Select(
            attrs={'id': 'jefe_tic_celular', 'class': 'form-select'}
        ),
        required=True,
    )
    responsable = forms.ModelChoiceField(
        label='Responsable',
        queryset=FuncionarioInventario.objects.none(),
        empty_label='Seleccione un funcionario',
        widget=forms.Select(attrs={'id': 'responsable_celular', 'class': 'form-select tom-select'}),
        required=True,
    )

    class Meta:
        model = Celular
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
