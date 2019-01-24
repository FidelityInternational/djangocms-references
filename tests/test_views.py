from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import reverse
from django.test import RequestFactory
from django.test.utils import override_settings

from cms.api import add_plugin
from cms.test_utils.testcases import CMSTestCase

import djangocms_references.urls
from djangocms_references.test_utils.factories import (
    AliasContentFacotry,
    AliasPluginFactory,
    PageContentFactory,
    PlaceholderFactory,
)
from djangocms_references.views import ReferencesView


urlpatterns = [
    url(r"^references/", include(djangocms_references.urls)),
    url(r"^admin/", admin.site.urls),
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

    def test_view_endpoint_access_with_anonymous_user(self):
        response = self.client.get(self.view_url)
        redirect_url = "/admin/login/?next=" + self.view_url
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, redirect_url)

    def test_view_endpoint_access_with_superuser(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.view_url)
            self.assertEqual(response.status_code, 200)

    def test_view_endpoint_standard_user_permission(self):
        standard_user = self.get_standard_user()
        with self.login_user_context(standard_user):
            response = self.client.get(self.view_url)
            redirect_url = "/admin/login/?next=" + self.view_url
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, redirect_url)

    def test_view_endpoint_access_staff_user(self):
        staff_user = self.get_staff_user_with_no_permissions()
        with self.login_user_context(staff_user):
            response = self.client.get(self.view_url)
            self.assertEqual(response.status_code, 200)

    def test_view_expected_querysets_exists_in_context(self):
        request = self.factory.get(self.view_url)
        request.user = self.superuser

        view = ReferencesView()
        view.request = request
        view.kwargs = {"content_type_id": self.content.id, "object_id": self.page.id}
        response = view.get_context_data()
        self.assertIn("querysets", response)

    def test_context_data_has_related_alias_in_querysets(self):
        request = self.factory.get(self.view_url)
        request.user = self.superuser

        # Two alias plugins attached to alias
        alias_content = AliasContentFacotry()
        alias_plugin_1 = AliasPluginFactory(alias=alias_content.alias)
        alias_plugin_2 = AliasPluginFactory(alias=alias_content.alias)

        view = ReferencesView()
        view.request = request
        view.kwargs = {
            "content_type_id": ContentType.objects.get_for_model(
                alias_plugin_1.alias
            ).pk,
            "object_id": alias_plugin_1.alias.id,
        }
        response = view.get_context_data()

        self.assertIn("querysets", response)

        # two plugins should appear in plugin_queryset
        self.assertEqual(response["querysets"][0].count(), 2)

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
        )

        view = ReferencesView()
        view.request = request
        view.kwargs = {
            "content_type_id": ContentType.objects.get_for_model(
                alias_plugin1.alias
            ).pk,
            "object_id": alias_content.alias.id,
        }
        response = view.get_context_data()

        self.assertIn("querysets", response)
        # print(response["querysets"])
        # three plugin should be related to alias
        self.assertEqual(response["querysets"][0].count(), 3)
