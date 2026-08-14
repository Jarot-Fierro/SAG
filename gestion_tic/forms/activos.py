from django import forms
from django.db import transaction

from gestion_tic.models import Activo, ActivoCaracteristica, CampoTipoActivo


class ActivoForm(forms.ModelForm):
    dynamic_fields = []

    class Meta:
        model = Activo
        fields = [
            'codigo_barra', 'tipo',
            'marca', 'modelo', 'serie', 'contrato', 'observacion', 'de_baja'
        ]
        widgets = {
            'codigo_barra': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select', 'style': 'pointer-events:none;background:#e9ecef;'}),
            'marca': forms.Select(attrs={'class': 'form-select select2'}),
            'modelo': forms.Select(attrs={'class': 'form-select select2'}),
            'serie': forms.TextInput(attrs={'class': 'form-control'}),
            'contrato': forms.Select(attrs={'class': 'form-select select2'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'de_baja': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        tipo_activo = kwargs.pop('tipo_activo', None)
        super().__init__(*args, **kwargs)
        self.dynamic_fields = []

        # Si estamos editando y no se pasó tipo_activo, lo tomamos de la instancia
        if not tipo_activo and self.instance.pk:
            tipo_activo = self.instance.tipo

        if tipo_activo:
            # Aseguramos que el campo tipo tenga el valor correcto y sea readonly
            self.fields['tipo'].initial = tipo_activo
            self.fields['tipo'].widget.attrs['readonly'] = True

            campos = CampoTipoActivo.objects.filter(tipo_activo=tipo_activo).order_by('orden', 'nombre')
            for campo in campos:
                field_name = f'dynamic_{campo.id}'
                self.dynamic_fields.append(field_name)

                # Obtener valor inicial si existe la instancia
                initial_value = None
                if self.instance.pk:
                    carac = ActivoCaracteristica.objects.filter(activo=self.instance, campo=campo).first()
                    if carac:
                        initial_value = carac.valor

                field_kwargs = {
                    'label': campo.nombre,
                    'required': campo.obligatorio,
                    'initial': initial_value,
                }

                if campo.tipo_campo == 'text':
                    self.fields[field_name] = forms.CharField(
                        widget=forms.TextInput(attrs={'class': 'form-control'}),
                        **field_kwargs
                    )
                elif campo.tipo_campo == 'number':
                    self.fields[field_name] = forms.IntegerField(
                        widget=forms.NumberInput(attrs={'class': 'form-control'}),
                        **field_kwargs
                    )
                elif campo.tipo_campo == 'date':
                    self.fields[field_name] = forms.DateField(
                        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                        **field_kwargs
                    )
                elif campo.tipo_campo == 'boolean':
                    field_kwargs['initial'] = initial_value == 'True' if initial_value is not None else False
                    self.fields[field_name] = forms.BooleanField(
                        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                        **field_kwargs
                    )
                elif campo.tipo_campo == 'select':
                    opciones = [(opt.nombre, opt.nombre) for opt in campo.opciones.all()]
                    if not campo.obligatorio:
                        opciones = [('', '---------')] + opciones

                    self.fields[field_name] = forms.ChoiceField(
                        choices=opciones,
                        widget=forms.Select(attrs={'class': 'form-select select2'}),
                        **field_kwargs
                    )

            # Facilitar el renderizado en el template
            self.dynamic_form_fields = [self[name] for name in self.dynamic_fields]

    def save(self, commit=True):
        with transaction.atomic():
            activo = super().save(commit=commit)

            if commit:
                self.save_dynamic_fields(activo)

            return activo

    def save_dynamic_fields(self, activo):
        for field_name in self.dynamic_fields:
            campo_id = int(field_name.split('_')[1])
            valor = self.cleaned_data.get(field_name)

            if valor is None:
                valor_str = ""
            else:
                valor_str = str(valor)

            ActivoCaracteristica.objects.update_or_create(
                activo=activo,
                campo_id=campo_id,
                defaults={'valor': valor_str}
            )
