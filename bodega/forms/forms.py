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
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.bodega = kwargs.pop('bodega', None)
        super().__init__(*args, **kwargs)

        if self.bodega:
            self.fields['categoria'].queryset = CategoriaProducto.objects.filter(
                bodegas=self.bodega
            )

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
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.bodega = kwargs.pop('bodega', None)

        super().__init__(*args, **kwargs)

        if self.bodega:
            # Mostrar solamente la bodega seleccionada
            self.fields['bodega'].queryset = Bodega.objects.filter(
                pk=self.bodega
            )

            # Obtener la bodega
            bodega = Bodega.objects.filter(
                pk=self.bodega
            ).first()

            if bodega:
                # Obtener productos cuya categoría pertenece
                # a las categorías asignadas a esta bodega
                self.fields['producto'].queryset = Producto.objects.filter(
                    categoria__in=bodega.categorias.all()
                ).select_related(
                    'categoria',
                    'marca',
                    'unidad_medida'
                )

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
    stock_actual = forms.IntegerField(
        label='Stock Actual',
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'})
    )
    stock_minimo = forms.IntegerField(
        label='Stock Mínimo',
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'})
    )
    stock_maximo = forms.IntegerField(
        label='Stock Máximo',
        required=False,
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


class FormEntradaStock(forms.Form):
    cantidad = forms.IntegerField(
        min_value=1,
        label="Cantidad a ingresar",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    observacion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


class FormSalidaStock(forms.Form):
    cantidad = forms.IntegerField(
        min_value=1,
        label="Cantidad a retirar",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    observacion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


class FormAjusteStock(forms.Form):
    TIPO_AJUSTE = [
        ('AUMENTAR', 'Aumentar'),
        ('DISMINUIR', 'Disminuir'),
    ]
    tipo_ajuste = forms.ChoiceField(
        choices=TIPO_AJUSTE,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cantidad = forms.IntegerField(
        min_value=1,
        label="Cantidad",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    observacion = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


class FormTransferenciaStock(forms.Form):
    bodega_destino = forms.ModelChoiceField(
        queryset=Bodega.objects.none(),
        label="Bodega destino",
        empty_label="Seleccione una bodega",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cantidad = forms.IntegerField(
        min_value=1,
        label="Cantidad a transferir",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    observacion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def __init__(self, *args, **kwargs):
        stock = kwargs.pop('stock', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if stock and user:
            # Filtros:
            # 1. Diferente de la origen
            # 2. Permisos del usuario (PerfilBodega)
            # 3. Categoría del producto
            qs = Bodega.objects.exclude(pk=stock.bodega.pk)

            # Filtro por categoría del producto
            qs = qs.filter(categorias=stock.producto.categoria)

            # Filtro por perfil de bodega del usuario
            if hasattr(user, 'perfil_bodega'):
                qs = qs.filter(pk__in=user.perfil_bodega.bodegas.all())
            else:
                # Si el usuario no tiene perfil de bodega, quizás no debería ver ninguna?
                # O quizás ve todas las permitidas por defecto?
                # La instrucción dice: "estén disponibles según la lógica de permisos/perfil de bodega del usuario"
                qs = qs.none()

            self.fields['bodega_destino'].queryset = qs
