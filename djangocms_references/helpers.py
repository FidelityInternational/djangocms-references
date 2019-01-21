from django.apps import apps
from django.db.models import Q

from djangocms_versioning import versionables


def get_extension():
    app = apps.get_app_config("djangocms_references")
    return app.cms_extension


def _get_reference_models(content_model, models):
    versionable = versionables.for_content(content_model)
    grouper = versionable.grouper_model
    for model, fields in models[grouper].items():
        relations = []
        for field in fields:
            grouper_name = versionable.grouper_field.name
            content_name = versionable.grouper_field.remote_field.get_accessor_name()
            relations.append("{}__{}".format(grouper_name, content_name))
        yield model, relations


def get_reference_models(content_model):
    extension = get_extension()
    yield from _get_reference_models(content_model, extension.reference_models)


def get_reference_plugins(content_model):
    extension = get_extension()
    yield from _get_reference_models(content_model, extension.reference_plugins)


def _get_reference_objects(content, models_func):
    for reference in models_func(content.__class__):
        model, relations = reference
        q = Q()
        for relation in relations:
            q |= Q(**{relation: content})
        yield model.objects.filter(q)


def _get_reference_plugin_instances(content, model_func):
    for queryset in _get_reference_objects(content, model_func):
        yield queryset.prefetch_related("placeholder__source")


def get_reference_objects(content):
    querysets = list(_get_reference_objects(content, get_reference_models))
    plugins = list(_get_reference_plugin_instances(content, get_reference_plugins))
    return querysets, plugins
