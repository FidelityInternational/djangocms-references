from collections import defaultdict

from django.core.exceptions import ImproperlyConfigured

from cms.app_base import CMSAppExtension
from cms.plugin_base import CMSPlugin
from cms.plugin_pool import plugin_pool


class ReferencesCMSExtension(CMSAppExtension):
    def __init__(self):
        self.reference_models = self._make_default()
        self.reference_plugins = self._make_default()

    def _make_default(self):
        return defaultdict(lambda: defaultdict(set))

    def register_fields(self, fields):
        for field in fields:
            model = field.field.model
            related_model = field.field.related_model
            if (
                issubclass(model, (CMSPlugin,))
                and model.__name__ in plugin_pool.plugins
            ):
                store = self.reference_plugins
            else:
                store = self.reference_models
            store[related_model][model].add(field.field.name)

    def configure_app(self, cms_config):
        if getattr(cms_config, "reference_fields", None) is not None:
            reference_fields = getattr(cms_config, "reference_fields")
            if isinstance(reference_fields, set):
                self.register_fields(reference_fields)
            else:
                raise ImproperlyConfigured(
                    "Reference model configuration must be a set instance"
                )
        else:
            raise ImproperlyConfigured(
                "cms_config.py must have reference_fields attribute"
            )
