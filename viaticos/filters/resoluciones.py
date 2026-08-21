from django import forms


class FiltroResolucionCometido(forms.Form):
    numero_resolucion = forms.IntegerField(
        label='N° Resolución',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'N° Resolución'
        }),
        required=False
    )

    ano_resolucion = forms.IntegerField(
        label='Año',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Año'
        }),
        required=False
    )

    firmante = forms.CharField(
        label='Firmante',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre firmante'
        }),
        required=False
    )

    fecha_desde = forms.DateField(
        label='Desde',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )

    fecha_hasta = forms.DateField(
        label='Hasta',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )
