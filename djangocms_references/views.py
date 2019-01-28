from django.contrib.contenttypes.models import ContentType
from django.http.response import HttpResponseBadRequest
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView

from .helpers import get_additional_attrs, get_all_reference_objects


class ReferencesView(TemplateView):
    template_name = "djangocms_references/references.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        additional_attrs = get_additional_attrs()

        try:
            content_type = ContentType.objects.get_for_id(
                int(self.kwargs.get("content_type_id"))
            )
        except (ContentType.DoesNotExist, ValueError):
            return HttpResponseBadRequest()

        model = content_type.model_class()

        try:
            obj = content_type.get_object_for_this_type(
                pk=int(self.kwargs["object_id"])
            )
        except (model.DoesNotExist, ValueError):
            return HttpResponseBadRequest()

        draft_and_published = self.request.GET.get("state") == "draft_and_published"

        querysets = get_all_reference_objects(
            obj, draft_and_published=draft_and_published
        )

        context.update(
            {
                "title": _("References of {object}").format(object=obj),
                "opts": model._meta,
                "querysets": querysets,
                "draft_and_published": draft_and_published,
                "additional_attrs": [attr.verbose_name for attr in additional_attrs],
            }
        )
        return context
