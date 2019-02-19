from collections import defaultdict
from functools import lru_cache, partial
from itertools import groupby
from operator import itemgetter

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import F, Q

from cms.models import CMSPlugin


def get_versionable_for_content(content):
    """Returns a VersionableItem for a given content object (or content model).

    Returns None if given object is not versioned, or versioning is not installed.
    """
    try:
        from djangocms_versioning import versionables
    except ImportError:
        return
    try:
        return versionables.for_content(content)
    except KeyError:
        pass


def get_lookup(field_name, versionable):
    """Returns a filtering lookup.

    If passed a versionable (which is a VersionableItem for the content object),
    it makes it so that lookup uses <grouper>__<content> form.

    :param field_name:
    :param versionable: VersionableItem or None
    """
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
    """Yields (model, lookups) pairs, where model is a model that
    can contain references to content_model and lookups is a list
    of lookups used to filter that model's objects against
    provided content object later on.

    :param content_model: A content model
    :param models: Related model registry

    Example:
    models = {
        Alias: {
            AliasPlugin: ["alias"],
        },
    }
    content_model = AliasContent

    In this case, since AliasContent is versioned, target_model becomes
    Alias This generator will loop through models[Alias] dictionary and
    generate (model, lookups) pairs, in this case:
    [(AliasPlugin, 'alias__aliascontent')]
    """
    versionable = get_versionable_for_content(content_model)
    if versionable:
        target_model = versionable.grouper_model
    else:
        target_model = content_model
    for model, fields in models[target_model].items():
        lookups = []
        for field in fields:
            lookups.append(get_lookup(field, versionable))
        yield model, lookups


def get_reference_models(content_model):
    """Yields (model, lookups) tuples, where model
    is a model that can contain references to content_model.
    """
    extension = get_extension()
    yield from _get_reference_models(content_model, extension.reference_models)


def get_reference_plugins(content_model):
    """Yields (model, lookups) tuples, where model
    is a plugin model that can contain references to content_model.
    """
    extension = get_extension()
    yield from _get_reference_models(content_model, extension.reference_plugins)


def get_filters(content, lookups):
    """
    :param content: Content object to create filters against
    :param lookups: A list of lookup strings

    Example:
    poll = Poll.objects.get()
    get_filters(poll, ['poll', 'poll2']) -> Q(poll=poll) | Q(poll2=poll)

    """
    q = Q()
    for lookup in lookups:
        q |= Q(**{lookup: content})
    return q


def _get_reference_objects(content, models_func):
    """Generic generator that yields querysets of models that are
    related to content object.

    :param content: Content object
    :param models_func: A function that takes a content model and returns
                        a list of (model, lookups) tuples returned by
                        _get_reference_models
    """
    for reference in models_func(content.__class__):
        model, lookups = reference
        qs = model.objects.filter(get_filters(content, lookups))
        if qs.exists():
            yield qs


def get_reference_objects(content):
    """Yields querysets of models that are related to provided content object.

    :param content: Content object

    Example:
    poll = Poll.objects.get()
    answer1 = Answer.objects.create(poll=poll)
    answer2 = Answer.objects.create(poll=poll)
    list(get_reference_objects(poll)) ->
    [Answer.objects.filter(pk__in=[1, 2])]
    """
    yield from _get_reference_objects(content, get_reference_models)


def contenttype_values_queryset(queryset):
    """Convert a plugin queryset to a ValuesQuerySet with just
    placeholder.content_type and placeholder.object_id data.

    This is later used to retrieve source objects (objects related to
    placeholders containing these plugins) from the database.

    :param queryset: Plugin queryset
    """
    return (
        queryset.order_by()  # need to clear ordering,
        # as ordering clauses are not allowed in subqueries
        .annotate(
            content_type=F("placeholder__content_type"),
            object_id=F("placeholder__object_id"),
        ).values("content_type", "object_id")
    )


def convert_plugin_querysets_to_sources(querysets):
    """Convert provided plugin querysets to ValuesQuerySets containing
    only source object information and concatenate them into one
    CMSPlugin queryset using UNION.

    :param querysets: List of plugin querysets
    """
    # since plugins use concrete inheritance, it's safe to combine querysets
    # with PKs of different plugin models
    sources = contenttype_values_queryset(CMSPlugin.objects.none())
    for queryset in querysets:
        sources = sources.union(contenttype_values_queryset(queryset))
    return sources.order_by("content_type")


def get_reference_objects_from_plugins(content):
    """Yields querysets of models that are related to provided
    content object through plugins.

    :param content: Content object
    """
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
    """If queryset's model is versionable returns only objects in draft
    and published state. Otherwise, returns the provided queryset.

    :param queryset: A queryset
    """
    versionable = get_versionable_for_content(queryset.model)
    if versionable:
        from djangocms_versioning.constants import DRAFT, PUBLISHED

        return queryset.filter(versions__state__in=(DRAFT, PUBLISHED))
    return queryset


def combine_querysets_of_same_models(*querysets_list):
    """Given multiple arguments (each being a list of querysets),
    returns a single list of querysets, with querysets being
    combined with other querysets of the same model.

    :param `*querysets_list`: Lists of querysets

    Example:
    page_qs1 = Page.objects.filter(pk__in=[1,2,3])
    page_qs2 = Page.objects.filter(pk__in=[3,4,5])
    poll_qs1 = Poll.objects.filter(pk__in=[3,4,5])
    combine_querysets_of_same_models([page_qs1, poll_qs1], [page_qs2])
    -> [page_qs1 | page_qs2, poll_qs1]
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
    """Applies additional queryset modifier functions that have been
    defined in cms config. This is used to extend the available data
    in the the reference list view.

    :param queryset: A queryset
    """
    extension = get_extension()
    for modifier in extension.list_queryset_modifiers:
        queryset = modifier(queryset)
    return queryset


def get_all_reference_objects(content, draft_and_published=False):
    """Retrieves related objects (directly related and through plugins),
    combines the querysets of the same models and applies selected postprocessing
    functions (currently only filtering by version state).

    The end result is a list of querysets of different models,
    that are related to ``content``.

    :param content: Content object
    :param draft_and_published: Set to True if only draft or published
                                objects should be returned
    """
    postprocess = None
    if draft_and_published:
        postprocess = partial(map, filter_only_draft_and_published)
    querysets = combine_querysets_of_same_models(
        get_reference_objects(content), get_reference_objects_from_plugins(content)
    )
    if postprocess:
        querysets = postprocess(querysets)
    return list(apply_additional_modifiers(qs) for qs in querysets)


def version_attr(func):
    """A decorator that turns a function taking a content object into
    a function taking a Version.

    Returns None when content object is not versioned."""

    def inner(obj):
        if get_versionable_for_content(obj):
            return func(obj.versions.all()[0])

    return inner
