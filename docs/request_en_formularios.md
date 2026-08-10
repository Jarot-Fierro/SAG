Como pasar el request a un Formulario.
Creamos la correspondiente vista basada en el standard ya creado llamado StandardCreateView e indicamos la funcion
get_form_kargs en donde pasaremos la petición request al formulario indicado en la clase.

```mermaid
class ProductoCreateView(StandardCreateView):
    model = Producto
    form_class = FormProducto
    template_name = 'bodega/form_producto.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
```

Creamos el formulario correspondiente a donde queremos pasar el request y obtenemos la petición a traves de la funcion _
_init__.

```mermaid
class FormProducto(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
```

Podemos agregar filtros o busquedas correspondientes al request en el formulario como el siguiente ejemploclass
FormStock(forms.ModelForm):

```mermaid
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request:
            bodega_id = self.request.GET.get('bodega')

            if bodega_id:
                self.fields['bodega'].queryset = Bodega.objects.filter(
                    pk=bodega_id
                )
```