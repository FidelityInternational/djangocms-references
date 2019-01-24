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
    PageContentFactory,
    PlaceholderFactory,
    PollContentFactory,
    PollFactory,
    PollPluginFactory,
)
from djangocms_references.test_utils.polls.models import PollPlugin
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

    def test_view_response_should_contain_querysets(self):
        request = self.factory.get(self.view_url)
        request.user = self.superuser
        request.GET = {"state": "draft_and_published"}
        view = ReferencesView()
        view.request = request
        view.kwargs = {"content_type_id": self.content.id, "object_id": self.page.id}
        response = view.get_context_data()

        self.assertIn("querysets", response)

    def test_view_assigning_three_child_to_one_parent(self):
        request = self.factory.get(self.view_url)
        request.user = self.superuser
        request.GET = {"state": "draft_and_published"}

        # Three poll content attached to poll
        poll = PollFactory()
        poll_content_1 = PollContentFactory(poll=poll)  # flake8: noqa
        poll_content_2 = PollContentFactory(poll=poll)  # flake8: noqa
        poll_content_3 = PollContentFactory(poll=poll)  # flake8: noqa

        view = ReferencesView()
        view.request = request

        view.kwargs = {
            "content_type_id": ContentType.objects.get_for_model(poll).pk,
            "object_id": poll.id,
        }
        response = view.get_context_data()

        self.assertIn("querysets", response)

        # three poll content objects should appear in querysets
        self.assertEqual(len(response["querysets"]), 3)

    def test_view_poll_plugin_attached_to_page_should_return_related_page(self):
        request = self.factory.get(self.view_url)
        request.GET = {"state": "draft_and_published"}
        request.user = self.superuser

        pagecontent = PageContentFactory(title="test", language=self.language)
        page = pagecontent.page
        placeholder = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page), object_id=page.id
        )

        poll = PollFactory()
        # Attach poll plugin to page
        poll_plugin_1 = add_plugin(
            placeholder, "PollPlugin", "en", poll=poll, template=0
        )

        view = ReferencesView()
        view.request = request
        view.kwargs = {
            "content_type_id": ContentType.objects.get_for_model(poll_plugin_1).pk,
            "object_id": poll_plugin_1.id,
        }
        response = view.get_context_data()

        self.assertIn("querysets", response)

        # queryset should contain page
        self.assertEqual(len(response["querysets"]), 1)
