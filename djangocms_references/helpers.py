from contextlib import suppress
from functools import lru_cache

from django.apps import apps
from django.db.models import Q


def get_versionable_for_content(content_model):
    try:
        from djangocms_versioning import versionables
    except ImportError:
        return
    with suppress(KeyError):
        return versionables.for_content(content_model)


def get_relation(field_name, versionable):
    if versionable:
        content_name = versionable.grouper_field.remote_field.get_accessor_name()
        return "{}__{}".format(field_name, content_name)
    return field_name


@lru_cache(maxsize=1)
def get_extension():
    app = apps.get_app_config("djangocms_references")
    return app.cms_extension


def _get_reference_models(content_model, models):
    versionable = get_versionable_for_content(content_model)
    if versionable:
        target_model = versionable.grouper_model
    else:
        target_model = content_model
    for model, fields in models[target_model].items():
        relations = []
        for field in fields:
            relations.append(get_relation(field, versionable))
        yield model, relations


def get_reference_models(content_model):
    extension = get_extension()
    yield from _get_reference_models(content_model, extension.reference_models)


def get_reference_plugins(content_model):
    extension = get_extension()
    yield from _get_reference_models(content_model, extension.reference_plugins)


def get_filters(content, relations):
    q = Q()
    for relation in relations:
        q |= Q(**{relation: content})
    return q


def _get_reference_objects(content, models_func):
    for reference in models_func(content.__class__):
        model, relations = reference
        yield model.objects.filter(get_filters(content, relations))


def _get_reference_plugin_instances(content, model_func):
    for queryset in _get_reference_objects(content, model_func):
        yield queryset.prefetch_related("placeholder__source")


def get_reference_objects(content):
    querysets = list(_get_reference_objects(content, get_reference_models))
    plugins = list(_get_reference_plugin_instances(content, get_reference_plugins))
    return querysets, plugins
