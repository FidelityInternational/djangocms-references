from cms.app_base import CMSAppConfig

from .models import Child


class CMSApp1Config(CMSAppConfig):
    djangocms_references_enabled = True
    reference_fields = [(Child, "parent")]
