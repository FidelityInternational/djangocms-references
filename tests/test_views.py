from unittest.mock import patch

from django.conf.urls import include
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import reverse
from django.test import RequestFactory
from django.test.utils import override_settings
from django.urls import re_path

from cms.api import add_plugin
from cms.test_utils.testcases import CMSTestCase

from djangocms_versioning.constants import (
    ARCHIVED,
    DRAFT,
    PUBLISHED,
    UNPUBLISHED,
)

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
    re_path(r"^references/", include(djangocms_references.urls)),
    re_path(r"^admin/", admin.site.urls),
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

    def test_view_endpoint_access_staff_user_without_permission(self):
        staff_user = self.get_staff_user_with_no_permissions()
        with self.login_user_context(staff_user):
            response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 403)

    def test_view_endpoint_access_staff_user_with_permission(self):
        staff_user = self.get_staff_user_with_no_permissions()
        staff_user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="djangocms_references",
                codename="show_references",
            )
        )
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

    def test_extra_columns(self):
        extra_column = ExtraColumn(lambda o: "{} test".format(o), "Test column")

        with self.login_user_context(self.superuser), patch(
            "djangocms_references.views.get_extra_columns", return_value=[extra_column]
        ):
            response = self.client.get(self.view_url)

        self.assertEqual(response.context["extra_columns"], [extra_column])

    def test_view_draft_filter_applied(self):
        version1 = PageVersionFactory(
            content__title="test1", content__language=self.language
        )
        version2 = PageVersionFactory(
            content__title="test2", content__language=self.language, state=PUBLISHED
        )

        page_content1 = version1.content
        page_content2 = version2.content

        placeholder1 = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_content1),
            object_id=page_content1.id,
        )

        placeholder2 = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_content2),
            object_id=page_content2.id,
        )

        poll = PollFactory()
        # add poll plugin to page
        add_plugin(placeholder1, "PollPlugin", "en", poll=poll, template=0)
        add_plugin(placeholder2, "PollPlugin", "en", poll=poll, template=0)

        # When draft is selected only the draft entries should be shown
        version_selection = f"?state={DRAFT}"
        admin_endpoint = self.get_view_url(
            content_type_id=ContentType.objects.get_for_model(poll).pk,
            object_id=poll.id,
        )

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + version_selection)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["querysets"][0].count(), 1)
        self.assertIn(page_content1, response.context["querysets"][0])
        self.assertNotIn(page_content2, response.context["querysets"][0])

    def test_view_published_filter_applied(self):
        version1 = PageVersionFactory(
            content__title="test1", content__language=self.language,
        )
        version2 = PageVersionFactory(
            content__title="test2", content__language=self.language, state=PUBLISHED
        )

        page_content1 = version1.content
        page_content2 = version2.content

        placeholder1 = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_content2),
            object_id=page_content2.id,
        )

        placeholder2 = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_content2),
            object_id=page_content2.id,
        )

        poll = PollFactory()
        # add poll plugin to page
        add_plugin(placeholder1, "PollPlugin", "en", poll=poll, template=0)
        add_plugin(placeholder2, "PollPlugin", "en", poll=poll, template=0)

        # When published is selected only the published entries should be shown
        version_selection = f"?state={PUBLISHED}"
        admin_endpoint = self.get_view_url(
            content_type_id=ContentType.objects.get_for_model(poll).pk,
            object_id=poll.id,
        )

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + version_selection)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["querysets"][0].count(), 1)
        self.assertNotIn(page_content1, response.context["querysets"][0])
        self.assertIn(page_content2, response.context["querysets"][0])

    def test_view_archived_filter_applied(self):
        version1 = PageVersionFactory(
            content__title="test1", content__language=self.language,
        )
        version2 = PageVersionFactory(
            content__title="test2", content__language=self.language, state=ARCHIVED
        )

        page_content1 = version1.content
        page_content2 = version2.content

        placeholder1 = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_content2),
            object_id=page_content2.id,
        )

        placeholder2 = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_content2),
            object_id=page_content2.id,
        )

        poll = PollFactory()
        # add poll plugin to page
        add_plugin(placeholder1, "PollPlugin", "en", poll=poll, template=0)
        add_plugin(placeholder2, "PollPlugin", "en", poll=poll, template=0)

        # When archived is selected only the archived entries should be shown
        version_selection = f"?state={ARCHIVED}"
        admin_endpoint = self.get_view_url(
            content_type_id=ContentType.objects.get_for_model(poll).pk,
            object_id=poll.id,
        )

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + version_selection)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["querysets"][0].count(), 1)
        self.assertNotIn(page_content1, response.context["querysets"][0])
        self.assertIn(page_content2, response.context["querysets"][0])

    def test_view_unpublised_filter_applied(self):
        version1 = PageVersionFactory(
            content__title="test1", content__language=self.language,
        )
        version2 = PageVersionFactory(
            content__title="test2", content__language=self.language, state=UNPUBLISHED
        )

        page_content1 = version1.content
        page_content2 = version2.content

        placeholder1 = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_content2),
            object_id=page_content2.id,
        )

        placeholder2 = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_content2),
            object_id=page_content2.id,
        )

        poll = PollFactory()
        # add poll plugin to page
        add_plugin(placeholder1, "PollPlugin", "en", poll=poll, template=0)
        add_plugin(placeholder2, "PollPlugin", "en", poll=poll, template=0)

        # When unpublished is selected only the unpublished entries should be shown
        version_selection = f"?state={UNPUBLISHED}"
        admin_endpoint = self.get_view_url(
            content_type_id=ContentType.objects.get_for_model(poll).pk,
            object_id=poll.id,
        )

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + version_selection)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["querysets"][0].count(), 1)
        self.assertNotIn(page_content1, response.context["querysets"][0])
        self.assertIn(page_content2, response.context["querysets"][0])

    def test_view_no_filter_applied(self):
        version1 = PageVersionFactory(
            content__title="test1", content__language=self.language, state=PUBLISHED
        )
        version2 = PageVersionFactory(
            content__title="test2", content__language=self.language, state=DRAFT
        )
        version3 = PageVersionFactory(
            content__title="test3", content__language=self.language, state=ARCHIVED
        )
        version4 = PageVersionFactory(
            content__title="test3", content__language=self.language, state=UNPUBLISHED
        )

        page_content1 = version1.content
        page_content2 = version2.content
        page_content3 = version3.content
        page_content4 = version4.content

        placeholder1 = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_content1),
            object_id=page_content1.id,
        )

        placeholder2 = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_content2),
            object_id=page_content2.id,
        )

        placeholder3 = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_content3),
            object_id=page_content3.id,
        )

        placeholder4 = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_content4),
            object_id=page_content4.id,
        )

        poll = PollFactory()
        # add poll plugin to page
        add_plugin(placeholder1, "PollPlugin", "en", poll=poll, template=0)
        add_plugin(placeholder2, "PollPlugin", "en", poll=poll, template=0)
        add_plugin(placeholder3, "PollPlugin", "en", poll=poll, template=0)
        add_plugin(placeholder4, "PollPlugin", "en", poll=poll, template=0)

        # When all filter is selected, all entries should be shown
        version_selection = "?state=all"
        admin_endpoint = self.get_view_url(
            content_type_id=ContentType.objects.get_for_model(poll).pk,
            object_id=poll.id,
        )

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(admin_endpoint + version_selection)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["querysets"][0].count(), 4)
        self.assertIn(page_content1, response.context["querysets"][0])
        self.assertIn(page_content2, response.context["querysets"][0])
        self.assertIn(page_content3, response.context["querysets"][0])
        self.assertIn(page_content4, response.context["querysets"][0])
