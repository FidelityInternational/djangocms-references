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

    def test_view_invalid_content_type(self):
        request = self.factory.get(self.view_url)
        request.user = self.superuser
        view = ReferencesView()
        view.request = request
        view.kwargs = {"content_type_id": 0, "object_id": 1}
        response = view.get_context_data()

        self.assertEqual(response.status_code, 400)

    def test_view_invalid_content_type_type(self):
        request = self.factory.get(self.view_url)
        request.user = self.superuser
        view = ReferencesView()
        view.request = request
        view.kwargs = {"content_type_id": "foo", "object_id": 1}
        response = view.get_context_data()

        self.assertEqual(response.status_code, 400)

    def test_view_invalid_object(self):
        request = self.factory.get(self.view_url)
        request.user = self.superuser
        view = ReferencesView()
        view.request = request
        view.kwargs = {"content_type_id": self.content.id, "object_id": 0}
        response = view.get_context_data()

        self.assertEqual(response.status_code, 400)

    def test_view_invalid_object_id_type(self):
        request = self.factory.get(self.view_url)
        request.user = self.superuser
        view = ReferencesView()
        view.request = request
        view.kwargs = {"content_type_id": self.content.id, "object_id": "foo"}
        response = view.get_context_data()

        self.assertEqual(response.status_code, 400)

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
        poll_content_4 = PollContentFactory(poll=PollFactory())  # flake8: noqa

        view = ReferencesView()
        view.request = request

        view.kwargs = {
            "content_type_id": ContentType.objects.get_for_model(poll).pk,
            "object_id": poll.id,
        }
        response = view.get_context_data()

        self.assertIn("querysets", response)

        # three poll content objects should appear in querysets
        self.assertEqual(response["querysets"][0].count(), 3)
        self.assertIn(poll_content_1, response["querysets"][0])
        self.assertIn(poll_content_2, response["querysets"][0])
        self.assertIn(poll_content_3, response["querysets"][0])

        # poll_content_4 shouldn't be in queryset
        self.assertNotIn(poll_content_4, response["querysets"][0])
