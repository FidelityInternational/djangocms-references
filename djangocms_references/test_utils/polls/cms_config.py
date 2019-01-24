from cms.app_base import CMSAppConfig
from cms.utils.i18n import get_language_tuple

from djangocms_versioning.datastructures import VersionableItem, default_copy

from .models import PollContent


class PollsCMSConfig(CMSAppConfig):
    djangocms_references_enabled = True
    reference_fields = {PollContent.poll}
