from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import reverse
from django.test import RequestFactory
from django.test.utils import override_settings

from cms.test_utils.testcases import CMSTestCase

import djangocms_references.urls
from djangocms_references.test_utils.factories import (
    PageContentFactory,
    PollContentFactory,
    PollFactory,
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

    def test_view_response_should_contain_querysets(self):
        request = self.factory.get(self.view_url)
        request.user = self.superuser
        request.GET = {"state": "draft_and_published"}
        view = ReferencesView()
        view.request = request
        view.kwargs = {"content_type_id": self.content.id, "object_id": self.page.id}
        response = view.get_context_data()

        self.assertIn("querysets", response)

    def test_context_data_has_related_poll_in_querysets(self):
        request = self.factory.get(self.view_url)
        request.user = self.superuser
        request.GET = {"state": "draft_and_published"}
        # Two poll plugins attached to poll
        poll = PollFactory()
        poll_content_1 = PollContentFactory(poll=poll)
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

        # three pollcontent should appear in querysets
        self.assertEqual(len(response["querysets"]), 3)

    #
    # def test_view_get_context_data_related_poll_with_page(self):
    #     request = self.factory.get(self.view_url)
    #     request['GET']= {
    #         'state': 'draft_and_published',
    #         'draft_and_published': True,
    #     }
    #     request.user = self.superuser
    #
    #     # three different poll plugins attached to poll
    #     # pagecontent = PageContentFactory(title="test", language=self.language)
    #     # page = pagecontent.page
    #     # placeholder = PlaceholderFactory(
    #     #     content_type=ContentType.objects.get_for_model(page), object_id=page.id
    #     # )
    #
    #     poll_content = PollsContentFactory()
    #     poll_plugin1 = PollsPluginFactory(polls=poll_content.polls)
    #     poll_plugin2 = PollsPluginFactory(polls=poll_content.polls)
    #
    #     view = ReferencesView()
    #     view.request = request
    #     view.kwargs = {
    #         "content_type_id": ContentType.objects.get_for_model(
    #             poll_plugin1.polls
    #         ).pk,
    #         "object_id": poll_content.polls.id,
    #     }
    #     response = view.get_context_data()
    #
    #     self.assertIn("querysets", response)
    #     # print(response["querysets"])
    #     # three plugin should be related to poll
    #     self.assertEqual(response["querysets"][0].count(), 3)
