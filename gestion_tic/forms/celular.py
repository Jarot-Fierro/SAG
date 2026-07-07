from django import forms
from django.contrib.auth.models import User

from core.models import Departamento
from gestion_tic.models.catalogo import Marca, Modelo, TipoCelular, Propietario, JefeTic, Contrato
from gestion_tic.models.celular import Celular


class FormCelular(forms.ModelForm):
    imei = forms.CharField(
        label='IMEI',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese IMEI del equipo'
        }),
        required=True
    )

    numero_telefono = forms.CharField(
        label='Número de Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'form-control telefono_personal',
            'placeholder': 'Ej: 912345678'
        }),
        required=True
    )

    numero_chip = forms.CharField(
        label='Número de Chip',
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        }),
        required=False
    )

    pin = forms.CharField(
        label='PIN',
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        }),
        required=False
    )

    puk = forms.CharField(
        label='PUK',
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        }),
        required=False
    )

    minutos = forms.CharField(
        label='Minutos',
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        }),
        required=False
    )

    minsal = forms.BooleanField(
        label='¿Plan MINSAL?',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    de_baja = forms.BooleanField(
        label='¿Equipo dado de baja?',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    motivo_baja = forms.CharField(
        label='Motivo de Baja',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        }),
        required=False
    )

    observaciones = forms.CharField(
        label='Observaciones',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        }),
        required=False
    )

    marca = forms.ModelChoiceField(
        label='Marca',
        queryset=Marca.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=True
    )

    modelo = forms.ModelChoiceField(
        label='Modelo',
        queryset=Modelo.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=False
    )

    tipo = forms.ModelChoiceField(
        label='Tipo de Celular',
        queryset=TipoCelular.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=False
    )

    propietario = forms.ModelChoiceField(
        label='Propietario',
        queryset=Propietario.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=False
    )

    departamento = forms.ModelChoiceField(
        label='Departamento',
        queryset=Departamento.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=False
    )

    jefe_entrega = forms.ModelChoiceField(
        label='Jefe que Entrega',
        queryset=JefeTic.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=False
    )

    responsable = forms.ModelChoiceField(
        label='Responsable',
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=False
    )

    contrato = forms.ModelChoiceField(
        label='Contrato',
        queryset=Contrato.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=False
    )

    class Meta:
        model = Celular
        fields = [
            'imei',
            'numero_telefono',
            'numero_chip',
            'pin',
            'puk',
            'minutos',
            'marca',
            'modelo',
            'tipo',
            'propietario',
            'departamento',
            'jefe_entrega',
            'responsable',
            'contrato',
            'minsal',
            'de_baja',
            'motivo_baja',
            'observaciones',
        ]
