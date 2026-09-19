from django.urls import path

from .views import SubmissionEventListView

urlpatterns = [
    path("submissions/<int:submission_id>/events/", SubmissionEventListView.as_view(), name="submission-events"),
]
