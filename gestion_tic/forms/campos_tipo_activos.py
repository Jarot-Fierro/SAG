from django import forms
from django.forms import inlineformset_factory

from gestion_tic.models.campo_tipo_activo import CampoTipoActivo
from gestion_tic.models.tipo_activo import TipoActivo


class CamposTipoActivos(forms.Form):
    tipo_activo = forms.ModelChoiceField(
        empty_label='Seleccione un tipo de Activo',
        required=True,
        queryset=TipoActivo.objects.all(),
        widget=forms.Select(
            attrs={
                'class': 'form-select select2',
                'onchange': 'location = "?tipo=" + this.value;'
            }
        ),
    )


class CampoTipoActivoForm(forms.ModelForm):
    class Meta:
        model = CampoTipoActivo
        fields = ['nombre', 'tipo_campo', 'obligatorio', 'orden']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_campo': forms.Select(attrs={'class': 'form-select'}),
            'obligatorio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
        }


CampoTipoActivoFormSet = inlineformset_factory(
    TipoActivo,
    CampoTipoActivo,
    form=CampoTipoActivoForm,
    extra=0,
    can_delete=True
)
