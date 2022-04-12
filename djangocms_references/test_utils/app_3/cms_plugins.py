from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import PluginModelWithNestedTarget

from djangocms_references.test_utils.app_2.models import ExtensionModel

@plugin_pool.register_plugin
class ExtensionPlugin(CMSPluginBase):
    name = "ExtensionPlugin"
    model = PluginModelWithNestedTarget
    render_plugin = False
