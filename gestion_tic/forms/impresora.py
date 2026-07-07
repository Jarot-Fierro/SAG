from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from catalogo import TipoImpresora, Marca, Modelo, Contrato, JefeTic, Propietario, Ips, Toner, validate_exists
from core.models import Departamento
from gestion_tic.models.equipos import Equipo, AsignacionIP


class IPModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Verificar si tiene una asignación activa
        asignada = hasattr(obj, 'asignacion_ip') and obj.asignacion_ip.activa
        if asignada:
            return f"{obj.ip} - [ASIGNADA]"
        return f"{obj.ip} - [LIBRE]"


class FormImpresora(forms.ModelForm):
    serie = forms.CharField(
        label='Número de Serie',
        widget=forms.TextInput(
            attrs={
                'id': 'serie',
                'class': 'form-control',
                'placeholder': 'Ingrese número de serie',
            }
        ),
        required=True
    )

    hh = forms.CharField(
        label='HH',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese código HH',
            }
        ),
        required=False
    )

    ip = IPModelChoiceField(
        label='Dirección IP',
        queryset=Ips.objects.all().select_related('asignacion_ip').order_by('ip'),
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'form-control select2',
                'placeholder': 'Ej: 192.168.1.10',
            }
        )
    )

    tipo_impresora = forms.ModelChoiceField(
        label='Tipo de Impresora',
        queryset=TipoImpresora.objects.all(),
        required=True,
        widget=forms.Select(
            attrs={
                'class': 'form-control select2'
            }
        )
    )

    marca = forms.ModelChoiceField(
        label='Marca',
        queryset=Marca.objects.all(),
        required=True,
        widget=forms.Select(
            attrs={
                'class': 'form-control select2'
            }
        )
    )

    modelo = forms.ModelChoiceField(
        label='Modelo',
        queryset=Modelo.objects.all(),
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'form-control select2'
            }
        )
    )

    toner = forms.ModelChoiceField(
        label='Tóner / Tinta',
        queryset=Toner.objects.all(),
        required=True,
        widget=forms.Select(
            attrs={
                'class': 'form-control select2'
            }
        )
    )

    propietario = forms.ModelChoiceField(
        label='Propietario',
        queryset=Propietario.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control select2'
        })
    )

    departamento = forms.ModelChoiceField(
        label='Departamento',
        queryset=Departamento.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control select2'
        })
    )

    jefe_entrega = forms.ModelChoiceField(
        label='Jefe que Entrega',
        queryset=JefeTic.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control select2'
        })
    )

    responsable = forms.ModelChoiceField(
        label='Responsable',
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control select2'
        })
    )

    contrato = forms.ModelChoiceField(
        label='Contrato',
        queryset=Contrato.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control select2'
        })
    )

    de_baja = forms.BooleanField(
        label='¿Equipo dado de baja?',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    observaciones = forms.CharField(
        label='Observaciones',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        }),
        required=False
    )

    motivo_baja = forms.CharField(
        label='Motivo de Baja',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        }),
        required=False
    )

    def clean_serie(self):
        serie = self.cleaned_data['serie'].strip()
        current_instance = self.instance if self.instance.pk else None

        exists = Equipo.objects.filter(serie__iexact=serie).exclude(
            pk=current_instance.pk if current_instance else None
        ).exists()

        validate_exists(serie, exists)
        return serie

    def clean_ip(self):
        ip = self.cleaned_data.get('ip')

        # Si hay una IP seleccionada, verificar si ya está asignada a OTRO equipo en AsignacionIP
        if ip:
            asignacion = AsignacionIP.objects.filter(ip=ip, activa=True).exclude(
                equipo=self.instance if self.instance.pk else None
            ).exists()

            if asignacion:
                raise ValidationError('La dirección IP ya está asignada a otro equipo.')

        return ip

    class Meta:
        model = Equipo
        fields = [
            'serie',
            'hh',
            'ip',
            'tipo_impresora',
            'marca',
            'modelo',
            'toner',
            'propietario',
            'departamento',
            'jefe_entrega',
            'responsable',
            'contrato',
            'de_baja',
            'motivo_baja',
            'observaciones',
        ]
