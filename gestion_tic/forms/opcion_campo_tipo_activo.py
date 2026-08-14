from django import forms

from gestion_tic.models.campo_tipo_activo import CampoTipoActivo
from gestion_tic.models.opcion_campo_tipo_activo import OpcionCampoTipoActivo


class OpcionCampoTipoActivoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.fields['campo'].queryset = CampoTipoActivo.objects.filter(
            establecimiento=self.request.user.establecimiento)

    nombre = forms.CharField(
        label='Nombre de la opción',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Láser, Térmica, etc.',
                'minlength': '1',
                'maxlength': '100'
            }),
        required=True
    )
    campo = forms.ModelChoiceField(
        label='Campo al que pertenece',
        queryset=CampoTipoActivo.objects.none(),
        widget=forms.Select(
            attrs={
                'class': 'form-select select2',
            }),
        required=True
    )
    orden = forms.IntegerField(
        label='Orden',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
            }),
        initial=0,
        required=False
    )

    class Meta:
        model = OpcionCampoTipoActivo
        fields = ['nombre', 'campo', 'orden']
