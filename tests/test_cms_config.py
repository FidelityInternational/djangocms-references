import importlib
from unittest.mock import Mock, patch

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, RequestFactory, override_settings

from cms import app_registration
from cms.models import PageContent
from cms.toolbar.utils import get_object_preview_url
from cms.utils.setup import configure_cms_apps

from djangocms_references import cms_config
from djangocms_references.test_utils import factories
from djangocms_references.test_utils.app_1.models import Child, Parent
from djangocms_references.test_utils.polls.models import Poll, PollContent


class CMSConfigTestCase(TestCase):
    def test_int_reference_fields_cms_config_parameter(self):
        """CMS config with int as reference_fields as it expect dict object"""
        extensions = cms_config.ReferencesCMSExtension()
        mocked_cms_config = Mock(
            spec=[],
            djangocms_references_enabled=True,
            reference_fields=23234,
            app_config=Mock(label="blah_cms_config"),
        )

        with self.assertRaises(ImproperlyConfigured):
            extensions.configure_app(mocked_cms_config)

    def test_string_reference_fields_cms_config_parameter(self):
        """CMS config with string as reference_fields as it expect dict object"""
        extensions = cms_config.ReferencesCMSExtension()
        mocked_cms_config = Mock(
            spec=[],
            djangocms_references_enabled=True,
            reference_fields="dummy",
            app_config=Mock(label="blah_cms_config"),
        )

        with self.assertRaises(ImproperlyConfigured):
            extensions.configure_app(mocked_cms_config)

    def test_list_reference_fields_cms_config_parameter(self):
        """CMS config with list as reference_fields as it expect dict object"""
        extensions = cms_config.ReferencesCMSExtension()
        mocked_cms_config = Mock(
            spec=[],
            djangocms_references_enabled=True,
            reference_fields=[1, 2],
            app_config=Mock(label="blah_cms_config"),
        )

        with self.assertRaises(ImproperlyConfigured):
            extensions.configure_app(mocked_cms_config)

    def test_valid_cms_config_parameter(self):
        """CMS config with valid configuration"""
        extensions = cms_config.ReferencesCMSExtension()
        mocked_cms_config = Mock(
            spec=[],
            djangocms_references_enabled=True,
            reference_fields={Child.parent},
            app_config=Mock(label="blah_cms_config"),
        )

        extensions.configure_app(mocked_cms_config)
        reference_models = apps.get_app_config(
            "djangocms_references"
        ).cms_extension.reference_models

        self.assertTrue(Child not in reference_models.keys())
        self.assertTrue(Parent in reference_models.keys())
        self.assertTrue(Child in reference_models[Parent])
        self.assertTrue("parent" in reference_models[Parent][Child])


class ModifierTestCase(TestCase):
    def test_versioned(self):
        queryset = PageContent.objects.all()

        with patch(
            "djangocms_references.cms_config.get_versionable_for_content",
            return_value=True,
        ) as mock:
            result = cms_config.version_queryset_modifier(queryset)
        mock.assert_called_once_with(queryset.model)
        self.assertNotEqual(result, queryset)
        self.assertIn("versions", result._prefetch_related_lookups)

    def test_not_versioned(self):
        queryset = PageContent.objects.all()

        with patch(
            "djangocms_references.cms_config.get_versionable_for_content",
            return_value=False,
        ) as mock:
            result = cms_config.version_queryset_modifier(queryset)
        mock.assert_called_once_with(queryset.model)
        self.assertEqual(result, queryset)


class IntegrationTestCase(TestCase):
    def test_config_with_multiple_apps(self):
        reference_models = apps.get_app_config(
            "djangocms_references"
        ).cms_extension.reference_models
        expected_models = [Parent, Poll]

        self.assertCountEqual(reference_models.keys(), expected_models)


class UnpublishDependenciesSettingTestCase(TestCase):

    @patch('djangocms_references.cms_config.get_all_reference_objects')
    def test_unpublish_dependencies(self, mocked_references):
        request = RequestFactory().get('/')
        version = factories.PageVersionFactory()
        polls = factories.PollContentFactory.create_batch(2)
        parent = factories.ParentFactory()
        mocked_references.return_value = [
            PollContent.objects.all(),  # this has 2 polls
            Child.objects.all(),  # this is an empty queryset
            Parent.objects.all(),  # this has 1 parent
        ]

        html = cms_config.unpublish_dependencies(request, version)

        mocked_references.assert_called_once_with(
            version.content, draft_and_published=True)
        # NOTE: This is not an extensive test of the html, but testing for
        # exact html will likely be a pain later (making this test
        # break easily and make it difficult to maintain)
        self.assertIn(get_object_preview_url(polls[0]), html)
        self.assertIn(get_object_preview_url(polls[1]), html)
        self.assertIn(get_object_preview_url(parent), html)

    @patch('djangocms_references.cms_config.get_all_reference_objects')
    def test_unpublish_dependencies_when_no_dependencies_found(self, mocked_references):
        request = RequestFactory().get('/')
        version = factories.PageVersionFactory()
        mocked_references.return_value = [
            # All these querysets are empty
            PollContent.objects.none(),
            Child.objects.none(),
            Parent.objects.none(),
        ]

        html = cms_config.unpublish_dependencies(request, version)

        mocked_references.assert_called_once_with(
            version.content, draft_and_published=True)
        self.assertIn("No related objects", html)

    @patch('djangocms_references.cms_config.get_all_reference_objects')
    def test_unpublish_dependencies_when_no_dependencies_registered(self, mocked_references):
        request = RequestFactory().get('/')
        version = factories.PageVersionFactory()
        # No models have relations so no querysets are added
        mocked_references.return_value = []

        html = cms_config.unpublish_dependencies(request, version)

        mocked_references.assert_called_once_with(
            version.content, draft_and_published=True)
        self.assertIn("No related objects", html)


class VersioningSettingTestCase(TestCase):
    def setUp(self):
        self.versioning_app = apps.get_app_config('djangocms_versioning')
        # Empty the context dict so it gets populated
        # from scratch in tests (but save original values first)
        self.add_to_context = self.versioning_app.cms_extension.add_to_context
        self.versioning_app.cms_extension.add_to_context = {}

    def tearDown(self):
        """Populate everything again so our setting changes do not
        effect any other tests"""
        # Set the defaults for the navigation app config again
        importlib.reload(cms_config)
        # Repopulate add_to_context in the app registry
        self.versioning_app.cms_extension.add_to_context = self.add_to_context

    def test_references_has_versioning_enabled_by_default(self):
        importlib.reload(cms_config)  # Reload so setting gets checked again
        # The app should have a cms config with the overridden setting
        references_app = apps.get_app_config('djangocms_references')
        references_app.cms_config = cms_config.ReferencesCMSAppConfig(references_app)

        with patch.object(app_registration, 'get_cms_config_apps', return_value=[references_app]):
            configure_cms_apps([self.versioning_app])

        expected = {
            'unpublish': {'unpublish_dependencies': cms_config.unpublish_dependencies}
        }
        self.assertDictEqual(self.versioning_app.cms_extension.add_to_context, expected)

    @override_settings(DJANGOCMS_REFERENCES_VERSIONING_ENABLED=True)
    def test_references_has_versioning_enabled_if_setting_true(self):
        importlib.reload(cms_config)  # Reload so setting gets checked again
        # The app should have a cms config with the overridden setting
        references_app = apps.get_app_config('djangocms_references')
        references_app.cms_config = cms_config.ReferencesCMSAppConfig(references_app)

        with patch.object(app_registration, 'get_cms_config_apps', return_value=[references_app]):
            configure_cms_apps([self.versioning_app])

        expected = {
            'unpublish': {'unpublish_dependencies': cms_config.unpublish_dependencies}
        }
        self.assertDictEqual(self.versioning_app.cms_extension.add_to_context, expected)

    @override_settings(DJANGOCMS_REFERENCES_VERSIONING_ENABLED=False)
    def test_references_has_versioning_disabled_if_setting_false(self):
        importlib.reload(cms_config)  # Reload so setting gets checked again
        # The app should have a cms config with the overridden setting
        references_app = apps.get_app_config('djangocms_references')
        references_app.cms_config = cms_config.ReferencesCMSAppConfig(references_app)

        with patch.object(app_registration, 'get_cms_config_apps', return_value=[references_app]):
            configure_cms_apps([self.versioning_app])

        self.assertDictEqual(self.versioning_app.cms_extension.add_to_context, {})
