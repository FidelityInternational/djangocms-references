from collections import defaultdict
from functools import lru_cache, partial
from itertools import groupby
from operator import itemgetter

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import F, Q

from cms.models import CMSPlugin


def get_versionable_for_content(content):
    try:
        from djangocms_versioning import versionables
    except ImportError:
        return
    try:
        return versionables.for_content(content)
    except KeyError:
        pass


def get_relation(field_name, versionable):
    if versionable:
        content_name = versionable.grouper_field.remote_field.get_accessor_name()
        return "{}__{}".format(field_name, content_name)
    return field_name


@lru_cache(maxsize=1)
def get_extension():
    app = apps.get_app_config("djangocms_references")
    return app.cms_extension


def get_extra_columns():
    return get_extension().list_extra_columns


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
        qs = model.objects.filter(get_filters(content, relations))
        if qs.exists():
            yield qs


def get_reference_objects(content):
    yield from _get_reference_objects(content, get_reference_models)


def contenttype_values_queryset(queryset):
    return (
        queryset.order_by()  # need to clear ordering,
        # as ordering clauses are not allowed in subqueries
        .annotate(
            content_type=F("placeholder__content_type"),
            object_id=F("placeholder__object_id"),
        ).values("content_type", "object_id")
    )


def convert_plugin_querysets_to_sources(querysets):
    # since plugins use concrete inheritance, it's safe to combine querysets
    # with PKs of different plugin models
    sources = contenttype_values_queryset(CMSPlugin.objects.none())
    for queryset in querysets:
        sources = sources.union(contenttype_values_queryset(queryset))
    return sources.order_by("content_type")


def get_reference_objects_from_plugins(content):
    querysets = [
        qs.filter(
            # NOTE: This filters out static placeholders
            Q(placeholder__content_type__isnull=False)
        )
        for qs in _get_reference_objects(content, get_reference_plugins)
    ]
    # `querysets` contains a list of plugin querysets,
    # we want to end up with a list of source object (CMSPlugin.placeholder.source)
    # querysets
    sources = convert_plugin_querysets_to_sources(querysets)
    for ctype_id, group_sources in groupby(sources, itemgetter("content_type")):
        content_type = ContentType.objects.get_for_id(ctype_id)
        yield content_type.get_all_objects_for_this_type(
            pk__in=[source["object_id"] for source in group_sources]
        )


def filter_only_draft_and_published(queryset):
    versionable = get_versionable_for_content(queryset.model)
    if versionable:
        from djangocms_versioning.constants import DRAFT, PUBLISHED

        return queryset.filter(versions__state__in=(DRAFT, PUBLISHED))
    return queryset


def combine_querysets_of_same_models(*querysets_list):
    """Given multiple List[Queryset[Model]] arguments,
    returns a single List[Queryset[Model]], with querysets being
    combined with other querysets of the same model.
    """
    model_map = defaultdict(list)
    for querysets in querysets_list:
        for queryset in querysets:
            model_map[queryset.model].append(queryset)
    for querysets in model_map.values():
        combined = querysets.pop()
        for queryset in querysets:
            combined |= queryset
        yield combined


def apply_additional_modifiers(queryset):
    extension = get_extension()
    for modifier in extension.list_queryset_modifiers:
        queryset = modifier(queryset)
    return queryset


def get_all_reference_objects(content, draft_and_published=False):
    postprocess = None
    if draft_and_published:
        postprocess = partial(map, filter_only_draft_and_published)
    querysets = combine_querysets_of_same_models(
        get_reference_objects(content), get_reference_objects_from_plugins(content)
    )
    if postprocess:
        querysets = postprocess(querysets)
    return list(apply_additional_modifiers(qs) for qs in querysets)
