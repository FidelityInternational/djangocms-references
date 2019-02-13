from cms.app_base import CMSAppConfig

from djangocms_references.test_utils.polls.models import PollPlugin

from .models import PollContent


class PollsCMSConfig(CMSAppConfig):
    djangocms_references_enabled = True
    reference_fields = [(PollContent, "poll"), (PollPlugin, "poll")]
