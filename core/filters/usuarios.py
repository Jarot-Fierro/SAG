from django import forms


class FiltroUsuarios(forms.Form):
    username = forms.CharField(
        label="RUT",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'RUT',
        }),
    )

    first_name = forms.CharField(
        label="Nombres",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombres',
        }),
    )

    last_name = forms.CharField(
        label="Apellidos",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellidos',
        }),
    )
    email = forms.CharField(
        label="Correo",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo',
        }),
    )
