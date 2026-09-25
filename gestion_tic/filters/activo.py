from django import forms

from gestion_tic.models import Activo
from gestion_tic.models.catalogo import Marca, Modelo, Contrato
from gestion_tic.models.tipo_activo import TipoActivo


class ActivoFormFilter(forms.ModelForm):
    class Meta:
        model = Activo
        fields = [
            'codigo_barra', 'tipo',
            'marca', 'modelo', 'serie', 'contrato',
        ]

    def __init__(self, *args, **kwargs):
        establecimiento = kwargs.pop('establecimiento', None)
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.required = False
            field.widget.attrs.update({'class': 'form-control form-control-sm'})

        if 'codigo_barra' in self.fields:
            self.fields['codigo_barra'].widget.attrs.update({'placeholder': 'Código de barras'})
        if 'serie' in self.fields:
            self.fields['serie'].widget.attrs.update({'placeholder': 'Número de serie'})

        if 'tipo' in self.fields:
            self.fields['tipo'].empty_label = 'Todos los tipos'
            self.fields['tipo'].widget.attrs.update({'class': 'form-select form-select-sm'})
            if establecimiento:
                self.fields['tipo'].queryset = TipoActivo.objects.filter(establecimiento=establecimiento,
                                                                         is_active=True)
            else:
                self.fields['tipo'].queryset = TipoActivo.objects.filter(is_active=True)

        if 'marca' in self.fields:
            self.fields['marca'].empty_label = 'Todas las marcas'
            self.fields['marca'].widget.attrs.update({'class': 'form-select form-select-sm'})
            if establecimiento:
                self.fields['marca'].queryset = Marca.objects.filter(establecimiento=establecimiento, is_active=True)
            else:
                self.fields['marca'].queryset = Marca.objects.filter(is_active=True)

        if 'modelo' in self.fields:
            self.fields['modelo'].empty_label = 'Todos los modelos'
            self.fields['modelo'].widget.attrs.update({'class': 'form-select form-select-sm'})
            if establecimiento:
                self.fields['modelo'].queryset = Modelo.objects.filter(establecimiento=establecimiento, is_active=True)
            else:
                self.fields['modelo'].queryset = Modelo.objects.filter(is_active=True)

        if 'contrato' in self.fields:
            self.fields['contrato'].empty_label = 'Todos los contratos'
            self.fields['contrato'].widget.attrs.update({'class': 'form-select form-select-sm'})
            if establecimiento:
                self.fields['contrato'].queryset = Contrato.objects.filter(establecimiento=establecimiento,
                                                                           is_active=True)
            else:
                self.fields['contrato'].queryset = Contrato.objects.filter(is_active=True)
