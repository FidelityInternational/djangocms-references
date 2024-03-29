from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.urls import reverse_lazy

from djangocms_alias import admin as AliasOriginalAdmin
from djangocms_snippet import admin as SnippetOriginalAdmin


def generate_get_references_link(content_grouper):
    def _get_references_link(self, obj, request):
        content_type = ContentType.objects.get(
            app_label=getattr(obj, content_grouper)._meta.app_label, model=getattr(obj, content_grouper)._meta.model_name,
        )

        url = reverse_lazy(
            "djangocms_references:references-index",
            kwargs={"content_type_id": content_type.id, "object_id": getattr(obj, content_grouper).id}
        )

        return render_to_string("djangocms_references/references_icon.html", {"url": url})
    return _get_references_link


def get_list_actions(func):
    """
    Add references action to alias list display
    """
    def inner(self, *args, **kwargs):
        list_actions = func(self, *args, **kwargs)
        list_actions.append(self._get_references_link)
        return list_actions
    return inner


AliasOriginalAdmin.AliasContentAdmin._get_references_link = generate_get_references_link('alias')
AliasOriginalAdmin.AliasContentAdmin.get_list_actions = get_list_actions(
    AliasOriginalAdmin.AliasContentAdmin.get_list_actions
)

SnippetOriginalAdmin.SnippetAdmin._get_references_link = generate_get_references_link('snippet_grouper')
SnippetOriginalAdmin.SnippetAdmin.get_list_actions = get_list_actions(
    SnippetOriginalAdmin.SnippetAdmin.get_list_actions
)