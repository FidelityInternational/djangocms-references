from django.contrib.admin.views.decorators import staff_member_required
from django.urls import re_path

from .views import ReferencesView


app_name = "djangocms_references"
urlpatterns = [
    re_path(
        r"^references/(?P<content_type_id>\d+)/(?P<object_id>\d+)/$",
        staff_member_required(ReferencesView.as_view()),
        name="references-index",
    )
]
