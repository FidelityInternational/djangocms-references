from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .forms import PollPluginForm
from .models import PollPlugin


_all__ = ["References"]


@plugin_pool.register_plugin
class Polls(CMSPluginBase):
    name = _("Poll")
    model = PollPlugin
    form = PollPluginForm
    render_plugin = False
