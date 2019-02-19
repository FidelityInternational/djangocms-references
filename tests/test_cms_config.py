from unittest.mock import Mock, patch

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, RequestFactory

from cms.models import PageContent

from djangocms_references.cms_config import (
    ReferencesCMSExtension,
    version_queryset_modifier,
    unpublish_dependencies,
)
from djangocms_references.test_utils import factories
from djangocms_references.test_utils.app_1.models import Child, Parent
from djangocms_references.test_utils.polls.models import Poll, PollContent


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

        html = unpublish_dependencies(request, version)

        mocked_references.assert_called_once_with(
            version.content, draft_and_published=True)
        expected = """<div>
    The following objects have relationships with the object you're about to unpublish:
    <ul>
    
        
        <li>{poll1}</li>
        
        <li>{poll2}</li>
        
    
        
    
        
        <li>{parent}</li>
        
    
    </ul>
</div>
""".format(poll1=str(polls[0]), poll2=str(polls[1]), parent=str(parent))
        self.assertEqual(html, expected)

    @patch('djangocms_references.cms_config.get_all_reference_objects')
    def test_unpublish_dependencies_when_no_dependencies_found(self, mocked_references):
        request = RequestFactory().get('/')
        version = factories.PageVersionFactory()
        mocked_references.return_value = [
            # All these querysets are empty
            PollContent.objects.all(),
            Child.objects.all(),
            Parent.objects.all(),
        ]

        html = unpublish_dependencies(request, version)

        mocked_references.assert_called_once_with(
            version.content, draft_and_published=True)
        self.assertEqual(html, '')
