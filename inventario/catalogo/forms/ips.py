from django import forms

from catalogo.models import Ips
from core.validations import validate_exists


class FormIps(forms.ModelForm):
    ip = forms.GenericIPAddressField(
        label='Dirección IP',
        protocol='IPv4',
        widget=forms.TextInput(
            attrs={
                'id': 'ip_ip',
                'class': 'form-control',
                'placeholder': '192.168.0.1',
                'minlength': '7',
                'maxlength': '15'
            }
        ),
        required=True
    )

    establecimiento = forms.ModelChoiceField(
        label='Establecimiento',
        queryset=None,
        required=False,
        empty_label='Seleccione un establecimiento',
        widget=forms.Select(
            attrs={
                'id': 'ip_establecimiento',
                'class': 'form-control'
            }
        )
    )

    departamento = forms.ModelChoiceField(
        label='Departamento',
        queryset=None,
        required=False,
        empty_label='Seleccione un departamento',
        widget=forms.Select(
            attrs={
                'id': 'ip_departamento',
                'class': 'form-control'
            }
        )
    )

    observacion = forms.CharField(
        label='Observación',
        required=False,
        widget=forms.Textarea(
            attrs={
                'id': 'ip_observacion',
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ingrese una observación (opcional)'
            }
        )
    )

    class Meta:
        model = Ips
        fields = [
            'ip',
            'asignado',
            'establecimiento',
            'departamento',
            'observacion',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['establecimiento'].queryset = self._meta.model._meta.get_field(
            'establecimiento').related_model.objects.all().order_by('nombre')
        self.fields['departamento'].queryset = self._meta.model._meta.get_field(
            'departamento').related_model.objects.all().order_by('nombre')

    def clean_ip(self):
        ip = self.cleaned_data['ip']
        current_instance = self.instance if self.instance.pk else None

        exists = Ips.objects.filter(ip__iexact=ip).exclude(
            pk=current_instance.pk if current_instance else None
        ).exists()

        validate_exists(ip, exists)
        return ip
