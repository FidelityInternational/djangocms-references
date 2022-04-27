from django import template
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy

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


@register.simple_tag()
def extra_column(obj, column):
    return column.getter(obj)


@register.simple_tag()
def get_versioning_filer_references_url(file):
    """
    A template tag that provides a url to the references view.

    :param file: A file grouper object
    :returns: A url that links to the references index view for a given file
    """
    content_type = ContentType.objects.get(
        app_label=file._meta.app_label,
        model=file._meta.model_name,
    )

    return reverse_lazy(
        "djangocms_references:references-index",
        kwargs={"content_type_id": content_type.id, "object_id": file.id}
    )
