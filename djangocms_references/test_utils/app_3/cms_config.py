from cms.app_base import CMSAppConfig

from .models import PluginModelWithNestedTarget


class CMSApp3Config(CMSAppConfig):
    djangocms_references_enabled = True
    reference_fields = [(PluginModelWithNestedTarget, "referenced_field")]
