from django import forms
from django.db.models import Q

from ..models.mantenedores import Contrato


class ContratoEquipoFormMixin:
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None) or getattr(self, 'request', None)
        super().__init__(*args, **kwargs)
        contratos = Contrato.objects.filter(Q(is_active=True) | Q(pk=self.instance.contrato_id))
        if request is not None and not request.user.is_superuser:
            contratos = contratos.filter(establecimiento_id=request.user.establecimiento_id) if request.user.establecimiento_id else contratos.none()
        self.fields['contrato'].queryset = contratos.order_by('nombre')
        self.fields['contrato'].widget = forms.Select(attrs={'class': 'form-select tom-select'})
        self.fields['contrato'].empty_label = 'Sin contrato'
