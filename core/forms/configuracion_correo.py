from django import forms

from core.models.configuracion_correo import ConfiguracionCorreo


class ConfiguracionCorreoForm(forms.ModelForm):
    nombre_remitente = forms.CharField(
        label='Nombre del Remitente',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del remitente'
            }
        ),
        required=True
    )
    email_remitente = forms.EmailField(
        label='Correo del Remitente',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Correo del remitente'
            }
        ),
        required=True
    )
    smtp_host = forms.CharField(
        label='Servidor SMTP',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Servidor SMTP'
            }
        ),
    )
    smtp_port = forms.IntegerField(
        label='Puerto SMTP',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Puerto SMTP'
            }
        ),
    )
    smtp_tls = forms.BooleanField(
        label='Usar TLS',
        widget=forms.CheckboxInput(
            attrs={
                'class': 'form-check-input'
            }
        ),
        required=False
    )
    smtp_ssl = forms.BooleanField(
        label='Usar SSL',
        widget=forms.CheckboxInput(
            attrs={
                'class': 'form-check-input'
            }
        ),
        required=False
    )
    smtp_usuario = forms.CharField(
        label='Usuario SMTP',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Usuario SMTP'
            }
        ),
    )
    activo = forms.BooleanField(
        label='Activo',
        widget=forms.CheckboxInput(
            attrs={
                'class': 'form-check-input'
            }
        ),
        required=False
    )
    smtp_password = forms.CharField(
        label='Contraseña SMTP',
        widget=forms.PasswordInput(
            render_value=True,
            attrs={
                'class': 'form-control',
            }),
        help_text='Ingrese la contraseña para la cuenta de correo SMTP. Se almacenará de forma cifrada.',
        required=False
    )

    class Meta:
        model = ConfiguracionCorreo
        fields = [
            'nombre_remitente',
            'email_remitente',
            'smtp_host',
            'smtp_port',
            'smtp_usuario',
            'smtp_password',
            'smtp_tls',
            'smtp_ssl',
            'activo',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # Si el objeto ya existe, intentamos cargar la contraseña actual descifrada
        if self.instance and self.instance.pk:
            try:
                self.fields['smtp_password'].initial = self.instance.smtp_password
            except Exception:
                # Si falla el descifrado (p.ej. no estaba cifrada), dejamos el campo vacío o como esté
                pass

    def clean(self):
        cleaned_data = super().clean()
        if self.user and not self.instance.pk:
            # Solo validamos si es una creación nueva
            if ConfiguracionCorreo.objects.filter(establecimiento=self.user.establecimiento).exists():
                raise forms.ValidationError(
                    "Ya existe una configuración de correo para su establecimiento. Por favor, edite la existente."
                )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Asignar la contraseña a través de la propiedad del modelo para que se cifre
        nueva_password = self.cleaned_data.get('smtp_password')
        if nueva_password:
            instance.smtp_password = nueva_password

        if commit:
            instance.save()
        return instance
