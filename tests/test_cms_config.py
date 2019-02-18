from unittest.mock import Mock, patch

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from cms.models import PageContent

from djangocms_references.cms_config import (
    ReferencesCMSExtension,
    version_queryset_modifier,
)
from djangocms_references.test_utils.app_1.models import Child, Parent
from djangocms_references.test_utils.polls.models import Poll


class CMSConfigTestCase(TestCase):
    def test_int_reference_fields_cms_config_parameter(self):
        """CMS config with int as reference_fields as it expects
        a list of tuples with two elements"""
        extensions = ReferencesCMSExtension()
        cms_config = Mock(
            spec=[],
            djangocms_references_enabled=True,
            reference_fields=23234,
            app_config=Mock(label="blah_cms_config"),
        )

        with self.assertRaises(ImproperlyConfigured):
            extensions.configure_app(cms_config)

    def test_string_reference_fields_cms_config_parameter(self):
        """CMS config with string as reference_fields as it expects
        a list of tuples with two elements"""
        extensions = ReferencesCMSExtension()
        cms_config = Mock(
            spec=[],
            djangocms_references_enabled=True,
            reference_fields="dummy",
            app_config=Mock(label="blah_cms_config"),
        )

        with self.assertRaises(ImproperlyConfigured):
            extensions.configure_app(cms_config)

    def test_list_reference_fields_cms_config_parameter(self):
        """CMS config with list of ints as reference_fields as it expects
        a list of tuples with two elements"""
        extensions = ReferencesCMSExtension()
        cms_config = Mock(
            spec=[],
            djangocms_references_enabled=True,
            reference_fields=[1, 2],
            app_config=Mock(label="blah_cms_config"),
        )

        with self.assertRaises(ImproperlyConfigured):
            extensions.configure_app(cms_config)

    def test_list_with_tuples_with_incorrect_number_of_elements_reference_fields_cms_config_parameter(self):
        """CMS config with list of tuples with three elements as it expects
        a list of tuples with two elements"""
        extensions = ReferencesCMSExtension()
        cms_config = Mock(
            spec=[],
            djangocms_references_enabled=True,
            reference_fields=[(Child, "a field", "too many")],
            app_config=Mock(label="blah_cms_config"),
        )

        with self.assertRaises(ImproperlyConfigured):
            extensions.configure_app(cms_config)

    def test_valid_cms_config_parameter(self):
        """CMS config with valid configuration"""
        extensions = ReferencesCMSExtension()
        cms_config = Mock(
            spec=[],
            djangocms_references_enabled=True,
            reference_fields=[(Child, "parent")],
            app_config=Mock(label="blah_cms_config"),
        )

        extensions.configure_app(cms_config)
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
            result = version_queryset_modifier(queryset)
        mock.assert_called_once_with(queryset.model)
        self.assertNotEqual(result, queryset)
        self.assertIn("versions", result._prefetch_related_lookups)

    def test_not_versioned(self):
        queryset = PageContent.objects.all()

        with patch(
            "djangocms_references.cms_config.get_versionable_for_content",
            return_value=False,
        ) as mock:
            result = version_queryset_modifier(queryset)
        mock.assert_called_once_with(queryset.model)
        self.assertEqual(result, queryset)


class IntegrationTestCase(TestCase):
    def test_config_with_multiple_apps(self):
        reference_models = apps.get_app_config(
            "djangocms_references"
        ).cms_extension.reference_models
        expected_models = [Parent, Poll]

        self.assertCountEqual(reference_models.keys(), expected_models)
