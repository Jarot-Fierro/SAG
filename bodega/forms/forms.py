from django import forms

from bodega.models.bodega import Bodega
from bodega.models.mantenedores import CategoriaProducto, Marca, UnidadMedida
from bodega.models.producto import Producto
from bodega.models.stock import Stock


class FormBodega(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    descripcion = forms.CharField(
        label='Descripción',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3})
    )
    categorias = forms.ModelMultipleChoiceField(
        queryset=CategoriaProducto.objects.all(),
        label='Categorías',
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control form-control-sm'})
    )

    class Meta:
        model = Bodega
        fields = ['nombre', 'descripcion', 'categorias']


class FormProducto(forms.ModelForm):
    codigo = forms.CharField(
        label='Código',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    nombre = forms.CharField(
        label='Nombre',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    descripcion = forms.CharField(
        label='Descripción',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 3})
    )
    categoria = forms.ModelChoiceField(
        queryset=CategoriaProducto.objects.all(),
        label='Categoría',
        required=True,
        empty_label='Seleccione una categoría',
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    marca = forms.ModelChoiceField(
        queryset=Marca.objects.all(),
        label='Marca',
        required=False,
        empty_label='Seleccione una marca',
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    unidad_medida = forms.ModelChoiceField(
        queryset=UnidadMedida.objects.all(),
        label='Unidad de Medida',
        required=True,
        empty_label='Seleccione una unidad',
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    activo = forms.BooleanField(
        label='Activo',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'descripcion', 'categoria', 'marca', 'unidad_medida', 'activo']


class FormStock(forms.ModelForm):
    bodega = forms.ModelChoiceField(
        queryset=Bodega.objects.all(),
        label='Bodega',
        required=True,
        empty_label='Seleccione una bodega',
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        label='Producto',
        required=True,
        empty_label='Seleccione un producto',
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    status_stock = forms.ChoiceField(
        choices=Stock.STATUS_CHOICES,
        label='Estado de Stock',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    stock_actual = forms.DecimalField(
        label='Stock Actual',
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'})
    )
    stock_minimo = forms.DecimalField(
        label='Stock Mínimo',
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'})
    )
    stock_maximo = forms.DecimalField(
        label='Stock Máximo',
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'})
    )
    ubicacion = forms.CharField(
        label='Ubicación',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )

    class Meta:
        model = Stock
        fields = ['bodega', 'producto', 'status_stock', 'stock_actual', 'stock_minimo', 'stock_maximo', 'ubicacion']
