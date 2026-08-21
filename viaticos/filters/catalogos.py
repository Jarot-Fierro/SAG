from django import forms


class FiltroLugarDestino(forms.Form):
    codigo = forms.CharField(
        label='Código',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código'
        }),
        required=False
    )
    nombre = forms.CharField(
        label='Nombre / Ciudad',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre o ciudad'
        }),
        required=False
    )
    region = forms.CharField(
        label='Región',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Región'
        }),
        required=False
    )
    comuna = forms.CharField(
        label='Comuna',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Comuna'
        }),
        required=False
    )


class FiltroEscalaViatico(forms.Form):
    ano_vigencia = forms.IntegerField(
        label='Año',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Año'
        }),
        required=False
    )
    grado = forms.CharField(
        label='Grado',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Grado'
        }),
        required=False
    )
    estamento = forms.CharField(
        label='Estamento',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Estamento'
        }),
        required=False
    )


class FiltroVistoLegal(forms.Form):
    codigo = forms.CharField(
        label='Código',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código'
        }),
        required=False
    )
    corresponde_a = forms.CharField(
        label='Tipo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tipo / Cometido / Viático'
        }),
        required=False
    )
    q = forms.CharField(
        label='Buscar en texto',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar...'
        }),
        required=False
    )
