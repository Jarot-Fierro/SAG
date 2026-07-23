from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from core.models.establecimientos import Establecimiento

User = get_user_model()


class RegistroForm(forms.ModelForm):
    username = forms.CharField(
        label='RUT',
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'RUT'
            })
    )
    email = forms.EmailField(
        label='Correo',
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Correo'
            })
    )
    first_name = forms.CharField(
        label='Nombres',
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Nombres'
            })
    )
    last_name = forms.CharField(
        label='Apellidos',
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos'
            })
    )

    password = forms.CharField(
        label='Contraseña',
        required=True,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Contraseña'
            })
    )
    password_confirm = forms.CharField(
        label='Confirmar Contraseña',
        required=True,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Repetir Contraseña'
            })
    )
    establecimiento = forms.ModelChoiceField(
        required=True,
        queryset=Establecimiento.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Seleccione Establecimiento"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'establecimiento']

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        p2 = self.cleaned_data.get('password_confirm')
        if password and p2 and password != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username:
            username = username.upper()

            # Validación de RUT Chileno (Algoritmo Módulo 11)
            rut_limpio = username.replace(".", "").replace("-", "")
            if len(rut_limpio) < 2:
                raise ValidationError("El RUT no tiene un formato válido.")

            cuerpo = rut_limpio[:-1]
            dv = rut_limpio[-1]

            if not cuerpo.isdigit():
                raise ValidationError("El cuerpo del RUT debe contener solo números.")

            suma = 0
            multiplo = 2
            for c in reversed(cuerpo):
                suma += int(c) * multiplo
                multiplo = 2 if multiplo == 7 else multiplo + 1

            dv_esperado = 11 - (suma % 11)
            dv_real = '0' if dv_esperado == 11 else 'K' if dv_esperado == 10 else str(dv_esperado)

            if dv != dv_real:
                raise ValidationError("El RUT ingresado no es válido.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_active = False
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user
