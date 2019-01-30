from unittest.mock import patch

from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import reverse
from django.test import RequestFactory
from django.test.utils import override_settings

from cms.api import add_plugin
from cms.test_utils.testcases import CMSTestCase

import djangocms_references.urls
from djangocms_references.datastructures import ExtraColumn
from djangocms_references.test_utils.factories import (
    PageContentFactory,
    PageVersionFactory,
    PlaceholderFactory,
    PollContentFactory,
    PollFactory,
)


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
        self.view_url = self.get_view_url(self.content.pk, self.page.id)
        self.language = "en"

    def get_view_url(self, content_type_id, object_id):
        return reverse(
            "djangocms_references:references-index",
            kwargs={"content_type_id": content_type_id, "object_id": object_id},
        )

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
        with self.login_user_context(self.superuser):
            response = self.client.get(
                self.get_view_url(content_type_id=0, object_id=1)
            )
        self.assertEqual(response.status_code, 404)

    def test_view_invalid_object(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(
                self.get_view_url(content_type_id=self.content.id, object_id=0)
            )
        self.assertEqual(response.status_code, 404)

    def test_view_response_should_contain_querysets(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("querysets", response.context)

    def test_view_assigning_three_child_to_one_parent(self):
        poll = PollFactory()
        poll_content_1 = PollContentFactory(poll=poll)
        poll_content_2 = PollContentFactory(poll=poll)
        poll_content_3 = PollContentFactory(poll=poll)
        poll_content_4 = PollContentFactory()

        with self.login_user_context(self.superuser):
            response = self.client.get(
                self.get_view_url(
                    content_type_id=ContentType.objects.get_for_model(poll).pk,
                    object_id=poll.id,
                )
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("querysets", response.context)

        # three poll content objects should appear in querysets
        self.assertEqual(response.context["querysets"][0].count(), 3)
        self.assertIn(poll_content_1, response.context["querysets"][0])
        self.assertIn(poll_content_2, response.context["querysets"][0])
        self.assertIn(poll_content_3, response.context["querysets"][0])

        # poll_content_4 shouldn't be in queryset
        self.assertNotIn(poll_content_4, response.context["querysets"][0])

    def test_view_poll_plugin_attached_to_page_should_return_related_page(self):
        version = PageVersionFactory(
            content__title="test", content__language=self.language
        )
        page_content = version.content
        placeholder = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_content),
            object_id=page_content.id,
        )

        poll = PollFactory()
        # add poll plugin to page
        add_plugin(placeholder, "PollPlugin", "en", poll=poll, template=0)

        with self.login_user_context(self.superuser):
            response = self.client.get(
                self.get_view_url(
                    content_type_id=ContentType.objects.get_for_model(poll).pk,
                    object_id=poll.id,
                )
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("querysets", response.context)

        # queryset should contain page
        self.assertEqual(response.context["querysets"][0].count(), 1)
        self.assertIn(page_content, response.context["querysets"][0])

    def test_view_draft_and_published(self):
        poll = PollFactory()

        archived = PageVersionFactory()
        placeholder1 = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(archived.content),
            object_id=archived.content.id,
        )
        add_plugin(placeholder1, "PollPlugin", "en", poll=poll, template=0)

        version2 = archived.copy(archived.created_by)
        version2.publish(archived.created_by)
        version3 = version2.copy(version2.created_by)

        with self.login_user_context(self.superuser):
            response = self.client.get(
                self.get_view_url(
                    content_type_id=ContentType.objects.get_for_model(poll).pk,
                    object_id=poll.id,
                )
                + "?state=draft_and_published"
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("querysets", response.context)

        # queryset should contain page
        self.assertEqual(response.context["querysets"][0].count(), 2)
        self.assertNotIn(archived.content, response.context["querysets"][0])
        self.assertIn(version2.content, response.context["querysets"][0])
        self.assertIn(version3.content, response.context["querysets"][0])

    def test_extra_columns(self):
        extra_column = ExtraColumn(lambda o: "{} test".format(o), "Test column")

        with self.login_user_context(self.superuser), patch(
            "djangocms_references.views.get_extra_columns", return_value=[extra_column]
        ) as get_extra_columns:
            response = self.client.get(self.view_url)

        self.assertEqual(response.context["extra_columns"], [extra_column])
