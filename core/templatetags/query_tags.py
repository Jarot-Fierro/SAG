from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Template tag que permite transformar el query string actual del request.GET.
    Permite añadir, modificar o eliminar parámetros.
    Si un parámetro es None o una cadena vacía, se elimina del query string.
    """
    request = context.get('request')
    if not request:
        return ""

    # Hacemos una copia mutable de request.GET
    # request.GET es un QueryDict inmutable por defecto.
    updated = request.GET.copy()

    for key, value in kwargs.items():
        if value is not None and value != "":
            updated[key] = value
        else:
            # Si el valor es None o vacío, eliminamos la llave si existe
            if key in updated:
                del updated[key]

    # urlencode() genera la cadena tipo 'key1=val1&key2=val2'
    return updated.urlencode()
