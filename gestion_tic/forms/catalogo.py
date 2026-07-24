from django import forms
from django.core.exceptions import ValidationError

from ..models.catalogo import Contrato, Ips, JefeTic, LicenciaOs, Marca, MicrosoftOffice, Modelo, \
    Propietario, TipoCelular, TipoComputador, TipoImpresora, Toner


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

    class Meta:
        model = Contrato
        fields = ['nombre']


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
            ('JEFE DPTO MNT', 'JEFE DPTO MNT'),
            ('JEFE(S) DPTO MNT', 'JEFE(S) DPTO MNT')
        ],
        widget=forms.Select(
            attrs={
                'id': 'nombre_categoria',
                'class': 'form-control',
                'placeholder': '',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )

    class Meta:
        model = JefeTic
        fields = ['nombre', 'posicion']


class FormLicenciaOs(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la licencia_os',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_licencia_os',
                'class': 'form-control',
                'placeholder': 'Lebu',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )

    class Meta:
        model = LicenciaOs
        fields = ['nombre']


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


class FormMicrosoftOffice(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la versión de microsoft office',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_microsoft_office',
                'class': 'form-control',
                'placeholder': 'office 2007, office 2016, office 2019, Microsoft 365',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )

    class Meta:
        model = MicrosoftOffice
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

    class Meta:
        model = Modelo
        fields = ['nombre']


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


class FormTipoCelular(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la tipo plan',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_tipo_celular',
                'class': 'form-control',
                'placeholder': 'Smartphone / Anexo',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )

    class Meta:
        model = TipoCelular
        fields = ['nombre']


class FormTipoComputador(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la tipo computador',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_tipo_computador',
                'class': 'form-control',
                'placeholder': 'Escritorio/Notebook/OnlyOne',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )

    class Meta:
        model = TipoComputador
        fields = ['nombre']


class FormTipoImpresora(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la tipo impresora',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_tipo_impresora',
                'class': 'form-control',
                'placeholder': 'Multifuncion / Con escaner',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )

    class Meta:
        model = TipoImpresora
        fields = ['nombre']


class FormToner(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la categoria',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_categoria',
                'class': 'form-control',
                'placeholder': 'Estándar Negro / Alta Capacidad / Toner Color',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )

    class Meta:
        model = Toner
        fields = ['nombre']
