from django import forms
from django.core.exceptions import ValidationError

from ..models.catalogo import Categoria, Contrato, Ips, JefeTic, LicenciaOs, Marca, MicrosoftOffice, Modelo, \
    Propietario, PuestoTrabajo, SistemaOperativo, SubCategoria, TipoCelular, TipoComputador, TipoImpresora, Toner


def validate_exists(value, exists):
    if exists:
        raise ValidationError(f"{value} ya existe.")


class FormCategoria(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la categoria',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_categoria',
                'class': 'form-control',
                'placeholder': 'Monitor/Cables/Adaptadores/Pendrives/Switch/Routers',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = Categoria.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = Categoria
        fields = ['nombre']


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

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = Contrato.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

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

    establecimiento = forms.ModelChoiceField(
        label='Establecimiento',
        queryset=None,
        required=False,
        empty_label='Seleccione un establecimiento',
        widget=forms.Select(
            attrs={
                'id': 'ip_establecimiento',
                'class': 'form-control select2'
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
            'establecimiento',
            'observacion',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['establecimiento'].queryset = self._meta.model._meta.get_field(
            'establecimiento').related_model.objects.all().order_by('nombre')

    def clean_ip(self):
        ip = self.cleaned_data['ip']
        current_instance = self.instance if self.instance.pk else None

        exists = Ips.objects.filter(ip__iexact=ip).exclude(
            pk=current_instance.pk if current_instance else None
        ).exists()

        validate_exists(ip, exists)
        return ip


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

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = JefeTic.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

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

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = LicenciaOs.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

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

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = Marca.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

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

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = MicrosoftOffice.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

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

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = Modelo.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

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

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = Propietario.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = Propietario
        fields = ['nombre']


class FormPuestoTrabajo(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la categoria',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_categoria',
                'class': 'form-control',
                'placeholder': 'PuestoTrabajo',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = PuestoTrabajo.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = PuestoTrabajo
        fields = ['nombre']


class FormSistemaOperativo(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la sistema operativo',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_sistema_operativo',
                'class': 'form-control',
                'placeholder': 'Windows 11 / Windows 10 / Windows 7 / Linux / macOS',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = SistemaOperativo.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = SistemaOperativo
        fields = ['nombre']


class FormSubCategoria(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre de la subcategoria',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre_subcategoria',
                'class': 'form-control',
                'placeholder': 'Pulgadas/Modelo/Tipo',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )
    categoria = forms.ModelChoiceField(
        required=True,
        empty_label='Selecciona una Categoría',
        label='Categoría',
        queryset=Categoria.objects.filter(is_active=True),
        widget=forms.Select(
            attrs={
                'id': 'categoria_subcategoria',
                'class': 'form-control select2',
            }
        ),
    )
    ver_mantencion = forms.BooleanField(
        required=False,
        label='Ver para Mantención',
        widget=forms.CheckboxInput(attrs={'class': 'mt-4 form-check-input'}),
    )
    ver_informatica = forms.BooleanField(
        required=False,
        label='Ver para Informática',
        widget=forms.CheckboxInput(attrs={'class': 'mt-4 form-check-input'}),
    )

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = SubCategoria.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = SubCategoria
        fields = ['nombre', 'categoria', 'ver_mantencion', 'ver_informatica']


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

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = TipoCelular.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

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

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = TipoComputador.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

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

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = TipoImpresora.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

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

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = Toner.objects.filter(nombre__iexact=nombre).exclude(
            pk=current_instance.pk if current_instance else None).exists()

        validate_exists(nombre, exists)
        return nombre

    class Meta:
        model = Toner
        fields = ['nombre']
