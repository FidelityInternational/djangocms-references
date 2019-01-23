from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required

from .views import ReferencesView


app_name = "djangocms_references"
urlpatterns = [
    url(
        r"^(?P<content_type_id>\d+)/(?P<object_id>\d+)/$",
        staff_member_required(ReferencesView.as_view()),
        name="references-index",
    )
]
