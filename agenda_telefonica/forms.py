from django import forms

from agenda_telefonica.models import Anexo


class FormAnexo(forms.ModelForm):
    anexo = forms.CharField(
        label='Anexo',
        widget=forms.TextInput(
            attrs={
                'id': 'anexo',
                'class': 'form-control form-control-sm',
                'placeholder': 'Ej: 1234',
                'maxlength': '20'
            }
        ),
        required=True
    )

    anexo_publico = forms.CharField(
        label='Anexo Público',
        widget=forms.TextInput(
            attrs={
                'id': 'anexo_publico',
                'class': 'form-control form-control-sm',
                'placeholder': 'Ej: +56 41 2541201',
                'maxlength': '20'
            }
        ),
        required=False
    )

    nombre = forms.CharField(
        label='Nombre',
        widget=forms.TextInput(
            attrs={
                'id': 'nombre',
                'class': 'form-control form-control-sm',
                'placeholder': 'Nombre del funcionario',
                'maxlength': '255'
            }
        ),
        required=True
    )

    email = forms.EmailField(
        label='Correo Electrónico',
        widget=forms.EmailInput(
            attrs={
                'id': 'email',
                'class': 'form-control form-control-sm',
                'placeholder': 'correo@institucion.cl'
            }
        ),
        required=False
    )

    is_active = forms.BooleanField(
        label='¿Está Activo?',
        required=False,
        initial=True,
        widget=forms.Select(
            choices=[(True, 'Activo'), (False, 'Inactivo')],
            attrs={
                'id': 'is_active',
                'class': 'form-select form-select-sm'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        servicios_disponibles = kwargs.pop('servicios_disponibles', None)
        super().__init__(*args, **kwargs)

        if servicios_disponibles is not None:
            self.fields['servicio'].queryset = servicios_disponibles

    class Meta:
        model = Anexo
        fields = [
            'anexo',
            'anexo_publico',
            'nombre',
            'email',
            'servicio',
            'is_active',
        ]


class AnexoFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Búsqueda',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar por nombre, anexo o correo...',
            'hx-get': '/agenda/editor/buscar/',
            'hx-target': '#table-results',
            'hx-trigger': 'keyup changed delay:500ms, search',
        })
    )

    per_page = forms.ChoiceField(
        choices=[(10, '10'), (20, '20'), (50, '50'), (100, '100')],
        initial=10,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
            'hx-get': '/agenda/editor/buscar/',
            'hx-target': '#table-results',
            'hx-trigger': 'change',
            'name': 'per_page',
        })
    )

class MantenedorFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Búsqueda',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar...',
            'hx-get': './buscar/',  # Dinámico relativo a la URL actual
            'hx-trigger': 'keyup changed delay:500ms, search',
            'hx-target': '#table-results-mantenedor',
        })
    )
    per_page = forms.ChoiceField(
        choices=[(10, '10'), (20, '20'), (50, '50'), (100, '100')],
        initial=10,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
            'hx-get': './buscar/',  # Dinámico relativo a la URL actual
            'hx-trigger': 'change',
            'hx-target': '#table-results-mantenedor',
        })
    )
