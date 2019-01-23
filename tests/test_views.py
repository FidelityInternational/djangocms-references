from django.conf import settings
from django.conf.urls import include, url
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import reverse
from django.test import Client, RequestFactory
from django.test.utils import override_settings

from cms.api import add_plugin
from cms.models import Placeholder
from cms.test_utils.testcases import CMSTestCase

from djangocms_references.views import ReferencesView

from .factories import (
    AliasContentFacotry,
    AliasPluginFactory,
    PageContentFactory,
    PlaceholderFactory,
)


urlpatterns = [
    url(
        r"^references/",
        include("djangocms_references.urls", namespace="djangocms_references"),
    )
]


@override_settings(ROOT_URLCONF=__name__)
class ReferencesViewTestCases(CMSTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.superuser = self.get_superuser()
        self.page = PageContentFactory()
        self.content = ContentType.objects.get_for_model(self.page)
        self.view_url = reverse(
            "djangocms_references:references-index",
            kwargs={"content_type_id": self.content.pk, "object_id": self.page.id},
        )
        self.language = "en"

    def test_view_expected_querysets_exists_in_context(self):
        request = self.factory.get(self.view_url)
        request.user = self.superuser

        view = ReferencesView(template_name="djagnocms_references/index.html")
        view.kwargs = {"content_type_id": self.content.id, "object_id": self.page.id}
        response = view.get_context_data()
        self.assertIn("querysets", response)
        self.assertIn("plugin_querysets", response)

    def test_context_data_has_related_alias_in_querysets(self):
        request = self.factory.get(self.view_url)
        request.user = self.superuser

        # Two alias plugins attached to alias
        alias_content = AliasContentFacotry()
        alias_plugin_1 = AliasPluginFactory(alias=alias_content.alias)
        alias_plugin_2 = AliasPluginFactory(alias=alias_content.alias)

        view = ReferencesView(template_name="djagnocms_references/index.html")
        view.kwargs = {
            "content_type_id": ContentType.objects.get_for_model(
                alias_plugin_1.alias
            ).pk,
            "object_id": alias_plugin_1.alias.id,
        }
        response = view.get_context_data()

        self.assertIn("querysets", response)
        self.assertIn("plugin_querysets", response)

        self.assertEqual(len(response["querysets"]), 0)

        # two plugins should appear in plugin_queryset
        self.assertEqual(response["plugin_querysets"][0].count(), 2)

    def test_view_get_context_data_related_alias_with_page(self):
        request = self.factory.get(self.view_url)
        request.user = self.superuser

        # three different alias plugins attached to alias
        pagecontent = PageContentFactory(title="test", language=self.language)
        page = pagecontent.page
        placeholder = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page), object_id=page.id
        )
        alias_content = AliasContentFacotry()
        alias_plugin1 = AliasPluginFactory(alias=alias_content.alias)
        alias_plugin2 = AliasPluginFactory(alias=alias_content.alias)

        # adding plugin using api should reflect in response
        add_plugin(
            placeholder, "Alias", language=self.language, alias=alias_content.alias
        )  # flake8: noqa

        view = ReferencesView(template_name="djagnocms_references/index.html")
        view.kwargs = {
            "content_type_id": ContentType.objects.get_for_model(
                alias_plugin1.alias
            ).pk,
            "object_id": alias_content.id,
        }
        response = view.get_context_data()

        self.assertIn("querysets", response)
        self.assertIn("plugin_querysets", response)

        # three plugin should be related to alias
        self.assertEqual(response["plugin_querysets"][0].count(), 3)
