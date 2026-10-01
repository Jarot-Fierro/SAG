from django import forms
from django.utils import timezone

from core.models.establecimientos import Establecimiento
from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional
from solicitud_vpn.models import SolicitudVPN, BeneficiarioVPN, AccesoVPN, PerfilVPN
from solicitud_vpn.utils import obtener_departamento_principal, obtener_datos_tecnico_solicitante


class SolicitudVPNForm(forms.ModelForm):
    departamento_solicitante = forms.ModelChoiceField(
        queryset=UnidadOrganizacional.objects.filter(is_active=True),
        required=True,
        label='Departamento / Unidad Solicitante',
        widget=forms.Select(attrs={'class': 'form-select select2', 'data-placeholder': 'Seleccione Departamento / Unidad'})
    )
    accion = forms.ChoiceField(
        choices=SolicitudVPN.ACCIONES,
        required=True,
        label='Acción',
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )
    es_proveedor = forms.BooleanField(
        required=False,
        label='¿Es proveedor / empresa tercera?',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    grupo_vpn = forms.CharField(
        max_length=150,
        required=False,
        label='Nombre del Grupo VPN',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: VPN-SSARAUCO-HOSPITAL'})
    )
    fecha_expiracion = forms.DateField(
        required=False,
        label='Fecha de Expiración',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    timeout_vpn = forms.CharField(
        max_length=50,
        required=False,
        initial='1 hora',
        label='Time Out VPN',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1 hora, 30 min, 8 horas'})
    )
    observacion = forms.CharField(
        required=False,
        label='Observaciones / Descripción General',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Indique detalles generales del requerimiento o consideraciones para eConecta'
        })
    )

    # Datos del Técnico Solicitante
    tecnico_nombre = forms.CharField(
        max_length=255,
        required=True,
        label='Nombre Completo del Técnico / Solicitante',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan Pérez Soto'})
    )
    tecnico_rut = forms.CharField(
        max_length=20,
        required=True,
        label='RUT del Técnico',
        widget=forms.TextInput(attrs={'class': 'form-control rut-input', 'placeholder': 'Ej: 12.345.678-9'})
    )
    tecnico_establecimiento = forms.CharField(
        max_length=255,
        required=True,
        label='Establecimiento del Técnico',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Hospital Arauco'})
    )
    tecnico_telefono = forms.CharField(
        max_length=50,
        required=False,
        label='Teléfono del Técnico',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: +56 9 1234 5678'})
    )
    tecnico_cargo = forms.CharField(
        max_length=255,
        required=False,
        label='Cargo del Técnico',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Encargado de Informática'})
    )
    tecnico_email = forms.CharField(
        max_length=254,
        required=True,
        label='Email del Técnico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej: tecnico@ssarauco.cl'})
    )
    tecnico_fecha = forms.DateField(
        required=True,
        label='Fecha de Creación',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    class Meta:
        model = SolicitudVPN
        fields = [
            'departamento_solicitante',
            'accion',
            'es_proveedor',
            'grupo_vpn',
            'fecha_expiracion',
            'timeout_vpn',
            'observacion',
            'tecnico_nombre',
            'tecnico_rut',
            'tecnico_establecimiento',
            'tecnico_telefono',
            'tecnico_cargo',
            'tecnico_email',
            'tecnico_fecha',
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request and self.request.user.is_authenticated:
            user = self.request.user
            est = getattr(user, 'establecimiento', None)

            # Filtrar departamentos por establecimiento del usuario si corresponde
            if est and not user.is_superuser:
                self.fields['departamento_solicitante'].queryset = UnidadOrganizacional.objects.filter(
                    is_active=True,
                    establecimiento=est
                )

            # Determinar departamento por defecto a partir de la jerarquía
            if not self.is_bound and not self.instance.pk:
                unidad_usuario = None
                if hasattr(user, 'funcionario') and user.funcionario:
                    unidad_usuario = user.funcionario.unidad_organizacional
                if unidad_usuario:
                    depto_principal = obtener_departamento_principal(unidad_usuario)
                    if depto_principal:
                        self.fields['departamento_solicitante'].initial = depto_principal

                # Cargar datos del técnico por defecto
                datos_tec = obtener_datos_tecnico_solicitante(user)
                self.fields['tecnico_nombre'].initial = datos_tec['nombre_completo']
                self.fields['tecnico_rut'].initial = datos_tec['rut']
                self.fields['tecnico_establecimiento'].initial = datos_tec['establecimiento']
                self.fields['tecnico_telefono'].initial = datos_tec['telefono']
                self.fields['tecnico_cargo'].initial = datos_tec['cargo']
                self.fields['tecnico_email'].initial = datos_tec['email']
                self.fields['tecnico_fecha'].initial = datos_tec['fecha']


class BeneficiarioVPNForm(forms.ModelForm):
    """
    Formulario individual para cada beneficiario dentro del FormSet.
    """
    funcionario = forms.ModelChoiceField(
        queryset=Funcionario.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm select2-funcionario select-func-existente',
            'data-placeholder': 'Buscar Funcionario...'
        }),
        label='Funcionario Existente'
    )
    rut = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm rut-input input-rut',
            'placeholder': 'Ej: 12.345.678-9'
        }),
        label='RUT'
    )
    nombres = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm input-nombres',
            'placeholder': 'Nombres'
        }),
        label='Nombres'
    )
    apellidos = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm input-apellidos',
            'placeholder': 'Apellidos'
        }),
        label='Apellidos'
    )
    nombre_completo = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm input-nombre-completo',
            'placeholder': 'Nombre Completo'
        }),
        label='Nombre Completo'
    )
    establecimiento = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm input-establecimiento',
            'placeholder': 'Establecimiento'
        }),
        label='Establecimiento'
    )
    cargo = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm input-cargo',
            'placeholder': 'Cargo'
        }),
        label='Cargo'
    )
    telefono = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm input-telefono',
            'placeholder': 'Teléfono'
        }),
        label='Teléfono'
    )
    email = forms.CharField(
        max_length=254,
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-sm input-email',
            'placeholder': 'Email'
        }),
        label='Email'
    )
    fecha = forms.DateField(
        required=False,
        initial=timezone.now,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-sm input-fecha',
            'type': 'date'
        }),
        label='Fecha'
    )

    class Meta:
        model = BeneficiarioVPN
        fields = [
            'funcionario',
            'rut',
            'nombres',
            'apellidos',
            'nombre_completo',
            'establecimiento',
            'cargo',
            'telefono',
            'email',
            'fecha',
        ]

    def clean(self):
        cleaned_data = super().clean()
        nombres = (cleaned_data.get('nombres') or '').strip()
        apellidos = (cleaned_data.get('apellidos') or '').strip()
        nombre_completo = (cleaned_data.get('nombre_completo') or '').strip()

        if not nombre_completo and (nombres or apellidos):
            cleaned_data['nombre_completo'] = f"{nombres} {apellidos}".strip()

        if not cleaned_data.get('fecha'):
            cleaned_data['fecha'] = timezone.now().date()

        return cleaned_data


class BaseBeneficiarioVPNFormSet(forms.BaseInlineFormSet):
    """
    FormSet para la gestión de beneficiarios con validación de al menos un beneficiario válido.
    """
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        valid_count = 0
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                rut = form.cleaned_data.get('rut')
                nombres = form.cleaned_data.get('nombres')
                if rut and nombres:
                    valid_count += 1
                elif form.cleaned_data.get('funcionario') or rut or nombres:
                    raise forms.ValidationError("Todos los beneficiarios deben tener al menos RUT y Nombres completos.")

        if valid_count == 0:
            raise forms.ValidationError("Debe ingresar al menos un beneficiario para la solicitud.")


BeneficiarioVPNFormSet = forms.inlineformset_factory(
    SolicitudVPN,
    BeneficiarioVPN,
    form=BeneficiarioVPNForm,
    formset=BaseBeneficiarioVPNFormSet,
    extra=1,
    can_delete=True
)


class AccesoSeleccionForm(forms.Form):
    """
    Formulario individual para seleccionar un acceso existente del mantenedor/catálogo.
    """
    acceso = forms.ModelChoiceField(
        queryset=AccesoVPN.objects.filter(is_active=True).order_by('plataforma', 'ip'),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm select2-acceso select-acceso-catalogo',
            'data-placeholder': 'Seleccione un acceso del mantenedor...'
        }),
        label='Acceso'
    )


class BaseSolicitudAccesoFormSet(forms.BaseFormSet):
    """
    FormSet para la selección de accesos con validación de no duplicados.
    """
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        accesos_vistos = set()
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                acceso = form.cleaned_data.get('acceso')
                if acceso:
                    if acceso.pk in accesos_vistos:
                        raise forms.ValidationError(
                            f"El acceso '{acceso}' ha sido seleccionado más de una vez. No se permiten accesos duplicados dentro de la misma solicitud."
                        )
                    accesos_vistos.add(acceso.pk)


SolicitudAccesoFormSet = forms.formset_factory(
    AccesoSeleccionForm,
    formset=BaseSolicitudAccesoFormSet,
    extra=1,
    can_delete=True
)


class AccesoVPNForm(forms.ModelForm):
    """
    Formulario mantenedor para el catálogo de accesos a sistemas e IPs.
    """
    class Meta:
        model = AccesoVPN
        fields = ['plataforma', 'ip']
        widgets = {
            'plataforma': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Sistema SIDRA, Intranet, etc.'
            }),
            'ip': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 10.8.85.25 o 10.8.85.0/24'
            }),
        }


class GestionTICSolicitudForm(forms.Form):
    """
    Formulario para la gestión de solicitudes VPN en Bandeja TIC.
    Permite cambiar estado, registrar ticket eConecta y observaciones.
    """
    estado = forms.ChoiceField(
        choices=SolicitudVPN.ESTADOS,
        required=True,
        label='Nuevo Estado',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    ticket_econecta = forms.CharField(
        max_length=100,
        required=False,
        label='Ticket / ID de Solicitud eConecta',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: REQ-2026-12345 o folio de eConecta'
        })
    )
    observacion_revision = forms.CharField(
        required=False,
        label='Observaciones de Revisión / Gestión TIC',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ingrese notas del proceso, motivos de rechazo o instrucciones de gestión...'
        })
    )


class FiltroSolicitudVPNForm(forms.Form):
    """
    Formulario de filtrado para listados y bandeja TIC de solicitudes VPN.
    """
    numero_solicitud = forms.CharField(
        required=False,
        label='Folio / Número',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ej: VPN-2026...'})
    )
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los estados')] + list(SolicitudVPN.ESTADOS),
        label='Estado',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    establecimiento = forms.ModelChoiceField(
        queryset=Establecimiento.objects.filter(is_active=True),
        required=False,
        label='Establecimiento',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    accion = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas las acciones')] + list(SolicitudVPN.ACCIONES),
        label='Acción',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    beneficiario_busqueda = forms.CharField(
        required=False,
        label='Beneficiario (RUT / Nombre)',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'RUT o nombre...'})
    )


class PerfilVPNForm(forms.ModelForm):
    """
    Formulario para gestionar el PerfilVPN de un usuario.
    """
    class Meta:
        model = PerfilVPN
        fields = [
            'bandeja_vpn',
            'nombre_completo',
            'rut',
            'establecimiento',
            'telefono',
            'cargo',
            'email'
        ]
        widgets = {
            'bandeja_vpn': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre Completo'}),
            'rut': forms.TextInput(attrs={'class': 'form-control rut-input', 'placeholder': 'RUT'}),
            'establecimiento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Establecimiento'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cargo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
        }
