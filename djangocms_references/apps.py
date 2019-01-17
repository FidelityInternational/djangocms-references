from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ReferencesConfig(AppConfig):
    name = "djangocms_references"
    verbose_name = _("django CMS References")
