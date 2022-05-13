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


def get_view_url(content_type_id, object_id):
    return reverse(
        "djangocms_references:references-index",
        kwargs={"content_type_id": content_type_id, "object_id": object_id},
    )


@override_settings(ROOT_URLCONF=__name__)
class ReferencesViewTestCases(CMSTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.superuser = self.get_superuser()
        self.page = PageContentFactory()
        self.content = ContentType.objects.get_for_model(self.page)
        self.view_url = get_view_url(self.content.pk, self.page.id)
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
                get_view_url(content_type_id=0, object_id=1)
            )
        self.assertEqual(response.status_code, 404)

    def test_view_invalid_object(self):
        with self.login_user_context(self.superuser):
            response = self.client.get(
                get_view_url(content_type_id=self.content.id, object_id=0)
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
                get_view_url(
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
                get_view_url(
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


@override_settings(ROOT_URLCONF=__name__)
class ReferencesViewVersionFilterTestCases(CMSTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.superuser = self.get_superuser()
        self.poll = PollFactory()
        self.admin_endpoint = get_view_url(
            content_type_id=ContentType.objects.get_for_model(self.poll).pk,
            object_id=self.poll.id,
        )

    def _create_data_set_for_latest_versions(self, version_state_1, version_state_2, filter_applied=None):
        language_1 = "en"
        language_2 = "de"

        # Page 1 has 4 versions
        # Latest version uses the supplied version_state_1 for en and de languages, previous
        # versions use the supplied version_state_2
        page_1_version_1 = PageVersionFactory(
            content__language=language_1, state=version_state_1
        )
        page_1_grouper = page_1_version_1.content.page
        page_1_version_1_placeholder = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_1_version_1.content),
            object_id=page_1_version_1.content.id,
        )
        add_plugin(page_1_version_1_placeholder, "PollPlugin", language_1, poll=self.poll)
        page_1_version_2 = PageVersionFactory(
            content__page=page_1_grouper,
            content__language=language_1, state=version_state_2
        )
        page_1_version_2_placeholder = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_1_version_2.content),
            object_id=page_1_version_2.content.id,
        )
        add_plugin(page_1_version_2_placeholder, "PollPlugin", language_1, poll=self.poll)

        page_1_version_3 = PageVersionFactory(
            content__page=page_1_grouper,
            content__language=language_2, state=version_state_1
        )
        page_1_version_3_placeholder = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_1_version_3.content),
            object_id=page_1_version_3.content.id,
        )
        add_plugin(page_1_version_3_placeholder, "PollPlugin", language_2, poll=self.poll)
        page_1_version_4 = PageVersionFactory(
            content__page=page_1_grouper,
            content__language=language_2, state=version_state_2
        )
        page_1_version_4_placeholder = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_1_version_4.content),
            object_id=page_1_version_4.content.id,
        )
        add_plugin(page_1_version_4_placeholder, "PollPlugin", language_2, poll=self.poll)

        # Page 2 has 4 versions
        # Latest version uses the supplied version_state_2 for en and de languages, previous
        # versions use the supplied version_state_1. This is the opposite arrangement to the
        # versions created above.
        # by using the opposite state filter neither should be found because the "latest"
        # versions are not the same as the filter set.
        page_2_version_1 = PageVersionFactory(
            content__language=language_1, state=version_state_2
        )
        page_2_grouper = page_2_version_1.content.page
        page_2_version_1_placeholder = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_2_version_1.content),
            object_id=page_2_version_1.content.id,
        )
        add_plugin(page_2_version_1_placeholder, "PollPlugin", language_1, poll=self.poll)
        page_2_version_2 = PageVersionFactory(
            content__page=page_2_grouper,
            content__language=language_1, state=version_state_1
        )
        page_2_version_2_placeholder = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_2_version_2.content),
            object_id=page_2_version_2.content.id,
        )
        add_plugin(page_2_version_2_placeholder, "PollPlugin", language_1, poll=self.poll)

        page_2_version_3 = PageVersionFactory(
            content__page=page_2_grouper,
            content__language=language_2, state=version_state_2
        )
        page_2_version_3_placeholder = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_2_version_3.content),
            object_id=page_2_version_3.content.id,
        )
        add_plugin(page_2_version_3_placeholder, "PollPlugin", language_2, poll=self.poll)
        page_2_version_4 = PageVersionFactory(
            content__page=page_2_grouper,
            content__language=language_2, state=version_state_1
        )
        page_2_version_4_placeholder = PlaceholderFactory(
            content_type=ContentType.objects.get_for_model(page_2_version_4.content),
            object_id=page_2_version_4.content.id,
        )
        add_plugin(page_2_version_4_placeholder, "PollPlugin", language_2, poll=self.poll)

        # When a filter is applied only the latest versions for a grouper should be shown
        if filter_applied:
            # The latest versions of each grouper / grouping values version set
            return [
                page_1_version_2.content.pk,
                page_1_version_4.content.pk,
            ]
        # Otherwise all a groupers latest versions should be shown
        return [
            page_1_version_2.content.pk,
            page_1_version_4.content.pk,
            page_2_version_2.content.pk,
            page_2_version_4.content.pk,
        ]

    def test_view_draft_filter_applied(self):
        """
        When draft is selected only the draft entries should be shown
        """
        filter_applied = DRAFT
        latest_versions = self._create_data_set_for_latest_versions(
            version_state_1=PUBLISHED,
            version_state_2=DRAFT,
            filter_applied=filter_applied,
        )

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.admin_endpoint + f"?state={filter_applied}")

        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["querysets"][0],
            latest_versions,
            transform=lambda x: x.pk,
            ordered=False,
        )

    def test_view_published_filter_applied(self):
        """
        When published is selected only the published entries should be shown
        """
        filter_applied = PUBLISHED
        latest_versions = self._create_data_set_for_latest_versions(
            version_state_1=DRAFT,
            version_state_2=PUBLISHED,
            filter_applied=filter_applied,
        )

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.admin_endpoint + f"?state={filter_applied}")

        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["querysets"][0],
            latest_versions,
            transform=lambda x: x.pk,
            ordered=False,
        )

    def test_view_archived_filter_applied(self):
        """
        When archived is selected only the archived entries should be shown
        """
        filter_applied = ARCHIVED
        latest_versions = self._create_data_set_for_latest_versions(
            version_state_1=DRAFT,
            version_state_2=ARCHIVED,
            filter_applied=filter_applied,
        )

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.admin_endpoint + f"?state={filter_applied}")

        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["querysets"][0],
            latest_versions,
            transform=lambda x: x.pk,
            ordered=False,
        )

    def test_view_unpublised_filter_applied(self):
        """
        When unpublished is selected only the unpublished entries should be shown
        """
        filter_applied = UNPUBLISHED
        latest_versions = self._create_data_set_for_latest_versions(
            version_state_1=DRAFT,
            version_state_2=UNPUBLISHED,
            filter_applied=filter_applied,
        )

        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.admin_endpoint + f"?state={filter_applied}")

        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["querysets"][0],
            latest_versions,
            transform=lambda x: x.pk,
            ordered=False,
        )

    def test_view_no_filter_applied(self):
        """
        When all filter is selected, all entries should be shown
        """
        draft_latest_versions = self._create_data_set_for_latest_versions(
            version_state_1=PUBLISHED,
            version_state_2=DRAFT,
        )
        published_latest_versions = self._create_data_set_for_latest_versions(
            version_state_1=DRAFT,
            version_state_2=PUBLISHED,
        )
        archived_latest_versions = self._create_data_set_for_latest_versions(
            version_state_1=DRAFT,
            version_state_2=ARCHIVED,
        )
        unpublished_latest_versions = self._create_data_set_for_latest_versions(
            version_state_1=DRAFT,
            version_state_2=UNPUBLISHED,
        )

        # Try with all state set
        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.admin_endpoint + "?state=all")

        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["querysets"][0],
            draft_latest_versions + published_latest_versions +
            archived_latest_versions + unpublished_latest_versions,
            transform=lambda x: x.pk,
            ordered=False,
        )

        # Try again with no state set
        with self.login_user_context(self.get_superuser()):
            response = self.client.get(self.admin_endpoint)

        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context["querysets"][0],
            draft_latest_versions + published_latest_versions +
            archived_latest_versions + unpublished_latest_versions,
            transform=lambda x: x.pk,
            ordered=False,
        )
