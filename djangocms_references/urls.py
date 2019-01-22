from django.conf.urls import url

from .views import ReferencesView


urlpatterns = [
    url(
        r"^(?P<content_type_id>\d+)/(?P<object_id>\d+)/$",
        ReferencesView.as_view(),
        name="references-index",
    )
]
