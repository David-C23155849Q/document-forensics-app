from django.urls import path

from .views import SubmissionSnapshotListView, SnapshotDetailView

urlpatterns = [
    path("submissions/<int:submission_id>/snapshots/", SubmissionSnapshotListView.as_view(), name="submission-snapshots"),
    path("submissions/<int:submission_id>/snapshots/<int:snapshot_id>/", SnapshotDetailView.as_view(), name="snapshot-detail"),
]
