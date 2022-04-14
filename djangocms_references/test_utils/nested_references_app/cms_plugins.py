from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import DeeplyNestedPollPlugin, NestedPollPlugin


@plugin_pool.register_plugin
class NestedPoll(CMSPluginBase):
    name = "NestedPollPlugin"
    model = NestedPollPlugin
    render_plugin = False


@plugin_pool.register_plugin
class DeeplyNestedPollPlugin(CMSPluginBase):
    name = "DeeplyNestedPollPlugin"
    model = DeeplyNestedPollPlugin
    render_plugin = False
