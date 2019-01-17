from unittest.mock import Mock

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from cms.models import Page

from djangocms_references.cms_config import ReferencesCMSExtension
from djangocms_references.test_utils.app_1.models import TestModel1, TestModel2
from djangocms_references.test_utils.app_2.models import TestModel3, TestModel4


class CMSConfigTestCase(TestCase):
    def test_missing_cms_config(self):
        """CMS config with missing reference_model attributes"""
        extensions = ReferencesCMSExtension()
        cms_config = Mock(
            djangocms_referencess_enabled=True, app_config=Mock(label="blah_cms_config")
        )

        with self.assertRaises(ImproperlyConfigured):
            extensions.configure_app(cms_config)

    def test_int_reference_models_cms_config_parameter(self):
        """CMS config with int as reference_models as it expect dict object"""
        extensions = ReferencesCMSExtension()
        cms_config = Mock(
            djangocms_referencess_enabled=True,
            reference_models=23234,
            app_config=Mock(label="blah_cms_config"),
        )

        with self.assertRaises(ImproperlyConfigured):
            extensions.configure_app(cms_config)

    def test_string_reference_models_cms_config_parameter(self):
        """CMS config with string as reference_models as it expect dict object"""
        extensions = ReferencesCMSExtension()
        cms_config = Mock(
            djangocms_referencess_enabled=True,
            reference_models="dummy",
            app_config=Mock(label="blah_cms_config"),
        )

        with self.assertRaises(ImproperlyConfigured):
            extensions.configure_app(cms_config)

    def test_list_reference_models_cms_config_parameter(self):
        """CMS config with list as reference_models as it expect dict object"""
        extensions = ReferencesCMSExtension()
        cms_config = Mock(
            djangocms_referencess_enabled=True,
            reference_models=[1, 2],
            app_config=Mock(label="blah_cms_config"),
        )

        with self.assertRaises(ImproperlyConfigured):
            extensions.configure_app(cms_config)

    def test_valid_cms_config_parameter(self):
        """CMS config with valid configuration"""
        extensions = ReferencesCMSExtension()
        cms_config = Mock(
            djangocms_referencess_enabled=True,
            reference_models={
                TestModel1: [],
                TestModel2: [],
                TestModel3: [],
                TestModel4: [],
            },
            app_config=Mock(label="blah_cms_config"),
        )

        extensions.configure_app(cms_config)
        references_app_models = apps.get_app_config(
            "djangocms_references"
        ).cms_extension.references_app_models

        self.assertTrue(TestModel1 in references_app_models.keys())
        self.assertTrue(TestModel2 in references_app_models.keys())
        self.assertTrue(TestModel3 in references_app_models.keys())
        self.assertTrue(TestModel4 in references_app_models.keys())


class IntegrationTestCase(TestCase):
    def test_config_with_multiple_apps(self):
        references_app_models = apps.get_app_config(
            "djangocms_references"
        ).cms_extension.references_app_models
        expected_models = [TestModel1, TestModel2, TestModel3, TestModel4, Page]

        self.assertCountEqual(references_app_models.keys(), expected_models)
