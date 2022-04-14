from unittest import skipIf
from unittest.mock import Mock, patch

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.test import TestCase

from cms.api import add_plugin

from djangocms_references import helpers
from djangocms_references.compat import DJANGO_GTE_21
from djangocms_references.helpers import (
    _get_reference_models,
    combine_querysets_of_same_models,
    get_all_reference_objects,
    get_extension,
    get_filters,
    get_lookup,
    get_reference_models,
    get_reference_objects_from_plugins,
    get_reference_plugins,
    get_versionable_for_content,
    version_attr,
)
from djangocms_references.test_utils.app_1.models import (
    Child,
    Parent,
    UnknownChild,
)
from djangocms_references.test_utils.factories import (
    PageContentFactory,
    PageVersionFactory,
    PlaceholderFactory,
    PollFactory,
)


class GetVersionableTestCase(TestCase):
    def test_get_versionable_for_content_no_versioning(self):
        with patch.dict("sys.modules", {"djangocms_versioning": None}):
            self.assertIsNone(get_versionable_for_content("foo"))


class GetLookupTestCase(TestCase):
    def test_get_lookup_non_versioned(self):
        self.assertEqual(get_lookup("foo", None), "foo")

    def test_get_lookup_versioned(self):
        versionable = Mock(
            grouper_field=Mock(
                remote_field=Mock(get_accessor_name=Mock(return_value="bar"))
            )
        )
        self.assertEqual(get_lookup("foo", versionable), "foo__bar")


class GetExtensionTestCase(TestCase):
    def setUp(self):
        get_extension.cache_clear()

    def tearDown(self):
        get_extension.cache_clear()

    def test_get_extension(self):
        models = ["Foo", "Bar"]
        app_config = Mock(
            spec=[], cms_extension=Mock(spec=[], navigation_apps_models=models)
        )
        with patch.object(apps, "get_app_config", return_value=app_config):
            self.assertEqual(get_extension(), app_config.cms_extension)

    def test_get_extension_is_cached(self):
        models = ["Foo", "Bar"]
        app_config = Mock(
            spec=[], cms_extension=Mock(spec=[], navigation_apps_models=models)
        )
        with patch.object(apps, "get_app_config", return_value=app_config):
            get_extension()
        with patch.object(apps, "get_app_config") as mock:
            get_extension()
            mock.assert_not_called()


class GetReferenceModelsTestCase(TestCase):
    def test_get_reference_models(self):
        extension = Mock()
        with patch.object(
            helpers, "get_extension", return_value=extension
        ), patch.object(
            helpers, "_get_reference_models", return_value=["1", "2"]
        ) as inner:
            self.assertEqual(list(get_reference_models("foo")), ["1", "2"])
            inner.assert_called_once_with("foo", extension.reference_models)

    def test_get_reference_plugins(self):
        extension = Mock()
        with patch.object(
            helpers, "get_extension", return_value=extension
        ), patch.object(
            helpers, "_get_reference_models", return_value=["1", "2"]
        ) as inner:
            self.assertEqual(list(get_reference_plugins("foo")), ["1", "2"])
            inner.assert_called_once_with("foo", extension.reference_plugins)

    def test__get_reference_models(self):
        self.assertEqual(
            list(_get_reference_models(Parent, {Parent: {Child: ["parent"]}})),
            [(Child, ["parent"])],
        )

    def test__get_reference_models_multiple_fields(self):
        self.assertEqual(
            list(_get_reference_models(Parent, {Parent: {Child: ["parent", "foo"]}})),
            [(Child, ["parent", "foo"])],
        )

    def test__get_reference_models_versioned(self):
        versionable = Mock(
            grouper_model="GrouperModel",
            grouper_field=Mock(
                remote_field=Mock(get_accessor_name=Mock(return_value="contentmodel"))
            ),
        )
        with patch.object(
            helpers, "get_versionable_for_content", return_value=versionable
        ):
            self.assertEqual(
                list(
                    _get_reference_models(
                        Parent, {"GrouperModel": {Child: ["parent", "foo"]}}
                    )
                ),
                [(Child, ["parent__contentmodel", "foo__contentmodel"])],
            )


@skipIf(
    not DJANGO_GTE_21,
    "Reliable Q object comparison is available starting with Django 2.1",
)
class GetFiltersTestCase(TestCase):
    def test_get_filters_empty(self):
        self.assertEqual(get_filters("foo", []), Q())

    def test_get_filters(self):
        self.assertEqual(get_filters("foo", ["bar"]), Q(bar="foo"))

    def test_get_filters_multiple(self):
        self.assertEqual(
            get_filters("foo", ["bar", "baz"]), Q(bar="foo") | Q(baz="foo")
        )


class GetReferenceObjectsTestCase(TestCase):
    def test_get_all_reference_objects(self):
        parent = Parent.objects.create()
        child1 = Child.objects.create(parent=parent)
        child2 = Child.objects.create(parent=parent)
        child3 = UnknownChild.objects.create(parent=parent)
        querysets = get_all_reference_objects(parent)
        self.assertEqual(len(querysets), 1)
        self.assertIn(Child, [qs.model for qs in querysets])
        self.assertNotIn(UnknownChild, [qs.model for qs in querysets])
        self.assertIn(child1, querysets[0])
        self.assertIn(child2, querysets[0])
        self.assertNotIn(child3, querysets[0])

    def test_get_reference_objects_from_plugins(self):
        page_content = PageContentFactory(title="test", language="en")
        placeholder = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_content),
            object_id=page_content.id,
        )
        poll = PollFactory()
        add_plugin(placeholder, "PollPlugin", "en", poll=poll, template=0)

        querysets = list(get_reference_objects_from_plugins(poll))
        self.assertEqual(len(querysets), 1)
        self.assertIn(page_content, querysets[0])


class CombineQuerysetsTestCase(TestCase):
    def test_combine_querysets_of_same_models(self):
        class MockQueryset:
            def __init__(self, model, extra_state=None):
                self.model = model
                self._state = []
                if extra_state:
                    self._state.extend(extra_state)

            def __repr__(self):
                return "<MockQueryset {model} ({state})>".format(
                    model=self.model, state=self._state
                )

            def __or__(self, other):
                if self.model != other.model:
                    raise ValueError("Cannot combine querysets of different models")
                return MockQueryset(self.model, self._state + [other] + other._state)

            def __eq__(self, other):
                return self.model == other.model and self._state == other._state

            def __hash__(self):
                return hash(self.__repr__())

        foo_qs1 = MockQueryset("Foo")
        foo_qs2 = MockQueryset("Foo")
        bar_qs1 = MockQueryset("Bar")
        bar_qs2 = MockQueryset("Bar")
        baz_qs1 = MockQueryset("Baz")
        result = set(
            combine_querysets_of_same_models(
                [foo_qs1], [foo_qs2, bar_qs1], [baz_qs1, bar_qs2]
            )
        )
        self.assertEqual(result, set([foo_qs1 | foo_qs2, bar_qs1 | bar_qs2, baz_qs1]))


class VersionAttrTestCase(TestCase):
    def test_versioned(self):
        version = PageVersionFactory()

        func = Mock()
        decorated = version_attr(func)

        with patch(
            "djangocms_references.helpers.get_versionable_for_content",
            return_value=True,
        ) as mock:
            result = decorated(version.content)
            mock.assert_called_once_with(version.content)
            func.assert_called_once_with(version)
            self.assertEqual(result, func.return_value)

    def test_not_versioned(self):
        content = PageContentFactory()

        func = Mock()
        decorated = version_attr(func)

        with patch(
            "djangocms_references.helpers.get_versionable_for_content",
            return_value=False,
        ) as mock:
            result = decorated(content)
            mock.assert_called_once_with(content)
            func.assert_not_called()
            self.assertIsNone(result)
