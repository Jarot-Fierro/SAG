from django import forms
from django.utils import timezone

from core.models.funcionario import Funcionario
from core.models.unidad_organizacional import UnidadOrganizacional
from solicitud_correo.models import SolicitudCorreo, SolicitudCorreoDetalle


class SolicitudCorreoForm(forms.ModelForm):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        deptos_qs = UnidadOrganizacional.objects.filter(is_active=True)
        if request and hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            deptos_qs = deptos_qs.filter(establecimiento=request.user.establecimiento, es_departamento=True)
            # Intentar seleccionar por defecto el departamento del usuario si lo tiene
            if not self.instance.pk and hasattr(request.user, 'funcionario') and request.user.funcionario:
                if request.user.funcionario.unidad_organizacional:
                    self.initial['departamento_solicitante'] = request.user.funcionario.unidad_organizacional

        self.fields['departamento_solicitante'].queryset = deptos_qs

    departamento_solicitante = forms.ModelChoiceField(
        queryset=UnidadOrganizacional.objects.none(),
        label='Departamento Solicitante',
        empty_label='Seleccione un departamento',
        widget=forms.Select(attrs={'class': 'form-control form-select tom-select'}),
        required=True
    )
    observacion = forms.CharField(
        label='Observaciones / Justificación de la Solicitud',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Indique motivo o información adicional relevante...'
        }),
        required=False
    )

    class Meta:
        model = SolicitudCorreo
        fields = [
            'departamento_solicitante',
            'observacion',
        ]


class SolicitudCorreoDetalleForm(forms.ModelForm):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        func_qs = Funcionario.objects.filter(is_active=True).order_by('nombres', 'apellidos')
        if request and hasattr(request.user, 'establecimiento') and request.user.establecimiento:
            func_qs = func_qs.filter(establecimiento=request.user.establecimiento)
        self.fields['funcionario'].queryset = func_qs

    funcionario = forms.ModelChoiceField(
        queryset=Funcionario.objects.none(),
        label='Seleccionar Funcionario Existente (Opcional)',
        empty_label='-- Ingreso Manual / Seleccionar de la lista --',
        widget=forms.Select(attrs={'class': 'form-control form-select select2 funcionario-select'}),
        required=False
    )
    rut = forms.CharField(
        label='RUT',
        widget=forms.TextInput(attrs={'class': 'form-control rut-input', 'placeholder': 'Ej: 12.345.678-9'}),
        required=True
    )
    nombres = forms.CharField(
        label='Nombres',
        widget=forms.TextInput(attrs={'class': 'form-control nombres-input', 'placeholder': 'Ej: Juan Andrés'}),
        required=True
    )
    apellidos = forms.CharField(
        label='Apellidos',
        widget=forms.TextInput(attrs={'class': 'form-control apellidos-input', 'placeholder': 'Ej: Pérez Soto'}),
        required=True
    )
    departamento = forms.CharField(
        label='Departamento / Unidad',
        widget=forms.TextInput(attrs={'class': 'form-control depto-input', 'placeholder': 'Ej: Finanzas'}),
        required=False
    )
    cargo = forms.CharField(
        label='Cargo',
        widget=forms.TextInput(attrs={'class': 'form-control cargo-input', 'placeholder': 'Ej: Administrativo'}),
        required=False
    )

    class Meta:
        model = SolicitudCorreoDetalle
        fields = [
            'funcionario',
            'rut',
            'nombres',
            'apellidos',
            'departamento',
            'cargo',
        ]


class RevisionDetalleRRHHForm(forms.Form):
    ACCION_CHOICES = (
        ('APROBADO_RRHH', 'Aprobar Solicitud de Correo'),
        ('RECHAZADO_RRHH', 'Rechazar Solicitud de Correo'),
    )

    accion = forms.ChoiceField(
        choices=ACCION_CHOICES,
        label='Decisión de RR.HH.',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    motivo_rechazo = forms.CharField(
        label='Motivo del Rechazo',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Obligatorio en caso de rechazo. Explique el motivo...'
        }),
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        accion = cleaned_data.get('accion')
        motivo = cleaned_data.get('motivo_rechazo')

        if accion == 'RECHAZADO_RRHH' and not (motivo and motivo.strip()):
            self.add_error('motivo_rechazo', 'Debe indicar el motivo del rechazo.')

        return cleaned_data


class ProcesamientoDetalleTICForm(forms.Form):
    ACCION_CHOICES = (
        ('CREADO', 'Confirmar Creación de Cuenta (Exitosa)'),
        ('ERROR', 'Registrar Error o Inconveniente en Creación'),
    )

    accion = forms.ChoiceField(
        choices=ACCION_CHOICES,
        label='Resultado del Procesamiento TIC',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    correo_creado = forms.CharField(
        label='Correo Electrónico Creado',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: juan.perez@redsalud.gob.cl'
        }),
        required=False
    )
    fecha_creacion = forms.DateTimeField(
        label='Fecha / Hora de Creación Externa',
        initial=timezone.now,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }, format='%Y-%m-%dT%H:%M'),
        required=False
    )
    referencia_externa = forms.CharField(
        label='Referencia / N° Solicitud Externa MINSAL',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: TCK-MINSAL-12345'
        }),
        required=False
    )
    observacion_tic = forms.CharField(
        label='Observaciones Técnicas TIC',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones del técnico o detalles del error...'
        }),
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        accion = cleaned_data.get('accion')
        correo = cleaned_data.get('correo_creado')
        obs = cleaned_data.get('observacion_tic')

        if accion == 'CREADO':
            if not correo or not correo.strip():
                self.add_error('correo_creado', 'Debe indicar el correo electrónico creado.')
        elif accion == 'ERROR':
            if not obs or not obs.strip():
                self.add_error('observacion_tic', 'Debe detallar el motivo del error o inconveniente en la observación.')

        return cleaned_data


class NotificacionFuncionarioForm(forms.Form):
    correo_destinatario = forms.CharField(
        label='Correo Destinatario de la Notificación',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: correo.personal@gmail.com o jefatura@redsalud.gob.cl'
        }),
        required=False
    )
    observacion_notificacion = forms.CharField(
        label='Observaciones / Registro de Notificación',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ej: Notificado presencialmente / Notificado vía telefónica / Correo enviado...'
        }),
        required=False
    )
    enviar_email = forms.BooleanField(
        label='Intentar enviar correo electrónico automático al destinatario',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class FiltroSolicitudForm(forms.Form):
    numero_solicitud = forms.CharField(
        label='N° Folio',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar por Folio...'
        })
    )
    estado = forms.ChoiceField(
        label='Estado',
        required=False,
        choices=[('', 'Todos los Estados')] + list(SolicitudCorreo.ESTADOS),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    funcionario_busqueda = forms.CharField(
        label='Funcionario (RUT o Nombre)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'RUT o Nombre...'
        })
    )
