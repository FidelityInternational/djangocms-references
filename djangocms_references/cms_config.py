from collections import defaultdict

from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from cms.app_base import CMSAppConfig, CMSAppExtension
from cms.plugin_base import CMSPlugin
from cms.plugin_pool import plugin_pool

from .datastructures import ExtraColumn
from .helpers import get_versionable_for_content, version_attr, get_all_reference_objects


class ReferencesCMSExtension(CMSAppExtension):
    def __init__(self):
        self.reference_models = self._make_default()
        self.reference_plugins = self._make_default()
        self.list_extra_columns = []
        self.list_queryset_modifiers = []

    def _make_default(self):
        return defaultdict(lambda: defaultdict(set))

    def register_fields(self, fields):
        # generate reference_models and reference_plugins dict object
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

    def configure_list_extra_columns(self, extra_columns):
        """Registers additional columns to be displayed in the reference
        table.

        Expects `reference_list_extra_columns` attribute to be set,
        which is a list of (func, label) tuple.

        Function should expect a single argument, a content object.
        Its return value will be displayed in that column's/object's cell.

        Example:
        reference_list_extra_columns = [
            (lambda obj: str(obj), 'Column header'),
            (lambda obj: id(obj), 'Another column header'),
        ]
        """
        for column in extra_columns:
            column_ = ExtraColumn(*column)
            self.list_extra_columns.append(column_)

    def configure_list_queryset_modifiers(self, modifiers):
        """Registers a list of functions that are applied to reference
        list querysets.
        """
        self.list_queryset_modifiers.extend(modifiers)

    def configure_app(self, cms_config):
        """
        Third party app can define set object as reference_fields (like Child.parent)
        to define child parent relation of any field to model.
        Based on definition register_fields method generate model and plugin dict
        """
        if getattr(cms_config, "reference_fields", None) is not None:
            reference_fields = getattr(cms_config, "reference_fields")
            if isinstance(reference_fields, set):
                self.register_fields(reference_fields)
            else:
                raise ImproperlyConfigured(
                    "Reference model configuration must be a set instance"
                )
        self.configure_list_extra_columns(
            getattr(cms_config, "reference_list_extra_columns", [])
        )
        self.configure_list_queryset_modifiers(
            getattr(cms_config, "reference_list_queryset_modifiers", [])
        )


def version_queryset_modifier(queryset):
    """Applies prefetch_related on version relation
    if provided queryset's model is versionable.
    """
    if get_versionable_for_content(queryset.model):
        queryset = queryset.prefetch_related("versions", "versions__created_by")
    return queryset


def unpublish_dependencies(request, version, *args, **kwargs):
    references = get_all_reference_objects(
        version.content, draft_and_published=True)
    all_querysets_empty = all([not q.exists() for q in references])
    if all_querysets_empty:
        return ""
    return render_to_string(
        'djangocms_references/unpublish_dependencies.html',
        {'references': references}
    )


class ReferencesCMSAppConfig(CMSAppConfig):
    djangocms_references_enabled = True
    djangocms_versioning_enabled = True  # TODO: Setting
    reference_list_extra_columns = [
        (version_attr(lambda v: v.get_state_display()), _("Status")),
        (version_attr(lambda v: v.created_by), _("Author")),
        (version_attr(lambda v: v.modified), _("Modified date")),
    ]
    reference_list_queryset_modifiers = [version_queryset_modifier]
    versioning_add_to_confirmation_context = {
        'unpublish': {'unpublish_dependencies': unpublish_dependencies}
    }
