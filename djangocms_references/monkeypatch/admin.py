from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.urls import reverse_lazy

from djangocms_alias import admin


def _get_references_link(self, obj, request):
    alias_content_type = ContentType.objects.get(
        app_label=self._meta.app_label,
        model_Name=self._meta.model_name,
    )

    url = reverse_lazy(
        "djangocms_references:references-index",
        kwargs={"content_type_id": alias_content_type.id, "object_id": obj.alias.id}
    )

    return render_to_string("djangocms_references", {"url": url})


def get_list_display(func):
    """
    Add references action to alias list display
    """
    def inner(self, *args, **kwargs):
        list_display = func(self, *args, **kwargs)
        list_display.append(self._get_references_link)
        return list_display
    return inner


admin.AliasContentAdmin._get_references_link = _get_references_link
admin.AliasContentAdmin.get_list_display = admin.AliasContentAdmin.get_list_display(
    admin.AliasContentAdmin.get_list_display
)
