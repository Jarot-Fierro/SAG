from django import forms

from core.models.configuracion_correo import ConfiguracionCorreo


class ConfiguracionCorreoForm(forms.ModelForm):
    smtp_password = forms.CharField(
        label='Contraseña SMTP',
        widget=forms.PasswordInput(render_value=True),
        help_text='Ingrese la contraseña para la cuenta de correo SMTP. Se almacenará de forma cifrada.',
        required=False
    )

    class Meta:
        model = ConfiguracionCorreo
        fields = [
            'establecimiento',
            'nombre_remitente',
            'email_remitente',
            'smtp_host',
            'smtp_port',
            'smtp_tls',
            'smtp_ssl',
            'smtp_usuario',
            'smtp_password',
            'activo',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si el objeto ya existe, intentamos cargar la contraseña actual descifrada
        if self.instance and self.instance.pk:
            try:
                self.fields['smtp_password'].initial = self.instance.smtp_password
            except Exception:
                # Si falla el descifrado (p.ej. no estaba cifrada), dejamos el campo vacío o como esté
                pass

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Asignar la contraseña a través de la propiedad del modelo para que se cifre
        nueva_password = self.cleaned_data.get('smtp_password')
        if nueva_password:
            instance.smtp_password = nueva_password

        if commit:
            instance.save()
        return instance
