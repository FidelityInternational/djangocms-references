from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool

from .models import References


@toolbar_pool.register
class ReferencesToolbar(CMSToolbar):
    """
    Adding references button to CMS toolbar to access plugin admin area
    """

    def populate(self):
        obj = self.toolbar.obj
        opts = References._meta
        if not self.request.user.has_perm(
            "{app_label}.show_references".format(app_label=opts.app_label)
        ) or obj is None:
            return
        content_type_id = ContentType.objects.get_for_model(obj).pk
        self.toolbar.add_sideframe_button(
            _("Show References"),
            reverse(
                "djangocms_references:references-index",
                kwargs={"content_type_id": content_type_id, "object_id": obj.id},
            ),
        )
