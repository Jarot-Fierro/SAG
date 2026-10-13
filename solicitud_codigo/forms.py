from django import forms

from solicitud_codigo.models import (
    AreaSolicitud,
    SubareaSolicitud,
    SolicitudCodigo,
)


class SolicitudCodigoForm(forms.ModelForm):
    area = forms.ModelChoiceField(
        queryset=AreaSolicitud.objects.filter(is_active=True).order_by('nombre'),
        label="Área",
        empty_label="Seleccione un área",
        widget=forms.Select(attrs={
            'class': 'form-select form-control tom-select',
            'id': 'id_area',
        }),
        required=True
    )
    subarea = forms.ModelChoiceField(
        queryset=SubareaSolicitud.objects.filter(is_active=True).order_by('nombre'),
        label="Subárea",
        empty_label="Seleccione una subárea (opcional)",
        widget=forms.Select(attrs={
            'class': 'form-select form-control tom-select',
            'id': 'id_subarea',
        }),
        required=False
    )
    producto_base = forms.CharField(
        label="Producto Base",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Amoxicilina 500mg, Alcohol Gel 70%, Papel Bond Carta...',
            'id': 'id_producto_base',
            'autocomplete': 'off',
        }),
        required=True,
        help_text="Nombre genérico o descriptivo del bien/insumo solicitado."
    )
    presentacion = forms.CharField(
        label="Presentación",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Caja x 100 comprimidos, Frasco 1 Litro, Paquete 500 hojas...',
            'id': 'id_presentacion',
            'autocomplete': 'off',
        }),
        required=True,
        help_text="Formato, unidad de medida o empaque de presentación."
    )
    descripcion_requerimiento = forms.CharField(
        label="Descripción del Requerimiento",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describa detalladamente el producto requerido, uso clínico o administrativo, especificaciones técnicas y justificación...',
            'id': 'id_descripcion_requerimiento',
        }),
        required=True
    )
    antecedentes_complementarios = forms.CharField(
        label="Antecedentes Complementarios / Justificación",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Indique normativas, resoluciones, programas de salud asociados u otros antecedentes de respaldo (opcional)...',
            'id': 'id_antecedentes_complementarios',
        }),
        required=False
    )

    class Meta:
        model = SolicitudCodigo
        fields = [
            'area',
            'subarea',
            'producto_base',
            'presentacion',
            'descripcion_requerimiento',
            'antecedentes_complementarios',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'area' in self.data:
            try:
                area_id = int(self.data.get('area'))
                self.fields['subarea'].queryset = SubareaSolicitud.objects.filter(
                    area_id=area_id, is_active=True
                ).order_by('nombre')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.area:
            self.fields['subarea'].queryset = self.instance.area.subareas.filter(
                is_active=True
            ).order_by('nombre')


class SolicitudCodigoCorregirForm(SolicitudCodigoForm):
    """
    Formulario utilizado por el solicitante para corregir y reenviar una solicitud observada.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurar que subáreas correspondan al área inicial si no viene en POST
        if not self.is_bound and self.instance.pk and self.instance.area:
            self.fields['subarea'].queryset = SubareaSolicitud.objects.filter(
                area=self.instance.area, is_active=True
            ).order_by('nombre')


class ObservarSolicitudForm(forms.Form):
    observaciones = forms.CharField(
        label="Observaciones y Justificación de la Devolución",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describa las razones por las que se devuelve la solicitud y qué antecedentes debe corregir el solicitante...',
        }),
        required=True,
        min_length=5,
        help_text="Campo obligatorio. El solicitante verá este motivo para subsanar la solicitud."
    )


class RechazarSolicitudForm(forms.Form):
    motivo_rechazo = forms.CharField(
        label="Motivo del Rechazo",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Indique de forma clara y justificada el motivo del rechazo de la solicitud...',
        }),
        required=True,
        min_length=5,
        help_text="Campo obligatorio. El rechazo es definitivo."
    )


class ValidarSolicitudForm(forms.Form):
    observaciones = forms.CharField(
        label="Comentarios u Observaciones de Validación",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Comentarios adicionales sobre la validación de la solicitud (opcional)...',
        }),
        required=False
    )


class CrearCodigoEfectivoForm(forms.Form):
    codigo_creado = forms.CharField(
        label="Código SISSA Creado",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control font-monospace fw-bold',
            'placeholder': 'Ej: COD-SISSA-2026-00123',
            'autocomplete': 'off',
        }),
        required=True,
        help_text="Ingrese el código SISSA definitivo generado en la maestra institucional."
    )
    observaciones_creacion = forms.CharField(
        label="Observaciones de Cierre / Creación",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones o confirmación de la creación del código SISSA...',
        }),
        required=False
    )
    registrar_en_maestra = forms.BooleanField(
        label="Registrar también en la Maestra de Códigos de consulta rápida",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
