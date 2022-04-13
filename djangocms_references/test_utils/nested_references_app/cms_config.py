from cms.app_base import CMSAppConfig

from .models import DeeplyNestedPollPlugin


class CMSApp3Config(CMSAppConfig):
    djangocms_references_enabled = True
    reference_fields = [(DeeplyNestedPollPlugin, "deeply_nested_poll__nested_poll__poll")]
