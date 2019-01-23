from django.contrib.contenttypes.models import ContentType
from django.http.response import HttpResponseBadRequest
from django.views.generic.base import TemplateView

from .helpers import get_reference_objects


class ReferencesView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        content_type = ContentType.objects.get_for_id(
            int(self.kwargs.get("content_type_id"))
        )
        if not content_type:
            return HttpResponseBadRequest()

        try:
            object_content = content_type.model_class()._base_manager.get(
                pk=int(self.kwargs["object_id"])
            )
        except content_type.model_class().DoesNotExist:
            return HttpResponseBadRequest()

        querysets, plugin_querysets = get_reference_objects(object_content)
        context["querysets"] = querysets
        context["plugin_querysets"] = plugin_querysets
        return context
