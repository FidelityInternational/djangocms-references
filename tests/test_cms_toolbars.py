from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.test.client import RequestFactory
from django.test.utils import override_settings

from cms.middleware.toolbar import ToolbarMiddleware
from cms.test_utils.testcases import CMSTestCase
from cms.toolbar.items import SideframeButton
from cms.toolbar.toolbar import CMSToolbar

from djangocms_references.cms_toolbars import ReferencesToolbar
from djangocms_references.test_utils.factories import (
    PageContentFactory,
    UserFactory,
)


urlpatterns = [
    url(r"^references/", include("djangocms_references.urls")),
    url(r"^admin/", admin.site.urls),
]


@override_settings(ROOT_URLCONF=__name__)
class TestReferencesCMSToolbars(CMSTestCase):
    def _get_page_request(self, page, user):
        request = RequestFactory().get("/")
        request.session = {}
        request.user = user
        request.current_page = page
        mid = ToolbarMiddleware()
        mid.process_request(request)
        if hasattr(request, "toolbar"):
            request.toolbar.populate()
        return request

    def _get_toolbar(self, content_obj, user=None, **kwargs):
        """Helper method to set up the toolbar
        """
        if not user:
            user = UserFactory(is_staff=True)
        request = self._get_page_request(
            page=content_obj.page if content_obj else None, user=user
        )
        cms_toolbar = CMSToolbar(request)
        toolbar = ReferencesToolbar(
            cms_toolbar.request, toolbar=cms_toolbar, is_current_app=True, app_path="/"
        )
        toolbar.toolbar.set_object(content_obj)

        return toolbar

    def test_cms_toolbar_has_show_references(self):
        user = self.get_standard_user()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="djangocms_references",
                codename="show_references",
            )
        )
        page_content = PageContentFactory(created_by=user)
        toolbar = self._get_toolbar(page_content, user=user, edit_mode=True)
        toolbar.populate()
        toolbar.post_template_populate()
        self.assertIsInstance(
            toolbar.toolbar.left_items[-1].buttons[0], SideframeButton
        )
        self.assertEqual(
            toolbar.toolbar.left_items[-1].buttons[0].name, "Show References"
        )

    def test_cms_toolbar_button_not_shown_if_no_permission(self):
        user = self.get_standard_user()
        page_content = PageContentFactory(created_by=user)
        toolbar = self._get_toolbar(page_content, user=user, edit_mode=True)
        toolbar.populate()
        toolbar.post_template_populate()
        self.assertFalse(toolbar.toolbar.left_items)
