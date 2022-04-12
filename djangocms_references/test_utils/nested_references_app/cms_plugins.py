from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import DeeplyNestedPollPlugin


@plugin_pool.register_plugin
class DeeplyNestedPollPlugin(CMSPluginBase):
    name = "DeeplyNestedPollPlugin"
    model = DeeplyNestedPollPlugin
    render_plugin = False
