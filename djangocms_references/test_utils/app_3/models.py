from django.db import models

from cms.models.pluginmodel import CMSPlugin

from ..app_2.fields import PluginExtensionField


class PluginModelWithNestedTarget(CMSPlugin):
    name = models.CharField(max_length=255)
    field_referenced = PluginExtensionField(
        on_delete=models.SET_NULL,
        null=True,
    )
