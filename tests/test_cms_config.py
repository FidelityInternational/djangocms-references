from unittest.mock import Mock

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from djangocms_references.cms_config import ReferencesCMSExtension
from djangocms_references.test_utils.app_1.models import Child, Parent
from djangocms_references.test_utils.polls.models import Poll


class CMSConfigTestCase(TestCase):
    def test_int_reference_fields_cms_config_parameter(self):
        """CMS config with int as reference_fields as it expect dict object"""
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
        """CMS config with string as reference_fields as it expect dict object"""
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
        """CMS config with list as reference_fields as it expect dict object"""
        extensions = ReferencesCMSExtension()
        cms_config = Mock(
            spec=[],
            djangocms_references_enabled=True,
            reference_fields=[1, 2],
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
            reference_fields={Child.parent},
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


class IntegrationTestCase(TestCase):
    def test_config_with_multiple_apps(self):
        reference_models = apps.get_app_config(
            "djangocms_references"
        ).cms_extension.reference_models
        expected_models = [Parent, Poll]

        self.assertCountEqual(reference_models.keys(), expected_models)
