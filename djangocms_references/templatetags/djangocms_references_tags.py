from django import template

from cms.toolbar.utils import get_object_preview_url


register = template.Library()


@register.simple_tag()
def object_preview_url(obj):
    """
    Displays the preview url for obj.
    """
    return get_object_preview_url(obj)


@register.simple_tag()
def object_model(obj):
    """
    Displays the model name of the obj.
    """
    return obj._meta.model_name
