from django import forms
from django.contrib.auth.password_validation import validate_password


class RecuperacionPasswordForm(forms.Form):
    rut = forms.CharField(
        label='RUT',
        max_length=12,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su RUT (sin puntos y con guion)',
            'required': True,
            'autofocus': True
        })
    )

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        # Limpieza básica del RUT si es necesario (ej: remover puntos)
        if rut:
            rut = rut.replace('.', '').upper()
        return rut


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        label='Nueva Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'required': True}),
        validators=[validate_password]
    )
    confirm_password = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'required': True})
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "Las contraseñas no coinciden.")

        return cleaned_data
