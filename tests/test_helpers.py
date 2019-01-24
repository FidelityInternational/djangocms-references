from unittest import skipIf
from unittest.mock import Mock, patch

from django.apps import apps
from django.db.models import Q
from django.test import TestCase

from djangocms_references import helpers
from djangocms_references.compat import DJANGO_GTE_21
from djangocms_references.helpers import (
    _get_reference_models,
    get_all_reference_objects,
    get_extension,
    get_filters,
    get_reference_models,
    get_reference_plugins,
    get_relation,
)
from djangocms_references.test_utils.app_1.models import (
    Child,
    Parent,
    UnknownChild,
)


class GetRelationTestCase(TestCase):
    def test_get_relation_non_versioned(self):
        self.assertEqual(get_relation("foo", None), "foo")

    def test_get_relation_versioned(self):
        versionable = Mock(
            grouper_field=Mock(
                remote_field=Mock(get_accessor_name=Mock(return_value="bar"))
            )
        )
        self.assertEqual(get_relation("foo", versionable), "foo__bar")


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
        ), patch.object(helpers, "_get_reference_models") as inner:
            list(get_reference_models("foo"))
            inner.assert_called_once_with("foo", extension.reference_models)

    def test_get_reference_plugins(self):
        extension = Mock()
        with patch.object(
            helpers, "get_extension", return_value=extension
        ), patch.object(helpers, "_get_reference_models") as inner:
            list(get_reference_plugins("foo"))
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
