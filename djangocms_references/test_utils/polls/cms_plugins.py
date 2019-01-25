from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .forms import PollPluginForm
from .models import PollPlugin as Poll


_all__ = ["References"]


@plugin_pool.register_plugin
class PollPlugin(CMSPluginBase):
    name = "PollPlugin"
    model = Poll
    form = PollPluginForm
    render_plugin = False
