from django import forms

from soporte.models import AreaSoporte


class FiltroTicket(forms.Form):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)

        if request:
            establecimiento = request.user.establecimiento
            self.fields["area_soporte"].queryset = AreaSoporte.objects.filter(
                establecimiento=establecimiento,
                is_active=True
            )

    ESTADOS = (
        ('', 'Todos los Estados'),
        ('ABIERTO', 'Abierto'),
        ('EN_PROCESO', 'En Proceso'),
        ('ESPERA', 'En Espera'),
        ('CERRADO', 'Cerrado'),
        ('RECHAZADO', 'Rechazado'),
    )

    numero_ticket = forms.CharField(
        label='Número de Ticket',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número'
        }),
        required=False
    )
    titulo = forms.CharField(
        label='Título',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Título'
        }),
        required=False
    )

    area_soporte = forms.ModelChoiceField(
        queryset=AreaSoporte.objects.none(),
        empty_label='Todas las áreas',
        label='Área',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=False
    )

    estado = forms.ChoiceField(
        choices=ESTADOS,
        label='Estado',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=False
    )
