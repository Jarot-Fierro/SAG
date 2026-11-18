from django import forms

from ..models.mantenedores import Marca, Modelo, TipoProducto
from ..models.productos import Producto


class FormProducto(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre del Producto', max_length=150, required=True,
        widget=forms.TextInput(attrs={
            'id': 'nombre_producto', 'class': 'form-control',
            'placeholder': 'Nombre del producto', 'maxlength': '150',
        }),
    )
    tipo_producto = forms.ModelChoiceField(
        label='Tipo de Producto', required=True,
        queryset=TipoProducto.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Seleccione un tipo de producto',
        widget=forms.Select(attrs={'id': 'tipo_producto', 'class': 'form-select tom-select'}),
    )
    marca = forms.ModelChoiceField(
        label='Marca', required=False,
        queryset=Marca.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Seleccione una marca',
        widget=forms.Select(attrs={'id': 'marca_producto', 'class': 'form-select tom-select'}),
    )
    modelo = forms.ModelChoiceField(
        label='Modelo', required=False,
        queryset=Modelo.objects.filter(is_active=True).order_by('nombre'),
        empty_label='Seleccione un modelo',
        widget=forms.Select(attrs={'id': 'modelo_producto', 'class': 'form-select tom-select'}),
    )
    stock_total = forms.IntegerField(
        label='Stock Total', min_value=0, initial=0, required=True,
        widget=forms.NumberInput(attrs={'id': 'stock_total_producto', 'class': 'form-control', 'min': 0, 'step': 1}),
    )
    stock_disponible = forms.IntegerField(
        label='Stock Disponible', min_value=0, initial=0, required=True,
        help_text='Cantidad de unidades disponibles de este producto.',
        widget=forms.NumberInput(
            attrs={'id': 'stock_disponible_producto', 'class': 'form-control', 'min': 0, 'step': 1}),
    )
    stock_minimo = forms.IntegerField(
        label='Stock Mínimo', min_value=0, initial=0, required=True,
        widget=forms.NumberInput(attrs={'id': 'stock_minimo_producto', 'class': 'form-control', 'min': 0, 'step': 1}),
    )
    descripcion = forms.CharField(
        label='Descripción', required=False,
        help_text='Ejemplo: conexión USB, capacidad de 64 GB o disco SSD de 1 TB.',
        widget=forms.Textarea(attrs={'id': 'descripcion_producto', 'class': 'form-control', 'rows': 3}),
    )

    class Meta:
        model = Producto
        fields = [
            'nombre', 'tipo_producto', 'marca', 'modelo', 'stock_total',
            'stock_disponible', 'stock_minimo', 'descripcion',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        modelos = self.fields['modelo'].queryset
        self.modelos_por_marca = list(modelos.values('id', 'nombre', 'marca_id'))
        marca_id = self.data.get(self.add_prefix('marca')) if self.is_bound else self.initial.get('marca')
        try:
            marca_id = int(marca_id)
        except (TypeError, ValueError):
            marca_id = None
        self.fields['modelo'].queryset = modelos.filter(marca_id=marca_id) if marca_id else modelos.none()
        if not marca_id:
            self.fields['modelo'].widget.attrs['disabled'] = True

    def clean(self):
        cleaned_data = super().clean()
        marca = cleaned_data.get('marca')
        modelo = cleaned_data.get('modelo')
        if marca and modelo and modelo.marca_id != marca.pk:
            self.add_error('modelo', 'El modelo seleccionado no pertenece a la marca indicada.')
        return cleaned_data
