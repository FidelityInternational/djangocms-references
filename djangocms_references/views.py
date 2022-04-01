from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView

from .helpers import get_all_reference_objects, get_extra_columns
from .models import References

from djangocms_versioning.constants import VERSION_STATES


class ReferencesView(TemplateView):
    template_name = "djangocms_references/references.html"

    def dispatch(self, *args, **kwargs):
        opts = References._meta
        if not self.request.user.has_perm(
            "{app_label}.show_references".format(app_label=opts.app_label)
        ):
            raise PermissionDenied
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        extra_columns = get_extra_columns()

        try:
            content_type = ContentType.objects.get_for_id(
                int(self.kwargs.get("content_type_id"))
            )
        except ContentType.DoesNotExist:
            raise Http404

        model = content_type.model_class()

        try:
            obj = content_type.get_object_for_this_type(
                pk=int(self.kwargs["object_id"])
            )
        except model.DoesNotExist:
            raise Http404

        selected_state = self.request.GET.get("state")

        querysets = get_all_reference_objects(obj, selected_state)

        context.update(
            {
                "title": _("References of {object}").format(object=obj),
                "opts": model._meta,
                "querysets": querysets,
                "selected_state": selected_state,
                "extra_columns": extra_columns,
                "version_states": VERSION_STATES
            }
        )
        return context
