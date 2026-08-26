from django import forms

from core.models import User, Establecimiento
from soporte.models import Ticket, AreaSoporte, TipoSoporte, PerfilSoporte


class FormTicket(forms.ModelForm):

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)

        if request:
            self.fields["area_soporte"].queryset = AreaSoporte.objects.filter(
                establecimiento=request.user.establecimiento
            )

    titulo = forms.CharField(
        label='Título del problema',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Problema con impresora'
        }),
        required=True
    )

    descripcion = forms.CharField(
        label='Descripción del problema',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describa el problema que está presentando'
        }),
        required=False
    )

    area_soporte = forms.ModelChoiceField(
        queryset=AreaSoporte.objects.all(),
        label='¿Para que área quieres mandar este soporte?',
        empty_label='Selecciona una opción',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    class Meta:
        model = Ticket
        fields = [
            'titulo',
            'area_soporte',
            'descripcion',
        ]


class FormTicketEditor(forms.ModelForm):

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)

        if request:
            self.fields["area_soporte"].queryset = AreaSoporte.objects.filter(
                establecimiento=request.user.establecimiento
            )
            self.fields["tipo_soporte"].queryset = TipoSoporte.objects.filter(
                establecimiento=request.user.establecimiento
            )
            if not request.user.is_superuser and request.user.establecimiento:
                asignado_qs = PerfilSoporte.objects.filter(
                    usuario__establecimiento=request.user.establecimiento,
                    is_active=True
                )
                if self.instance and self.instance.asignado_a_id:
                    asignado_qs = (
                            asignado_qs | PerfilSoporte.objects.filter(pk=self.instance.asignado_a_id)).distinct()
                self.fields["asignado_a"].queryset = asignado_qs.select_related('usuario')
            else:
                self.fields["asignado_a"].queryset = PerfilSoporte.objects.filter(
                    is_active=True
                ).select_related('usuario')

        if self.instance and self.instance.pk:
            if self.instance.funcionario:
                self.fields['funcionario'].queryset = User.objects.filter(pk=self.instance.funcionario.pk)
                # Intentar obtener el departamento del funcionario si existe la propiedad o relación
                if hasattr(self.instance.funcionario, 'departamento'):
                    self.initial['departamento'] = self.instance.funcionario.departamento
                elif hasattr(self.instance.funcionario, 'unidad_organizacional'):
                    self.initial['departamento'] = self.instance.funcionario.unidad_organizacional

    numero_ticket = forms.CharField(
        label='N° Ticket',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'disabled': True
        }),
        required=False
    )

    establecimiento = forms.ModelChoiceField(
        queryset=Establecimiento.objects.all(),
        label='Establecimiento',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'disabled': True
        }),
        required=False
    )

    titulo = forms.CharField(
        label='Título del problema',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Problema con impresora'
        }),
        required=True
    )

    descripcion = forms.CharField(
        label='Descripción del problema',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describa el problema que está presentando'
        }),
        required=False
    )

    solucion = forms.CharField(
        label='Solución',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describa la solución brindada'
        }),
        required=False
    )

    estado = forms.ChoiceField(
        label='Estado',
        choices=Ticket.ESTADOS,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=True
    )

    area_soporte = forms.ModelChoiceField(
        queryset=AreaSoporte.objects.all(),
        label='Área del Soporte',
        empty_label='Selecciona una opción',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=True
    )

    funcionario = forms.ModelChoiceField(
        label='Funcionario solicitante',
        queryset=User.objects.none(),
        empty_label='Seleccione un funcionario',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'disabled': True
        }),
        required=True
    )

    asignado_a = forms.ModelChoiceField(
        label='Asignado a',
        empty_label='Seleccione a un responsable',
        queryset=PerfilSoporte.objects.filter(is_active=True).select_related('usuario'),
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
        }),
        required=False
    )

    tipo_soporte = forms.ModelChoiceField(
        queryset=TipoSoporte.objects.all(),
        label='Tipo de Soporte',
        empty_label='Seleccione un tipo de soporte',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        }),
        required=False
    )

    fecha_cierre = forms.DateTimeField(
        label='Fecha de cierre',
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }, format='%Y-%m-%dT%H:%M'),
        required=False
    )

    class Meta:
        model = Ticket
        fields = [
            'numero_ticket',
            'establecimiento',
            'titulo',
            'funcionario',
            'area_soporte',
            'estado',
            'asignado_a',
            'tipo_soporte',
            'fecha_cierre',
            'descripcion',
            'solucion',
        ]
