from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from django.urls import include, re_path
from django.views.static import serve


admin.autodiscover()

urlpatterns = [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT, "show_indexes": True}),  # NOQA
    path("", include('djangocms_references.urls')),
]
i18n_urls = [
    re_path(r"^admin/", admin.site.urls),
    path("", include("cms.urls")),
]

urlpatterns += i18n_patterns(*i18n_urls)
urlpatterns += staticfiles_urlpatterns()
