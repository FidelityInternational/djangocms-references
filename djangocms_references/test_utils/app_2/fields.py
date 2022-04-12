from django.db import models

from djangocms_references.test_utils.app_2.models import ExtensionModel


class PluginExtensionField(models.ForeignKey):
    def __init__(self, **kwargs):
        kwargs["to"] = f"djangocms_references.{ExtensionModel.__name__}"
        super().__init__(**kwargs)
