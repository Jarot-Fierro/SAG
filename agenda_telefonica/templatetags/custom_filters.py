from django import template

register = template.Library()


@register.filter
def attribute_filter(obj, attr_name):
    """
    Retorna el valor del atributo de un objeto.
    Si el atributo es un callable (como un method), lo llama.
    """
    try:
        attribute = getattr(obj, attr_name)
        if callable(attribute):
            return attribute()
        return attribute
    except (AttributeError, TypeError):
        return ""
