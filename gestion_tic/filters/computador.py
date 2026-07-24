from django import forms

from gestion_tic.models.catalogo import TipoComputador, Marca


class ComputadorFilter(forms.Form):
    tipo_pc = forms.ModelChoiceField(
        label='Tipo de Computador',
        queryset=TipoComputador.objects.all(),
        required=False,
        empty_label='Todos los tipos',
        widget=forms.Select(attrs={'class': 'form-control select2'}),
    )
    marca = forms.ModelChoiceField(
        label='Marca',
        queryset=Marca.objects.all(),
        required=False,
        empty_label='Todas las marcas',
        widget=forms.Select(attrs={'class': 'form-control select2'}),
    )
    serie = forms.CharField(
        label='Serie',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Serie...'}),
    )
    ip = forms.CharField(
        label='IPs',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección IP...'}),
    )
