from django import template

from cms.toolbar.utils import get_object_preview_url


register = template.Library()


@register.simple_tag()
def object_preview_url(obj):
    """
    Displays the preview url for obj.
    """
    if isinstance(obj, (int, str)):
        raise template.TemplateSyntaxError(
            "object_preview_url tag requires a model object as argument"
        )
    return get_object_preview_url(obj)


@register.simple_tag()
def object_model(obj):
    """
    Displays the model name of the obj.
    """
    if not hasattr(obj, "_meta"):
        raise template.TemplateSyntaxError(
            "object_model tag requires a model object as argument"
        )
    return obj._meta.model_name
