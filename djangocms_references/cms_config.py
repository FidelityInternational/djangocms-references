from django.core.exceptions import ImproperlyConfigured

from cms.app_base import CMSAppConfig, CMSAppExtension
from cms.models import Page


class ReferencesCMSExtension(CMSAppExtension):
    def __init__(self):
        self.references_app_models = {}

    def configure_app(self, cms_config):
        if hasattr(cms_config, "reference_models"):
            reference_models = getattr(cms_config, "reference_models")
            if isinstance(reference_models, dict):
                self.references_app_models.update(reference_models)
            else:
                raise ImproperlyConfigured(
                    "Reference model configuration must be a dictionary object"
                )
        else:
            raise ImproperlyConfigured(
                "cms_config.py must have reference_models attribute"
            )


class CoreCMSAppConfig(CMSAppConfig):
    djangocms_references_enabled = True
    # Todo: Need think through how to supply mapping of model and its relation
    reference_models = {
        # model_class : field(s) to search in menu item form UI
        Page: ["title"]
    }
