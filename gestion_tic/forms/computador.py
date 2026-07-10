from django import forms
from django.core.exceptions import ValidationError

from core.models import User
from gestion_tic.models.catalogo import (
    Marca,
    Modelo,
    TipoComputador,
    SistemaOperativo,
    MicrosoftOffice, Propietario, JefeTic, Contrato, Ips
)
from gestion_tic.models.equipos import AsignacionIP, Equipo


class IPModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Verificar si tiene una asignación activa
        asignada = hasattr(obj, 'asignacion_ip') and obj.asignacion_ip.activa
        if asignada:
            return f"{obj.ip} - [ASIGNADA]"
        return f"{obj.ip} - [LIBRE]"


class FormComputador(forms.ModelForm):
    serie = forms.CharField(
        label='Número de Serie',
        widget=forms.TextInput(
            attrs={
                'id': 'serie',
                'class': 'form-control form-control-sm',
                'placeholder': 'Ingrese número de serie',
            }
        ),
        required=True
    )

    mac = forms.CharField(
        label='Dirección MAC',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control form-control-sm mac-address',
                'placeholder': 'Ej: 00:1A:2B:3C:4D:5E',
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
                'class': 'form-control form-control-sm select2',
                'placeholder': 'Ej: 192.168.1.10',
            }
        )
    )

    marca = forms.ModelChoiceField(
        label='Marca',
        queryset=Marca.objects.all(),
        required=True,
        widget=forms.Select(
            attrs={
                'class': 'form-control form-control-sm select2'
            }
        )
    )

    modelo = forms.ModelChoiceField(
        label='Modelo',
        queryset=Modelo.objects.all(),
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'form-control form-control-sm select2'
            }
        )
    )

    tipo_pc = forms.ModelChoiceField(
        label='Tipo de Computador',
        queryset=TipoComputador.objects.all(),
        required=True,
        widget=forms.Select(
            attrs={
                'class': 'form-control form-control-sm select2'
            }
        )
    )

    sistema_operativo = forms.ModelChoiceField(
        label='Sistema Operativo',
        queryset=SistemaOperativo.objects.all(),
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'form-control form-control-sm select2'
            }
        )
    )

    microsoft_office = forms.ModelChoiceField(
        label='Microsoft Office',
        queryset=MicrosoftOffice.objects.all(),
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'form-control form-control-sm select2'
            }
        )
    )

    propietario = forms.ModelChoiceField(
        label='Propietario',
        queryset=Propietario.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-sm select2'
        })
    )

    jefe_entrega = forms.ModelChoiceField(
        label='Jefe que Entrega',
        queryset=JefeTic.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-sm'
        })
    )

    responsable = forms.ModelChoiceField(
        label='Responsable',
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-sm select2'
        })
    )

    contrato = forms.ModelChoiceField(
        label='Contrato',
        queryset=Contrato.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-sm select2'
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
            'class': 'form-control form-control-sm',
            'rows': 3
        }),
        required=False
    )

    motivo_baja = forms.CharField(
        label='Motivo de Baja',
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-sm',
            'rows': 3
        }),
        required=False
    )

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

    ram_gb = forms.CharField(label='RAM (GB)', required=False,
                             widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'}))
    procesador = forms.CharField(label='Procesador', required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'}))
    tarjeta_video = forms.CharField(label='Tarjeta de Video', required=False,
                                    widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'}))
    wifi = forms.CharField(label='WiFi', required=False,
                           widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'}))
    red_lan = forms.CharField(label='Red LAN', required=False,
                              widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'}))
    tipo_disco = forms.ChoiceField(label='Tipo de Disco',
                                   choices=[('', '---------'), ('SSD', 'SSD'), ('HDD', 'Mecánico'), ('NVME', 'NVMe')],
                                   required=False, widget=forms.Select(attrs={'class': 'form-control form-control-sm'}))
    capacidad_disco_gb = forms.IntegerField(label='Capacidad Disco (GB)', required=False,
                                            widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'}))

    class Meta:
        model = Equipo
        fields = [
            'serie',
            'mac',
            'ip',
            'marca',
            'modelo',
            'tipo_pc',
            'sistema_operativo',
            'microsoft_office',
            'propietario',
            'jefe_entrega',
            'responsable',
            'contrato',
            'de_baja',
            'motivo_baja',
            'observaciones',
            'es_armado',
            'ram_gb',
            'procesador',
            'tarjeta_video',
            'wifi',
            'red_lan',
            'tipo_disco',
            'capacidad_disco_gb',
        ]
