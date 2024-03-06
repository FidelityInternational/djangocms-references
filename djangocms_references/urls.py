from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from .views import ReferencesView


app_name = "djangocms_references"
urlpatterns = [
    path(
        "references/<int:content_type_id>/<int:object_id>/",
        staff_member_required(ReferencesView.as_view()),
        name="references-index",
    )
]
