from collections import defaultdict
from collections.abc import Iterable

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from cms.app_base import CMSAppConfig, CMSAppExtension
from cms.plugin_base import CMSPlugin
from cms.plugin_pool import plugin_pool

from djangocms_alias.models import AliasPlugin

from .datastructures import ExtraColumn
from .helpers import (
    get_all_reference_objects,
    get_extra_columns,
    get_versionable_for_content,
    version_attr,
)


class ReferencesCMSExtension(CMSAppExtension):
    def __init__(self):
        self.reference_models = self._make_default()
        self.reference_plugins = self._make_default()
        self.reference_complex_relationships = self._make_default()
        self.list_extra_columns = []
        self.list_queryset_modifiers = []

    def _make_default(self):
        return defaultdict(lambda: defaultdict(set))

    def get_nested_relationship(self, model, fields):

        for validation_field in fields:
            try:
                model = getattr(model, validation_field).field.related_model
            except (ValueError, TypeError) as e:
                raise ImproperlyConfigured(
                    "Elements of the reference_fields list should be (model, field_name) tuples"
                ) from e
        return model

    def register_fields(self, definitions):
        """Registers relations to enable reference retrieval.

        :param definitions: A list of (model, field_name) field.

        Example:
        (AliasPlugin, 'alias') enables tracking Alias use in plugins,
        so that pages using the alias will be shown in the references
        list.
        """
        # generate reference_models and reference_plugins dict object
        for definition in definitions:
            try:
                model, field_name = definition
            except (ValueError, TypeError) as e:
                raise ImproperlyConfigured(
                    "Elements of the reference_fields list should be (model, field_name) tuples"
                ) from e
            if "__" in field_name:
                fields = field_name.split("__")
                related_model = self.get_nested_relationship(model, fields)
            else:
                field = model._meta.get_field(field_name)
                related_model = field.related_model
            if (
                issubclass(model, (CMSPlugin,))
            ):
                store = self.reference_plugins
            else:
                store = self.reference_models
            store[related_model][model].add(field_name)

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
            if isinstance(reference_fields, Iterable) and not isinstance(
                reference_fields, str
            ):
                self.register_fields(reference_fields)
            else:
                raise ImproperlyConfigured(
                    "Reference model configuration must be an Iterable instance"
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
    """Render a partial template with a list of unpublish dependencies"""
    references = get_all_reference_objects(version.content, draft_and_published=True)
    return render_to_string(
        "djangocms_references/references_table.html",
        {"querysets": references, "extra_columns": get_extra_columns()},
    )


class ReferencesCMSAppConfig(CMSAppConfig):
    djangocms_references_enabled = True
    djangocms_versioning_enabled = getattr(
        settings, "DJANGOCMS_REFERENCES_VERSIONING_ENABLED", True
    )
    reference_fields = [(AliasPlugin, 'alias')]
    reference_list_extra_columns = [
        (version_attr(lambda v: v.get_state_display()), _("Status")),
        (version_attr(lambda v: v.created_by), _("Author")),
        (version_attr(lambda v: v.modified), _("Modified date")),
    ]
    reference_list_queryset_modifiers = [version_queryset_modifier]
    versioning_add_to_confirmation_context = {
        "unpublish": {"unpublish_dependencies": unpublish_dependencies}
    }
