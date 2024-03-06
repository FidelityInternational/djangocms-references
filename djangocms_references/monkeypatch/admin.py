from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.urls import reverse_lazy

from djangocms_alias import admin

from djangocms_references.compat import DJANGO_CMS_4_1


def _get_references_link(self, obj, request):
    alias_content_type = ContentType.objects.get(
        app_label=obj.alias._meta.app_label,
        model=obj.alias._meta.model_name,
    )

    url = reverse_lazy(
        "djangocms_references:references-index",
        kwargs={"content_type_id": alias_content_type.id, "object_id": obj.alias.id}
    )

    return render_to_string("djangocms_references/references_icon.html", {"url": url})


def get_list_actions(func):
    """
    Add references action to alias list display
    """
    def inner(self, *args, **kwargs):
        list_actions = func(self, *args, **kwargs)
        list_actions.append(self._get_references_link)
        return list_actions
    return inner


if not DJANGO_CMS_4_1:
    admin.AliasContentAdmin._get_references_link = _get_references_link
    admin.AliasContentAdmin.get_list_actions = get_list_actions(
        admin.AliasContentAdmin.get_list_actions
    )
else:
    # TODO: add reference button for django cms 4.1
    pass
