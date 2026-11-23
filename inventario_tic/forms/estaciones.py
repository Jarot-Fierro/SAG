from django import forms
from django.forms import BaseFormSet, formset_factory

from .computadores import FormComputador, FormRecepcionComputador
from .monitores import FormMonitor
from .productos import FormProducto
from ..models import Computador, Monitor, Producto


def visibles(model, user):
    qs = model.objects.filter(is_active=True)
    return qs if user.is_superuser else qs.filter(establecimiento_id=user.establecimiento_id) if user.establecimiento_id else qs.none()


def preparar(form, user):
    """Prefijos también en IDs; restringe catálogos sin cambiar los formularios originales."""
    for name, field in form.fields.items():
        field.widget.attrs['id'] = form.add_prefix(name)
        if isinstance(field, forms.ModelChoiceField):
            field.queryset = field.queryset.filter(pk__in=visibles(field.queryset.model, user).values('pk'))
    return form


class DestinoEstacionForm(FormRecepcionComputador):
    def __init__(self, *args, request, **kwargs):
        super().__init__(*args, request=request, **kwargs)
        preparar(self, request.user)


class FilaEstacionForm(forms.Form):
    existente = forms.ModelChoiceField(queryset=Computador.objects.none(), required=False, label='Buscar existente',
                                      widget=forms.Select(attrs={'class': 'form-select estacion-busqueda'}))
    nuevo = forms.BooleanField(required=False, widget=forms.HiddenInput)
    cantidad = forms.IntegerField(min_value=1, initial=1, required=False,
                                  widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}))

    def __init__(self, *args, tipo, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo = tipo
        model, form_class = {
            'computador': (Computador, FormComputador),
            'monitores': (Monitor, FormMonitor),
            'productos': (Producto, FormProducto),
        }[tipo]
        qs = visibles(model, user)
        if tipo != 'productos':
            qs = qs.filter(asignado=False, responsable__isnull=True)
            self.fields.pop('cantidad')
        self.fields['existente'].queryset = qs
        # Solo renderizar la selección actual; la búsqueda se realiza por AJAX.
        selected = self.data.get(self.add_prefix('existente')) if self.is_bound else None
        self.fields['existente'].widget.choices = [('', 'Buscar por inventario o serie' if tipo != 'productos' else 'Buscar producto')]
        if selected and str(selected).isdigit():
            self.fields['existente'].widget.choices += [(o.pk, str(o)) for o in qs.filter(pk=selected)]
        self.registro = preparar(form_class(self.data if self.is_bound else None, prefix=f'{self.prefix}-registro'), user)
        if 'numero_serie' in self.registro.fields and self.registro.is_bound:
            self.registro.data = self.registro.data.copy()
            key = self.registro.add_prefix('numero_serie')
            self.registro.data[key] = self.registro.data.get(key, '').strip().upper()
        self.fields['existente'].widget.attrs['data-tipo'] = tipo

    def clean(self):
        data = super().clean()
        if data.get('DELETE'):
            return data
        if data.get('nuevo'):
            if data.get('existente'):
                self.add_error('existente', 'Seleccione un existente o registre uno nuevo, no ambos.')
            if not self.registro.is_valid():
                raise forms.ValidationError('Corrija los datos del registro nuevo en el modal.')
            if self.tipo == 'productos':
                stock = self.registro.cleaned_data
                if stock['stock_disponible'] > stock['stock_total']:
                    self.registro.add_error('stock_disponible', 'No puede superar el stock total.')
                    raise forms.ValidationError('Revise el stock del producto nuevo.')
        elif not data.get('existente'):
            return data
        if self.tipo == 'productos' and not data.get('cantidad'):
            self.add_error('cantidad', 'Ingrese una cantidad mayor que cero.')
        return data

    @property
    def ocupado(self):
        return bool(self.cleaned_data.get('nuevo') or self.cleaned_data.get('existente')) and not self.cleaned_data.get('DELETE')


class SeccionFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        usados = set()
        ocupados = 0
        for form in self.forms:
            if not form.ocupado:
                continue
            ocupados += 1
            obj = form.cleaned_data.get('existente')
            key = ('id', obj.pk) if obj else ('serie', form.registro.cleaned_data.get('numero_serie', form.registro.cleaned_data.get('nombre', '')).upper())
            if key in usados:
                raise forms.ValidationError('No repita equipos o productos; ajuste la cantidad del producto.')
            usados.add(key)
        if not ocupados:
            raise forms.ValidationError('Agregue al menos un elemento o desmarque esta sección.')


def seccion(tipo, user, data=None):
    limite = {'computador': 1, 'monitores': 2, 'productos': 100}[tipo]
    factory = formset_factory(FilaEstacionForm, formset=SeccionFormSet, extra=1,
                              can_delete=True, max_num=limite, validate_max=True, absolute_max=limite)
    return factory(data, prefix=tipo, form_kwargs={'tipo': tipo, 'user': user})
