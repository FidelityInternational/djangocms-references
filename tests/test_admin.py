from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy

from cms.test_utils.testcases import CMSTestCase

from djangocms_alias.admin import AliasContentAdmin
from djangocms_alias.models import Alias, AliasContent, Category
from djangocms_snippet.admin import SnippetAdmin as SnippetContentAdmin
from djangocms_snippet.models import Snippet as SnippetContent, SnippetGrouper
from djangocms_versioning.models import Version


class AliasAdminReferencesMonkeyPatchTestCase(CMSTestCase):
    def test_list_display(self):
        """
        The monkeypatch extends the alias admin, adding the show references link
        """
        request = self.get_request("/")
        request.user = self.get_superuser()
        category = Category.objects.create(name="Alias Reference Monkey Patch Category")
        alias = Alias.objects.create(category=category, position=0)
        alias_content = AliasContent.objects.create(
            alias=alias,
            name="Alias Reference Monkey Patch Content",
            language="en",
        )

        Version.objects.create(content=alias_content, created_by=request.user)
        content_type = ContentType.objects.get(app_label=alias._meta.app_label, model=alias._meta.model_name)
        alias_admin = AliasContentAdmin(AliasContent, admin.AdminSite())
        func = alias_admin.get_list_display(request)[-1]
        references_url = reverse_lazy(
            "djangocms_references:references-index",
            kwargs={"content_type_id": content_type.id, "object_id": alias.id}
        )

        list_display_icons = func(alias_content)

        self.assertIn(str(references_url), list_display_icons)
        self.assertIn("Show References", list_display_icons)


class SnippetAdminReferencesMonkeyPatchTestCase(CMSTestCase):
    def test_list_display(self):
        """
        The monkeypatch extends the snippet admin, adding the show references link
        """
        request = self.get_request("/")
        request.user = self.get_superuser()
        snippet = SnippetGrouper.objects.create()
        snippet_content = SnippetContent.objects.create(
            name="Snippet Reference Monkey Patch Content",
            snippet_grouper=snippet,
            slug="snippet_reference_link_monkeypatch_slug",
        )

        Version.objects.create(content=snippet_content, created_by=request.user)
        content_type = ContentType.objects.get(app_label=snippet._meta.app_label, model=snippet._meta.model_name)
        snippet_admin = SnippetContentAdmin(SnippetContent, admin.AdminSite())
        func = snippet_admin.get_list_display(request)[-1]
        references_url = reverse_lazy(
            "djangocms_references:references-index",
            kwargs={"content_type_id": content_type.id, "object_id": snippet.id}
        )

        list_display_icons = func(snippet_content)

        self.assertIn(str(references_url), list_display_icons)
        self.assertIn("Show References", list_display_icons)
